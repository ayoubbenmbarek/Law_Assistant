from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from app.models.user import get_current_user, User
from app.models.response import LegalResponse
from app.models.query import QueryRequest
from app.models.processor import query_processor

router = APIRouter()

@router.post("/", response_model=LegalResponse)
async def legal_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint principal pour interroger l'assistant juridique.
    Traite la question juridique et renvoie une réponse structurée.
    """
    try:
        # Log the query
        logger.info(f"Requête reçue: {request.query} (user: {current_user.email})")
        
        # Process the query using the query processor
        response = await query_processor.process_query(
            request=request,
            is_professional=current_user.is_professional
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors du traitement de la requête") 