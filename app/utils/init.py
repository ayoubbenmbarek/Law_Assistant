import os
import asyncio
from loguru import logger
from app.utils.database import init_db
from app.utils.vector_store import vector_store
from app.data.legifrance_api import legifrance_api

async def initialize_app():
    """
    Initialize the application services
    
    This function:
    1. Creates required directories
    2. Initializes the database
    3. Checks and initializes the vector store
    4. Loads initial data if needed
    """
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.makedirs("logs")
            logger.info("Created logs directory")
            
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize vector store - this is already done when importing
        # as the vector_store is instantiated on import
        logger.info(f"Vector store initialized with type: {vector_store.db_type}")
        
        # Test the Legifrance API connection (if configured)
        if os.getenv("LEGIFRANCE_API_KEY") and os.getenv("LEGIFRANCE_API_SECRET"):
            try:
                await legifrance_api.authenticate()
                logger.info("Successfully connected to Legifrance API")
            except Exception as e:
                logger.warning(f"Could not connect to Legifrance API: {str(e)}")
                logger.warning("Will use mock data for legal sources")
        else:
            logger.warning("Legifrance API not configured. Will use mock data for legal sources")
            
        # Load initial sample data
        await load_sample_data()
        
        logger.info("Application initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")
        raise

async def load_sample_data():
    """
    Load sample data into the vector store
    
    This is used to have initial data for demonstration purposes
    when the application is first started.
    """
    try:
        # Sample legal sources with embeddings
        sample_sources = [
            {
                "id": "LEGIARTI000006436298",
                "title": "Article 1134 du Code Civil",
                "type": "loi",
                "content": "Les conventions légalement formées tiennent lieu de loi à ceux qui les ont faites.",
                "date": "2023-01-01",
                "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006436298",
                "metadata": {
                    "code": "Code Civil",
                    "section": "Des contrats"
                }
            },
            {
                "id": "LEGIARTI000037730625",
                "title": "Article L1231-1 du Code du travail",
                "type": "loi",
                "content": "Le contrat de travail à durée indéterminée peut être rompu à l'initiative de l'employeur ou du salarié, ou d'un commun accord, dans les conditions prévues par les dispositions du présent titre.",
                "date": "2023-01-01",
                "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037730625",
                "metadata": {
                    "code": "Code du travail",
                    "section": "Rupture du contrat de travail à durée indéterminée"
                }
            },
            {
                "id": "LEGIARTI000038814802",
                "title": "Article 220 du Code général des impôts",
                "type": "loi",
                "content": "Chacun des époux est seul imposable pour les revenus dont il a disposé pendant l'année de l'imposition.",
                "date": "2023-01-01",
                "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038814802",
                "metadata": {
                    "code": "Code général des impôts",
                    "section": "Imposition des couples mariés"
                }
            }
        ]
        
        # Add to vector store
        await legifrance_api.import_to_vector_store(sample_sources)
        logger.info(f"Loaded {len(sample_sources)} sample sources into vector store")
        
    except Exception as e:
        logger.error(f"Error loading sample data: {str(e)}")
        logger.warning("Application will start without sample data") 