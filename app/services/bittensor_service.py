# app/services/bittensor_service.py
import asyncio
import logging
import socket
import random
import numpy as np
from typing import Optional, List, Dict, Any

import bittensor as bt

logger = logging.getLogger(__name__)


class TextPromptingSynapse(bt.Synapse):
    """
    Synapse for text prompting subnets (e.g., subnet 1).
    Expects a list of messages (each with 'role' and 'content') and returns a completion.
    """
    messages: List[Dict[str, str]] = []
    # completion: Optional[str] = None
    # timeout: float = 12.0
    # error_message: Optional[str] = None
    # is_success: Optional[bool] = None


class BittensorService:
    """
    Service for interacting with Bittensor subnets.
    Supports querying subnet information, neuron details, and text generation.
    """

    def __init__(
        self,
        network: str,
        wallet_name: str,
        hotkey_name: str,
        wallet_path: Optional[str] = None,
    ):
        """
        Initialize the Bittensor service.

        :param network: Subtensor network (e.g., "finney", "test").
        :param wallet_name: Name of the wallet (directory under wallet_path).
        :param hotkey_name: Hotkey name inside the wallet.
        :param wallet_path: Path to the wallet root directory (defaults to ~/.bittensor/wallets).
        """
        self.network = network

        # Prepare wallet kwargs
        wallet_kwargs = {
            "name": wallet_name,
            "hotkey": hotkey_name,
        }
        if wallet_path:
            wallet_kwargs["path"] = self._normalize_wallet_path(wallet_path, wallet_name, hotkey_name)

        # Create wallet (will be loaded if exists, else created with empty keys)
        self.wallet = bt.Wallet(**wallet_kwargs)
        try:
            # Ensure the wallet exists; if not, create it (without password for simplicity)
            self.wallet.create_if_non_existent(
                coldkey_use_password=False,
                hotkey_use_password=False,
                suppress=True,
            )
        except Exception as e:
            logger.warning(f"Wallet creation/loading failed: {e}")

        # Connect to the subtensor
        self.subtensor = bt.Subtensor(network=network)

        # Dendrite for network queries
        self.dendrite = bt.Dendrite(wallet=self.wallet)

        # Metagraph cache (will be set per subnet)
        self.metagraph: Optional[bt.Metagraph] = None
        self.netuid: Optional[int] = None

    @staticmethod
    def _normalize_wallet_path(wallet_path: str, wallet_name: str, hotkey_name: str) -> str:
        from pathlib import Path

        p = Path(wallet_path).expanduser()
        if p.name == hotkey_name:
            p = p.parent
        if p.name == "hotkeys":
            p = p.parent
        if p.name == wallet_name:
            p = p.parent
        return str(p)

    def _sync_metagraph(self, netuid: int, lite: bool = False) -> bt.Metagraph:
        """
        Synchronize the metagraph for a given subnet.
        Use lite=False to get axon endpoints (required for querying).
        """
        self.metagraph = bt.Metagraph(netuid, network=self.network, sync=True, lite=lite)
        self.metagraph.sync()
        self.netuid = netuid
        return self.metagraph

    async def get_subnet_info(self, netuid: int) -> Dict[str, Any]:
        """
        Retrieve basic information about a subnet.
        """
        try:
            # Get metagraph with axon info (lite=False) for stake totals
            metagraph = await asyncio.to_thread(self._sync_metagraph, netuid, lite=False)

            # Fetch subnet details (tempo, founder, etc.)
            subnet_info = self.subtensor.subnet(netuid)

            # Count validators (those with validator_permit == True)
            validator_count = int(metagraph.validator_permit.sum()) if hasattr(metagraph, "validator_permit") else 0

            return {
                "netuid": netuid,
                "network": self.network,
                "tempo": subnet_info.tempo if subnet_info else None,
                "total_stake": float(metagraph.S.sum()) if hasattr(metagraph, "S") else None,
                "neuron_count": len(metagraph.hotkeys) if metagraph else 0,
                "active_validators": validator_count,
            }
        except Exception as e:
            logger.error(f"Error fetching subnet info: {e}")
            raise

    async def query_neurons(self, netuid: int, uids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Get details for specified neurons (or all) on a subnet.
        """
        metagraph = await asyncio.to_thread(self._sync_metagraph, netuid, lite=False)

        if uids is None:
            uids = range(len(metagraph.hotkeys))

        neurons = []
        for uid in uids:
            # Check if uid is within bounds
            if uid >= len(metagraph.hotkeys):
                continue

            neurons.append({
                "uid": uid,
                "hotkey": metagraph.hotkeys[uid],
                "coldkey": metagraph.coldkeys[uid],
                "stake": float(metagraph.S[uid]) if hasattr(metagraph, "S") else 0,
                "is_validator": bool(metagraph.validator_permit[uid]) if hasattr(metagraph, "validator_permit") else False,
                "axon": str(metagraph.axons[uid]) if uid < len(metagraph.axons) else None,
            })
        return neurons

    def get_wallet_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded wallet.
        """
        return {
            "name": self.wallet.name,
            "hotkey": self.wallet.hotkey_str,
            "coldkey_address": self.wallet.coldkeypub.ss58_address if self.wallet.coldkeypub else None,
            "hotkey_address": self.wallet.hotkey.ss58_address if self.wallet.hotkey else None,
        }

    def check_registration(self, netuid: int) -> bool:
        """
        Check if the wallet's hotkey is registered on the subnet.
        """
        try:
            self._sync_metagraph(netuid, lite=True)
            return self.wallet.hotkey.ss58_address in self.metagraph.hotkeys
        except Exception as e:
            logger.error(f"Registration check failed: {e}")
            return False

    @staticmethod
    def _is_axon_reachable(axon: bt.AxonInfo, timeout: float = 0.5) -> bool:
        """
        Check if an axon endpoint is reachable via TCP.
        """
        ip = getattr(axon, "ip", None)
        port = getattr(axon, "port", None)
        if not ip or ip in ("0.0.0.0", "::") or not port or port <= 0:
            return False

        # Clean IP (strip slashes if any)
        if isinstance(ip, str) and ip.startswith("/"):
            parts = ip.strip("/").split("/")
            if len(parts) >= 2 and parts[0] in ("ipv4", "ipv6"):
                ip = parts[1]

        try:
            with socket.create_connection((ip, port), timeout=timeout):
                return True
        except Exception:
            return False

    async def _get_reachable_axons(self, netuid: int, max_axons: int = 10, timeout: float = 0.5) -> List[bt.AxonInfo]:
        """
        Retrieve a list of reachable axons from the subnet.
        """
        # Get metagraph with axon details (lite=False)
        metagraph = await asyncio.to_thread(self._sync_metagraph, netuid, lite=False)

        # Collect all axons that have valid IP/port
        axons = [axon for axon in metagraph.axons if axon.ip and axon.ip not in ("0.0.0.0", "::") and axon.port > 0]

        return axons[:max_axons]  # Return the first few (could implement reachability check if needed)
    
        # Shuffle to avoid bias (optional)
        # random.shuffle(axons)

        # Keep only reachable ones
        # reachable = []
        # for axon in axons[:max_axons * 2]:  # Check a few extra to have enough
        #     if await asyncio.to_thread(self._is_axon_reachable, axon, timeout):
        #         reachable.append(axon)
        #         if len(reachable) >= max_axons:
        #             break

        # return reachable

    async def query_subnet_for_text_generation(self, netuid: int, prompt: str, timeout: int = 12) -> str:
        """
        Send a text prompt to the Bittensor network (subnet 1 or any text-prompting subnet)
        and return the generated response.

        :param netuid: Subnet ID (usually 1 for text prompting).
        :param prompt: User prompt.
        :param timeout: Overall timeout for the query (seconds).
        :return: Generated text.
        :raises RuntimeError: If no response is received or the query fails.
        """
        try:
            if not self.subtensor.is_hotkey_registered(self.wallet.hotkey.ss58_address, netuid):
                print(f"Hotkey not registered on subnet {netuid}. Registering...")
                res = bt.extrinsics.registration.register_extrinsic(
                            self.subtensor, self.wallet, netuid, output_in_place=False)
                print("Registration tx:", res)  # ExtrinsicResponse object
            else:
                print(f"Hotkey {self.wallet.hotkey.ss58_address} already registered on subnet {netuid}.")

            # sync metagraph to get axon info
            self._sync_metagraph(netuid=netuid, lite=False)
            # if len(self.metagraph.mechanism_count) == 0:
            #     print("No miners found on subnet.")
            #     return
            # Get reachable axons (max 50)
            axons = await self._get_reachable_axons(netuid, max_axons=50, timeout=5)
            # if not axons:
            #     raise RuntimeError("No reachable axons found on this subnet.")

            
            
            # Send the query (forward returns a list of responses)
            # responses = await self.dendrite.forward(
            #     axons=axons,
            #     synapse=synapse,
            #     timeout=timeout,
            #     deserialize=True,
            # )

            # Choose a miner (axon) to query, e.g. the top-ranked one.
            # sorted_indices = np.argsort(self.metagraph.incentive)
            # top_uid = sorted_indices[-1]  # last index = highest incentive
            # axon_info = self.metagraph.endpoints[top_uid]   # contains (IP, port)
            # print(f"Querying Axon at {axon_info.ip}:{axon_info.port}")

            #    (Use a specialized Synapse class if required by the subnet, here generic example:)
            # syn = bt.Synapse()
            # # Create the correct synapse for text prompting
            syn = TextPromptingSynapse(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            syn.name = "TextGeneration"       # Route name expected by the Axon
            syn.timeout = timeout
            # syn.deserialize = True

            responses = await self.dendrite.forward(
                axons=axons,
                synapse=syn,
                timeout=timeout,
            )  # Returns list of Synapse responses【58†L203-L210】

            for resp in responses:
                if resp.is_success:
                    print("Model response:", resp.outputs)  # or the appropriate field for output
                    return resp.outputs  # Return the generated text
                else:
                    print(f"Request failed: {resp.is_failure}, timed out: {resp.is_timeout}, error: {resp.error_message}")

            # Handle single response or list
            # if not isinstance(responses, list):
            #     responses = [responses]

            # # Extract the first non-empty completion
            # for resp in responses:
            #     # return resp.completion.strip()
            #     if resp and hasattr(resp, "completion") and resp.completion:
            #         return resp.completion.strip()

            # No usable response
            raise RuntimeError("No valid completion received from any axon.")

        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise