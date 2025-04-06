import os
from typing import List
try:
    from pydantic import BaseSettings
except ImportError:
    # Fallback pour les versions plus récentes de Pydantic (V2+)
    from pydantic_settings import BaseSettings
try:
    from dotenv import load_dotenv
except ImportError:
    # Message en cas d'absence de python-dotenv
    print("WARNING: python-dotenv not installed. Environment variables should be set manually.")
    
    def load_dotenv():
        pass

# Charger les variables d'environnement
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration de l'application
    Les valeurs par défaut sont utilisées si les variables d'environnement ne sont pas définies
    """
    # Paramètres d'application
    APP_NAME: str = "Assistant Juridique IA"
    API_V1_STR: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    ENV: str = os.getenv("ENV", "development")
    
    # Paramètres de base de données
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5439")  # Port standard PostgreSQL
    DB_NAME: str = os.getenv("DB_NAME", "law_assistant")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Construit l'URL de connexion à la base de données
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Paramètres CORS - Accepter les connexions de différentes origines
    CORS_ORIGINS: List[str] = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Charger les origines CORS depuis la variable d'environnement
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",")]
        
        # Ajouter des origines par défaut si la liste est vide
        if not self.CORS_ORIGINS:
            self.CORS_ORIGINS = [
                "http://localhost:3000",   # URL frontend React standard
                "http://localhost:3009",   # URL frontend React dans docker-compose
                "http://localhost:8009",   # URL backend FastAPI
                "http://127.0.0.1:3000",   # Alternative localhost
                "http://127.0.0.1:3009",   # Alternative localhost
                "http://127.0.0.1:8009",   # Alternative localhost
                "http://frontend:3009",    # URL frontend React container dans le réseau Docker
                "http://app:8009",         # URL backend container dans le réseau Docker
            ]
    
    # Configuration JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    
    # Configuration du serveur
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8009"))
    
    class Config:
        # Utiliser les variables d'environnement pour remplacer les valeurs par défaut
        env_file = ".env"

# Créer une instance de la configuration
settings = Settings() 