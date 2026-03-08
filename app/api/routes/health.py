from fastapi import APIRouter
from app.core.config import get_settings
from app.services.scraper import search_croma, search_amazon

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", summary="Health check")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "model": settings.groq_model,
        "groq_key_configured": bool(settings.groq_api_key),
    }


@router.get("/debug/amazon")
async def debug_amazon(q: str = "iPhone 16 Pro"):
    result = await search_amazon(q)
    return {
        "source": result.get("source"),
        "chars": len(result.get("content", "")),
        "content_preview": result.get("content", "")[:500],
    }


@router.get("/debug/croma")
async def debug_croma(q: str = "iPhone 16 Pro"):
    result = await search_croma(q)
    return {
        "source": result.get("source"),
        "chars": len(result.get("content", "")),
        "content_preview": result.get("content", "")[:500],
    }