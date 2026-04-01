# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LayerTao FastAPI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # BitTensor Network
    SUBTENSOR_NETWORK: str = "finney"  # finney (mainnet), test, local
    NETUID: int = 1                    # Default subnet 1, override per subnet

    # Wallet Configuration
    WALLET_NAME: str = "w1"
    WALLET_HOTKEY: str = "default"
    WALLET_PATH: Optional[str] = None  # Defaults to ~/.bittensor/wallets

    # Server
    HOST: str = "localhost"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()