import os
import importlib.util
import sys
# import weaviate
import qdrant_client
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Vector DB configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "qdrant").lower()  # Qdrant par défaut
# Utiliser les noms des services Docker pour la connexion interne
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6339")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Embedding model configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

# Collection/Class names
LEGAL_TEXTS_COLLECTION = "LegalTexts"

# Initialize embedding model
model = None
try:
    # Vérifier que huggingface_hub est à la bonne version
    import huggingface_hub
    logger.info(f"Using huggingface_hub version: {huggingface_hub.__version__}")
    
    # Vérifier que cached_download existe
    if not hasattr(huggingface_hub, "cached_download"):
        logger.warning("huggingface_hub does not have cached_download attribute. Patching...")
        # Si l'application démarre malgré cette erreur, on peut utiliser une alternative
        from huggingface_hub import hf_hub_download
        huggingface_hub.cached_download = hf_hub_download
    
    # Import sentence_transformers après la vérification/patch
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"Embedding model {EMBEDDING_MODEL} loaded successfully")
except ImportError as e:
    logger.error(f"Error importing required libraries: {str(e)}")
    logger.error("Vector store functionality will be disabled")
except Exception as e:
    logger.error(f"Error loading embedding model: {str(e)}")
    logger.error("Vector store functionality will be disabled")

# Import conditionnels pour éviter les erreurs au démarrage
if VECTOR_DB_TYPE == "weaviate":
    try:
        import weaviate
        logger.info("Weaviate library imported successfully")
    except ImportError:
        logger.error("Weaviate library not available")

if VECTOR_DB_TYPE == "qdrant":
    try:
        import qdrant_client
        from qdrant_client.http import models
        logger.info("Qdrant library imported successfully")
    except ImportError:
        logger.error("Qdrant library not available")

