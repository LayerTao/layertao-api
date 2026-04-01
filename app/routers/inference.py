#  inference.py - API router for handling AI inference requests to the Bittensor network.
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.dependencies import get_bittensor_service
from app.services.bittensor_service import BittensorService

router = APIRouter(tags=["inference"], prefix="/inference")

# Define the expected request body


class AIQuery(BaseModel):
    prompt: str
    netuid: int = 1  # Default to Subnet 1 (Apex)
    timeout: int = 12  # Timeout in seconds for the query


class AIResponse(BaseModel):
    prompt: str
    response: Optional[str]
    success: bool
    error: Optional[str] = None


@router.post("/generate", response_model=AIResponse)
async def generate_text(query: AIQuery, service: BittensorService = Depends(get_bittensor_service)):
    """
    Send a text prompt to the Bittensor network for AI inference.
    By default, it queries Subnet 1 (Apex/Text Prompting), which is the flagship
    subnet for general-purpose conversational AI.
    """
    try:
        # Delegate the actual network call to our service
        result = await service.query_subnet_for_text_generation(
            netuid=query.netuid,
            prompt=query.prompt,
            timeout=query.timeout
        )
        return AIResponse(
            prompt=query.prompt,
            response=result,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
