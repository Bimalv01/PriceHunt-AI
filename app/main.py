from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import get_settings
from app.api import api_router

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PriceHunt AI",
        description="AI agent that compares Amazon India vs Flipkart prices using Groq.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    # Serve the frontend HTML
    @app.get("/", response_class=FileResponse)
    async def serve_frontend():
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        return FileResponse(template_path)

    return app


app = create_app()