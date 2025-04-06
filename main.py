from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.utils.database import init_db
from app.utils.vector_store import vector_store
from app.models.user import create_admin_user
from dotenv import load_dotenv
import os
from loguru import logger
import time
import uvicorn

# Charger les variables d'environnement
load_dotenv()

# Configuration du logger
logger.add(
    os.getenv("LOG_FILE", "logs/law_assistant.log"),
    level=os.getenv("LOG_LEVEL", "INFO"),
    rotation="10 MB",
    retention="1 month",
    compression="zip"
)

# Créer l'application FastAPI
app = FastAPI(
    title="Assistant Juridique IA",
    description="API pour l'assistant juridique IA spécialisé dans le droit français",
    version="0.1.0"
)

# Configuration des CORS
origins = [
    "http://localhost:3009",
    "http://localhost:8009",
    "http://frontend:3009",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response

# Inclure les routes de l'API
app.include_router(api_router, prefix="/api")

# Endpoint de santé
@app.get("/health", tags=["Santé"])
async def health_check():
    """
    Vérifie l'état de santé de l'application
    """
    # Initialiser valeurs par défaut
    status = "Healthy"
    db_status = "Vérification non effectuée"
    vector_db_status = "Non disponible"
    vector_db_type = "Non configuré"
    
    # Vérifier la connexion à la base vectorielle
    try:
        if vector_store:
            if hasattr(vector_store, "is_functional") and vector_store.is_functional and vector_store.client:
                vector_db_type = vector_store.db_type
                try:
                    if vector_store.db_type == "qdrant":
                        _ = vector_store.client.get_collections()
                        vector_db_status = "OK"
                    elif vector_store.db_type == "weaviate":
                        _ = vector_store.client.schema.get()
                        vector_db_status = "OK"
                except Exception as e:
                    vector_db_status = f"Erreur: {str(e)}"
                    status = "Unhealthy"
            else:
                vector_db_status = "Client non initialisé ou non fonctionnel"
                # Ne pas considérer comme unhealthy - l'application peut fonctionner en mode dégradé
        else:
            vector_db_status = "VectorStore non initialisé"
            # Ne pas considérer comme unhealthy - l'application peut fonctionner en mode dégradé
    except Exception as e:
        vector_db_status = f"Erreur: {str(e)}"
        logger.error(f"Erreur de connexion à la base vectorielle: {str(e)}")
        status = "Unhealthy"
    
    return {
        "status": status,
        "details": {
            "api": "OK",
            "vector_db": {
                "status": vector_db_status,
                "type": vector_db_type
            }
        },
        "timestamp": time.time()
    }

# Événement de démarrage de l'application
@app.on_event("startup")
async def startup_event():
    logger.info("Application en démarrage...")
    
    # Configuration utilisée
    logger.info(f"VECTOR_DB_TYPE: {os.getenv('VECTOR_DB_TYPE', 'qdrant')}")
    logger.info(f"QDRANT_URL: {os.getenv('QDRANT_URL', 'http://qdrant:6339')}")
    logger.info(f"QDRANT_API_KEY: {'[SET]' if os.getenv('QDRANT_API_KEY') else '[NOT SET]'}")
    
    # Initialisation de la base de données
    try:
        await init_db()
        logger.info("Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
    
    # Création de l'utilisateur admin par défaut si nécessaire
    try:
        await create_admin_user()
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur admin: {str(e)}")
    
    # Vérification de la connexion à la base vectorielle
    try:
        if vector_store:
            if hasattr(vector_store, "is_functional") and vector_store.is_functional and vector_store.client:
                logger.info(f"Type de base vectorielle configuré: {vector_store.db_type}")
                if vector_store.db_type == "qdrant":
                    collections = vector_store.client.get_collections()
                    logger.info(f"Connexion à Qdrant réussie. Collections: {collections}")
                elif vector_store.db_type == "weaviate":
                    schema = vector_store.client.schema.get()
                    logger.info(f"Connexion à Weaviate réussie. Classes: {len(schema['classes'])}")
            else:
                logger.warning("VectorStore initialisé mais non fonctionnel")
        else:
            logger.warning("VectorStore non initialisé - les fonctionnalités de recherche seront limitées")
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à la base vectorielle: {str(e)}")
        logger.warning("L'application fonctionnera en mode dégradé sans recherche vectorielle")
    
    logger.info("Application prête à servir les requêtes")

# Si le fichier est exécuté directement
if __name__ == "__main__":
    # Récupérer le port de l'environnement ou utiliser 8009 par défaut
    port = int(os.getenv("APP_PORT", 8009))
    host = os.getenv("APP_HOST", "0.0.0.0")
    logger.info(f"Démarrage du serveur sur {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True) 