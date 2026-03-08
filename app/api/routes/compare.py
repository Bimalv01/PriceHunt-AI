from fastapi import APIRouter, HTTPException, status
from groq import AuthenticationError

from app.core.config import get_settings
from app.models.schemas import CompareRequest, CompareResponse, ErrorResponse
from app.services.agent import run_price_agent

router = APIRouter(prefix="/compare", tags=["Price Comparison"])
settings = get_settings()


@router.post(
    "/",
    response_model=CompareResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Compare product prices on Amazon India vs Croma",
)
async def compare_prices(body: CompareRequest) -> CompareResponse:
    # Use key from request body only if provided, else fall back to .env
    api_key = body.groq_api_key or settings.groq_api_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Groq API key configured. Please set GROQ_API_KEY in your .env file.",
        )
    try:
        return await run_price_agent(product=body.product, api_key=api_key)
    except AuthenticationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Groq API key.")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {exc}")