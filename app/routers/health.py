from fastapi import APIRouter, Depends
from app.dependencies import get_bittensor_service
from app.services.bittensor_service import BittensorService

router = APIRouter(tags=["health"], prefix="/health")

@router.get("")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/bittensor")
async def bittensor_health(service: BittensorService = Depends(get_bittensor_service)):
    """Check BitTensor service health."""
    print("Checking BitTensor service health...")
    try:
        wallet_info = service.get_wallet_info()
        return {
            "status": "healthy",
            "network": service.network,
            "wallet": wallet_info,
        }
    except Exception as e:
        print(f"Error occurred while checking BitTensor service health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }