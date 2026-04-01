# subnet.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from app.dependencies import get_bittensor_service
from app.services.bittensor_service import BittensorService
from app.config import settings

router = APIRouter(tags=["subnets"], prefix="/subnet")

@router.get("/{netuid}")
async def get_subnet_info(
    netuid: int,
    service: BittensorService = Depends(get_bittensor_service)
):
    """Get basic information about a subnet."""
    try:
        info = await service.get_subnet_info(netuid)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{netuid}/neurons")
async def list_neurons(
    netuid: int,
    uids: Optional[List[int]] = Query(None),
    service: BittensorService = Depends(get_bittensor_service)
):
    """List neurons on a subnet."""
    try:
        neurons = await service.query_neurons(netuid, uids)
        return {"netuid": netuid, "neurons": neurons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{netuid}/registration-status")
async def registration_status(
    netuid: int,
    service: BittensorService = Depends(get_bittensor_service)
):
    """Check if current wallet is registered on the subnet."""
    try:
        is_registered = service.check_registration(netuid)
        return {
            "netuid": netuid,
            "is_registered": is_registered,
            "wallet": service.get_wallet_info()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))