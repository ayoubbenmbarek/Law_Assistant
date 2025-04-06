import os
import logging
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from loguru import logger
import time

from app.api.endpoints import query, auth, users, sources, pdf
from app.utils.vector_store import vector_store
from app.api.routes import api_router
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.core.config import settings

# Charger les variables d'environnement
load_dotenv()

# Configurer la journalisation
logger.add("logs/app.log", rotation="500 MB", level="INFO", format="{time} {level} {message}")

# Créer les tables dans la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Assistant Juridique IA",
    description="API pour l'assistant juridique basé sur l'IA",
    version="1.0.0",
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour le logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# Monter les routes API
app.include_router(api_router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(pdf.router, prefix="/api", tags=["pdf"])

# Monter les fichiers statiques pour le front-end
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates pour le rendu des pages
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def root(request: Request):
    """
    Route racine - Redirection vers l'interface utilisateur React
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """
    Vérifier la santé de l'application
    """
    # Vérifier la connexion à la base vectorielle
    vector_db_status = False
    try:
        if vector_store and vector_store.is_functional:
            vector_db_status = True
    except Exception as e:
        logger.error(f"Erreur avec le vector store: {str(e)}")
    
    # Réponse du health check
    return {
        "status": "healthy",
        "vector_db": vector_db_status,
        "version": app.version
    }

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Gestionnaire d'exception global
    """
    logger.error(f"Exception non gérée: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Une erreur inattendue s'est produite: {str(exc)}"}
    )

if __name__ == "__main__":
    # En mode développement, démarrer le serveur directement
    port = int(os.getenv("PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        reload=True
    ) 