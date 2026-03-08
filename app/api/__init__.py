from fastapi import APIRouter
from app.api.routes import compare, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(compare.router, prefix="/api/v1")