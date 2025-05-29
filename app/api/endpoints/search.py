from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.utils.vector_store import vector_store
from app.data.legifrance_api import LegifranceAPI
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles de données
class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float = None
    type: str = None
    date: str = None
    url: str = None
    metadata: Dict[str, Any] = None

# Initialisation de l'API Legifrance
legifrance_api = LegifranceAPI()

@router.get("/semantic", response_model=List[SearchResult])
async def semantic_search(
    q: str = Query(..., description="Requête de recherche"),
    limit: int = Query(10, description="Nombre maximum de résultats"),
    doc_type: Optional[str] = Query(None, description="Type de document"),
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)")
):
    """Recherche sémantique dans la base de vecteurs"""
    try:
        logger.info(f"Recherche sémantique: '{q}', type: {doc_type}, limit: {limit}")
        
        # Construction des filtres
        filters = {}
        if doc_type:
            filters["type"] = doc_type
            
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["gte"] = date_from
            if date_to:
                date_filter["lte"] = date_to
            if date_filter:
                filters["date"] = date_filter
                
        # Exécution de la recherche
        results = vector_store.search(
            query=q,
            limit=limit,
            filters=filters if filters else None
        )
        
        # Formatage des résultats
        formatted_results = []
        for result in results:
            formatted_result = SearchResult(
                id=result.get("id", ""),
                title=result.get("title", "Document sans titre"),
                content=result.get("content", ""),
                score=result.get("score", 0),
                type=result.get("type", ""),
                date=result.get("date", ""),
                url=result.get("url", ""),
                metadata=result.get("metadata", {})
            )
            formatted_results.append(formatted_result)
            
        return formatted_results
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche sémantique: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")


@router.get("/codes")
async def search_codes(
    q: str = Query(..., description="Requête de recherche"),
    limit: int = Query(10, description="Nombre maximum de résultats")
):
    """Recherche dans les codes via l'API Legifrance"""
    try:
        logger.info(f"Recherche dans les codes: '{q}', limit: {limit}")
        
        # Construction du payload pour l'API consult/code
        payload = {
            "textId": "LEGITEXT000006075116",  # ID par défaut pour le code constitutionnel
            "searchedString": q,
            "date": None,  # Date actuelle
            "abrogated": True,  # Inclure les textes abrogés
            "fromSuggest": True
        }
        
        # Appel direct à l'API Legifrance
        result = await legifrance_api._make_api_request("consult/code", "POST", payload)
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche dans les codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")


@router.get("/jurisprudence")
async def search_jurisprudence(
    q: str = Query(..., description="Requête de recherche"),
    limit: int = Query(10, description="Nombre maximum de résultats")
):
    """Recherche dans la jurisprudence via l'API Legifrance"""
    try:
        logger.info(f"Recherche dans la jurisprudence: '{q}', limit: {limit}")
        
        # Utilisation de l'API Legifrance pour la recherche directe
        result = await legifrance_api.search_jurisprudence(
            query=q,
            page=1,
            page_size=limit
        )
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche dans la jurisprudence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")


@router.get("/conseil")
async def search_conseil(
    q: str = Query(..., description="Requête de recherche"),
    limit: int = Query(10, description="Nombre maximum de résultats")
):
    """Recherche dans les décisions du Conseil d'État via l'API Legifrance"""
    try:
        logger.info(f"Recherche dans le Conseil d'État: '{q}', limit: {limit}")
        
        # Pour le Conseil d'État, on utilise la recherche jurisprudence
        # mais on filtre côté client
        result = await legifrance_api.search_jurisprudence(
            query=q, 
            page=1, 
            page_size=limit
        )
        
        # Filtre côté client pour ne garder que les décisions du Conseil d'État
        if "results" in result and isinstance(result["results"], list):
            result["results"] = [
                item for item in result["results"] 
                if "jurisdiction" in item and "conseil d'état" in item["jurisdiction"].lower()
            ]
            
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche dans le Conseil d'État: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")


@router.post("/code-details")
async def get_code_details(
    text_id: str,
    search_string: Optional[str] = None,
    date: Optional[str] = None,
    sct_cid: Optional[str] = None,
    include_abrogated: bool = False
):
    """Récupère les détails d'un code spécifique via l'API Legifrance"""
    try:
        logger.info(f"Récupération des détails du code: {text_id}")
        
        # Construction du payload pour l'API
        payload = {
            "textId": text_id,
            "searchedString": search_string,
            "date": date,  # Format attendu: YYYY-MM-DD
            "abrogated": include_abrogated
        }
        
        if sct_cid:
            payload["sctCid"] = sct_cid
            
        # Appel à l'API Legifrance
        result = await legifrance_api._make_api_request("consult/code", "POST", payload)
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des détails du code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur API: {str(e)}") 