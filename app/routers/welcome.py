from fastapi import APIRouter, Depends
from datetime import datetime
import sys

router = APIRouter(tags=["welcome"])

@router.get("/")
async def welcome():
    """Welcome endpoint with system information."""
    return {
        "message": "Welcome to BitTensor FastAPI Web App",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "docs": "/docs",
        "redoc": "/redoc"
    }