class VectorStore:
    """Vector store abstraction layer supporting different backends"""
    
    def __init__(self):
        self.client = None
        self.db_type = VECTOR_DB_TYPE
        self.is_functional = model is not None  # Flag pour indiquer si la classe peut fonctionner
        
        if not self.is_functional:
            logger.warning("VectorStore initialized in limited mode (no embedding model available)")
            return
            
        logger.info(f"Initializing vector store with backend: {self.db_type}")
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the vector database client based on configuration"""
        if not self.is_functional:
            return
            
        logger.info(f"Initializing vector store client for: {self.db_type}")
        if self.db_type == "weaviate":
            self._initialize_weaviate()
        elif self.db_type == "qdrant":
            self._initialize_qdrant()
        else:
            logger.warning(f"Unsupported vector database type: {self.db_type}, fallback to Qdrant")
            self.db_type = "qdrant"
            self._initialize_qdrant()
            
    def _initialize_weaviate(self):
        """Initialize Weaviate client and schema"""
        try:
            import weaviate
            logger.info(f"Connecting to Weaviate at {WEAVIATE_URL}")
            auth_config = weaviate.auth.AuthApiKey(api_key=WEAVIATE_API_KEY) if WEAVIATE_API_KEY else None
            
            # Augmenter le timeout pour donner plus de temps au service de démarrer
            self.client = weaviate.Client(
                url=WEAVIATE_URL, 
                auth_client_secret=auth_config,
                timeout_config=(10, 60)  # 10s de connect timeout, 60s de read timeout
            )
            
            # Check if the schema exists, create if not
            if not self.client.schema.contains(LEGAL_TEXTS_COLLECTION):
                class_obj = {
                    "class": LEGAL_TEXTS_COLLECTION,
                    "description": "Collection of French legal texts for semantic search",
                    "vectorizer": "none",  # We provide our own vectors
                    "properties": [
                        {"name": "title", "dataType": ["text"]},
                        {"name": "content", "dataType": ["text"]},
                        {"name": "type", "dataType": ["text"]},
                        {"name": "date", "dataType": ["date"]},
                        {"name": "url", "dataType": ["text"]},
                        {"name": "metadata", "dataType": ["object"]}
                    ]
                }
                self.client.schema.create_class(class_obj)
                logger.info(f"Created Weaviate schema for {LEGAL_TEXTS_COLLECTION}")
            
            logger.info("Weaviate client initialized successfully")
        except ImportError:
            logger.error("Weaviate library not available")
            self.db_type = "qdrant"
            self._initialize_qdrant()
        except Exception as e:
            logger.error(f"Error initializing Weaviate: {str(e)}")
            logger.info("Falling back to Qdrant...")
            self.db_type = "qdrant"
            self._initialize_qdrant()
            
    def _initialize_qdrant(self):
        """Initialize Qdrant client and collection"""
        try:
            import qdrant_client
            from qdrant_client.http import models
            
            logger.info(f"Connecting to Qdrant at {QDRANT_URL} with API key: {'[SET]' if QDRANT_API_KEY else '[NOT SET]'}")
            self.client = qdrant_client.QdrantClient(
                url=QDRANT_URL, 
                api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
                timeout=60  # Augmenter le timeout pour laisser plus de temps au service
            )
            
            # Check if collection exists, create if not
            try:
                collection_info = self.client.get_collection(collection_name=LEGAL_TEXTS_COLLECTION)
                logger.info(f"Found existing Qdrant collection: {LEGAL_TEXTS_COLLECTION}")
            except Exception as e:
                logger.info(f"Collection {LEGAL_TEXTS_COLLECTION} not found, creating: {str(e)}")
                # Collection doesn't exist, create it
                try:
                    self.client.create_collection(
                        collection_name=LEGAL_TEXTS_COLLECTION,
                        vectors_config=models.VectorParams(
                            size=EMBEDDING_DIMENSION,
                            distance=models.Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {LEGAL_TEXTS_COLLECTION}")
                except Exception as collection_error:
                    # Vérifie si c'est une erreur "collection exists"
                    if "already exists" in str(collection_error):
                        logger.info(f"Collection {LEGAL_TEXTS_COLLECTION} already exists, continuing...")
                    else:
                        # Si c'est une autre erreur, on la propage
                        logger.error(f"Error creating Qdrant collection: {str(collection_error)}")
                        raise
                
            logger.info("Qdrant client initialized successfully")
        except ImportError:
            logger.error("Qdrant library not available")
            self.is_functional = False
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Collection {LEGAL_TEXTS_COLLECTION} already exists, continuing...")
                logger.info("Qdrant client initialized successfully")
            else:
                logger.error(f"Error initializing Qdrant: {str(e)}")
                self.is_functional = False
            
    def add_document(self, doc_id: str, title: str, content: str, doc_type: str, 
                    date: str, url: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a document to the vector store
        
        Args:
            doc_id: Unique identifier for the document
            title: Document title
            content: Document text content
            doc_type: Document type (loi, jurisprudence, etc.)
            date: Document date
            url: URL to the source
            metadata: Additional metadata
        """
        if not self.is_functional or not self.client:
            logger.warning("Cannot add document: VectorStore not functional")
            return False
            
        try:
            # Generate embedding
            embedding = model.encode(content).tolist()
            
            if self.db_type == "weaviate":
                self.client.data_object.create(
                    class_name=LEGAL_TEXTS_COLLECTION,
                    data_object={
                        "title": title,
                        "content": content,
                        "type": doc_type,
                        "date": date,
                        "url": url or "",
                        "metadata": metadata or {}
                    },
                    uuid=doc_id,
                    vector=embedding
                )
            elif self.db_type == "qdrant":
                self.client.upsert(
                    collection_name=LEGAL_TEXTS_COLLECTION,
                    points=[
                        models.PointStruct(
                            id=doc_id,
                            vector=embedding,
                            payload={
                                "title": title,
                                "content": content,
                                "type": doc_type,
                                "date": date,
                                "url": url or "",
                                "metadata": metadata or {}
                            }
                        )
                    ]
                )
            
            logger.info(f"Added document to vector store: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            return False
            
    def search(self, query: str, limit: int = 5, doc_type: Optional[str] = None, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the vector store
        
        Args:
            query: Search query
            limit: Maximum number of results
            doc_type: Filter by document type
            filters: Additional filters to apply (dictionary)
            
        Returns:
            List of matching documents with similarity scores
        """
        if not self.is_functional or not self.client:
            logger.warning("Cannot search: VectorStore not functional")
            return []
            
        try:
            # Generate query embedding
            query_embedding = model.encode(query).tolist()
            
            results = []
            
            if self.db_type == "weaviate":
                # Define filter if document type is specified
                filter_obj = {
                    "path": ["type"],
                    "operator": "Equal",
                    "valueText": doc_type
                } if doc_type else None
                
                # Apply additional filters if provided
                # Note: This is a simplified implementation
                if filters:
                    # TODO: Implement more complex filtering logic
                    pass
                
                # Perform vector search
                result = self.client.query.get(
                    LEGAL_TEXTS_COLLECTION, 
                    ["title", "content", "type", "date", "url", "metadata"]
                ).with_near_vector(
                    {"vector": query_embedding}
                ).with_where(
                    filter_obj
                ).with_limit(limit).do()
                
                # Format results
                for item in result["data"]["Get"][LEGAL_TEXTS_COLLECTION]:
                    results.append({
                        "id": item["_additional"]["id"],
                        "title": item["title"],
                        "content": item["content"],
                        "type": item["type"],
                        "date": item["date"],
                        "url": item["url"],
                        "metadata": item["metadata"],
                        "score": item["_additional"]["score"]
                    })
                    
            elif self.db_type == "qdrant":
                # Define filter if document type is specified
                from qdrant_client.http import models
                filter_obj = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value=doc_type)
                        )
                    ]
                ) if doc_type else None
                
                # Apply additional filters if provided
                if filters:
                    # TODO: Implement more complex filtering logic
                    pass
                
                # Perform vector search
                search_params = {
                    "collection_name": LEGAL_TEXTS_COLLECTION,
                    "query_vector": query_embedding,
                    "limit": limit,
                }
                
                # Only add filter if it's defined
                if filter_obj:
                    search_params["filter"] = filter_obj
                
                # Perform vector search with corrected params
                search_result = self.client.search(**search_params)
                
                # Format results
                for scored_point in search_result:
                    results.append({
                        "id": scored_point.id,
                        "title": scored_point.payload["title"],
                        "content": scored_point.payload["content"],
                        "type": scored_point.payload["type"],
                        "date": scored_point.payload["date"],
                        "url": scored_point.payload["url"],
                        "metadata": scored_point.payload["metadata"],
                        "score": scored_point.score
                    })
                    
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
            
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID
        
        Args:
            doc_id: The document ID
            
        Returns:
            Document data or None if not found
        """
        if not self.is_functional or not self.client:
            logger.warning("Cannot get document: VectorStore not functional")
            return None
            
        try:
            if self.db_type == "weaviate":
                # Get document by ID in Weaviate
                result = self.client.data_object.get(
                    LEGAL_TEXTS_COLLECTION,
                    doc_id,
                    with_vector=False
                )
                
                if not result:
                    return None
                    
                # Format the result
                return {
                    "id": doc_id,
                    "title": result.get("properties", {}).get("title", ""),
                    "content": result.get("properties", {}).get("content", ""),
                    "type": result.get("properties", {}).get("type", ""),
                    "date": result.get("properties", {}).get("date", ""),
                    "url": result.get("properties", {}).get("url", ""),
                    "metadata": result.get("properties", {}).get("metadata", {})
                }
                
            elif self.db_type == "qdrant":
                # Get document by ID in Qdrant
                results = self.client.retrieve(
                    collection_name=LEGAL_TEXTS_COLLECTION,
                    ids=[doc_id]
                )
                
                if not results:
                    return None
                
                # Get the first result (there should be only one)
                point = results[0]
                
                # Format the result
                return {
                    "id": point.id,
                    "title": point.payload.get("title", ""),
                    "content": point.payload.get("content", ""),
                    "type": point.payload.get("type", ""),
                    "date": point.payload.get("date", ""),
                    "url": point.payload.get("url", ""),
                    "metadata": point.payload.get("metadata", {})
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {str(e)}")
            return None

# Singleton instance to be used throughout the application
try:
    vector_store = VectorStore()
    logger.info(f"VectorStore initialized successfully, functional: {vector_store.is_functional}")
except Exception as e:
    logger.error(f"Failed to initialize VectorStore: {str(e)}")
    # Provide a minimal object for the application to start
    vector_store = None 