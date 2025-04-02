import os
import uvicorn
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.add("logs/app.log", rotation="10 MB", level=LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="Assistant Juridique IA pour le Droit Français",
    description="API d'assistance juridique IA spécialisée dans le droit français",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include API routers
from app.api.router import api_router
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service running"}

# Initialize application on startup
from app.utils.init import initialize_app

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting application initialization")
    await initialize_app()

# Mount static files for front-end (when available)
# app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8009))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Assistant Juridique IA on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True) 