from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Loli Video Generator",
        description="Generate educational videos using Manim",
        version="1.0.0"
    )

    # Add CORS middleware for React frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development/demo
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include routers
    app.include_router(router, prefix="/api/v1")

    # Health check endpoint at root
    @app.get("/")
    async def root():
        return {"message": "Manim Video Generator API", "version": "1.0.0", "status": "running"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os

    # Create directories
    os.makedirs(settings.VIDEOS_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)