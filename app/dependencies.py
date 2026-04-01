# dependencies.py
from app.services.bittensor_service import BittensorService
from app.config import settings

# Singleton service instance
_bittensor_service: BittensorService = None


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


def get_bittensor_service() -> BittensorService:
    global _bittensor_service
    print("Initializing BitTensorService...")

    wallet_path = settings.WALLET_PATH
    if wallet_path:
        wallet_path = _normalize_wallet_path(wallet_path, settings.WALLET_NAME, settings.WALLET_HOTKEY)

    if _bittensor_service is None:
        print(f"Using network: {settings.SUBTENSOR_NETWORK}")
        _bittensor_service = BittensorService(
            network=settings.SUBTENSOR_NETWORK,
            wallet_name=settings.WALLET_NAME,
            hotkey_name=settings.WALLET_HOTKEY,
            wallet_path=wallet_path,
        )
    print("BitTensorService initialized.")

    return _bittensor_service