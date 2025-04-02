import os
import weaviate
import qdrant_client
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Vector DB configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "weaviate").lower()
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Embedding model configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

# Collection/Class names
LEGAL_TEXTS_COLLECTION = "LegalTexts"

# Initialize embedding model
model = SentenceTransformer(EMBEDDING_MODEL)

class VectorStore:
    """Vector store abstraction layer supporting different backends"""
    
    def __init__(self):
        self.client = None
        self.db_type = VECTOR_DB_TYPE
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the vector database client based on configuration"""
        if self.db_type == "weaviate":
            self._initialize_weaviate()
        elif self.db_type == "qdrant":
            self._initialize_qdrant()
        else:
            raise ValueError(f"Unsupported vector database type: {self.db_type}")
            
    def _initialize_weaviate(self):
        """Initialize Weaviate client and schema"""
        try:
            auth_config = weaviate.auth.AuthApiKey(api_key=WEAVIATE_API_KEY) if WEAVIATE_API_KEY else None
            self.client = weaviate.Client(url=WEAVIATE_URL, auth_client_secret=auth_config)
            
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
        except Exception as e:
            logger.error(f"Error initializing Weaviate: {str(e)}")
            raise
            
    def _initialize_qdrant(self):
        """Initialize Qdrant client and collection"""
        try:
            self.client = qdrant_client.QdrantClient(
                url=QDRANT_URL, 
                api_key=QDRANT_API_KEY if QDRANT_API_KEY else None
            )
            
            # Check if collection exists, create if not
            try:
                collection_info = self.client.get_collection(collection_name=LEGAL_TEXTS_COLLECTION)
                logger.info(f"Found existing Qdrant collection: {LEGAL_TEXTS_COLLECTION}")
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    collection_name=LEGAL_TEXTS_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {LEGAL_TEXTS_COLLECTION}")
                
            logger.info("Qdrant client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Qdrant: {str(e)}")
            raise
            
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
        # Generate embedding
        embedding = model.encode(content).tolist()
        
        try:
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
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            raise
            
    def search(self, query: str, limit: int = 5, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the vector store
        
        Args:
            query: Search query
            limit: Maximum number of results
            doc_type: Filter by document type
            
        Returns:
            List of matching documents with similarity scores
        """
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        try:
            results = []
            
            if self.db_type == "weaviate":
                # Define filter if document type is specified
                filter_obj = {
                    "path": ["type"],
                    "operator": "Equal",
                    "valueText": doc_type
                } if doc_type else None
                
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
                filter_obj = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value=doc_type)
                        )
                    ]
                ) if doc_type else None
                
                # Perform vector search
                search_result = self.client.search(
                    collection_name=LEGAL_TEXTS_COLLECTION,
                    query_vector=query_embedding,
                    limit=limit,
                    filter=filter_obj
                )
                
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
            raise

# Singleton instance to be used throughout the application
vector_store = VectorStore() 