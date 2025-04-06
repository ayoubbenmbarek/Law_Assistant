from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import time
from loguru import logger

from app.models.sources import (
    LegalSource, 
    SearchSourceRequest, 
    SearchSourceResponse, 
    SourceType,
    SourceOrigin,
    LegalDomain,
    JurisdictionType
)
from app.utils.database import get_db
from app.utils.vector_store import vector_store
from app.models.user import get_current_active_user, User

router = APIRouter()

@router.post("/search", response_model=SearchSourceResponse)
async def search_sources(
    request: SearchSourceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Recherche de sources juridiques avec différents filtres
    """
    start_time = time.time()
    
    # Construire les filtres pour la recherche
    filters = {}
    
    if request.types:
        filters["type"] = [t.value for t in request.types]
    
    if request.origins:
        filters["origin"] = [o.value for o in request.origins]
    
    if request.domains:
        filters["domain"] = [d.value for d in request.domains]
    
    if request.date_start or request.date_end:
        date_filter = {}
        if request.date_start:
            date_filter["gte"] = request.date_start
        if request.date_end:
            date_filter["lte"] = request.date_end
        
        filters["date"] = date_filter
    
    # Effectuer la recherche dans la base vectorielle
    try:
        search_results = vector_store.search(
            query=request.query,
            limit=request.limit,
            filters=filters
        )
        
        # Convertir les résultats en LegalSource
        sources = []
        for result in search_results:
            # Extraction des données du résultat
            source_type = result.get("doc_type", "autre")
            source_origin = result.get("metadata", {}).get("source", "autre").lower() if result.get("metadata") else "autre"
            domains = result.get("metadata", {}).get("domains", []) if result.get("metadata") else []
            jurisdiction = result.get("metadata", {}).get("juridiction", None) if result.get("metadata") else None
            
            # Conversion en types énumérés
            try:
                type_enum = SourceType(source_type)
            except ValueError:
                type_enum = SourceType.AUTRE
                
            try:
                origin_enum = SourceOrigin(source_origin)
            except ValueError:
                origin_enum = SourceOrigin.AUTRE
                
            # Conversion des domaines
            domain_enums = []
            for domain in domains:
                try:
                    domain_enums.append(LegalDomain(domain.lower()))
                except ValueError:
                    continue
                    
            # Conversion de la juridiction
            jurisdiction_enum = None
            if jurisdiction:
                try:
                    jurisdiction_enum = JurisdictionType(jurisdiction.lower())
                except ValueError:
                    jurisdiction_enum = None
            
            # Création de l'objet LegalSource
            source = LegalSource(
                id=result.get("id", ""),
                title=result.get("title", ""),
                type=type_enum,
                content=result.get("content", ""),
                date=result.get("date", ""),
                url=result.get("url", ""),
                metadata=result.get("metadata", {}),
                origin=origin_enum,
                domain=domain_enums,
                jurisdiction=jurisdiction_enum,
                score=result.get("score", None)
            )
            sources.append(source)
            
        # Calculer le temps de requête
        query_time = time.time() - start_time
        
        # Construire la réponse
        response = SearchSourceResponse(
            sources=sources,
            total_count=len(sources),  # Dans une implémentation complète, vous voudrez le nombre total sans limite
            query_time=query_time
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche de sources: {str(e)}"
        )

@router.get("/types", response_model=List[str])
async def get_source_types():
    """Récupérer la liste des types de sources disponibles"""
    return [t.value for t in SourceType]

@router.get("/origins", response_model=List[str])
async def get_source_origins():
    """Récupérer la liste des origines de sources disponibles"""
    return [o.value for o in SourceOrigin]

@router.get("/domains", response_model=List[str])
async def get_legal_domains():
    """Récupérer la liste des domaines juridiques disponibles"""
    return [d.value for d in LegalDomain]

@router.get("/jurisdictions", response_model=List[str])
async def get_jurisdictions():
    """Récupérer la liste des juridictions disponibles"""
    return [j.value for j in JurisdictionType]

@router.get("/{source_id}", response_model=LegalSource)
async def get_source_by_id(
    source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une source juridique par son ID
    """
    try:
        logger.info(f"Recherche de la source avec ID: {source_id}")
        
        if not vector_store or not vector_store.is_functional:
            logger.error("Vector store non disponible")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de recherche vectorielle non disponible actuellement"
            )
            
        # Rechercher la source dans la base vectorielle
        result = vector_store.get_document(source_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Source juridique avec l'ID {source_id} non trouvée"
            )
            
        # Conversion comme dans la fonction de recherche
        source_type = result.get("doc_type", "autre")
        source_origin = result.get("metadata", {}).get("source", "autre").lower() if result.get("metadata") else "autre"
        domains = result.get("metadata", {}).get("domains", []) if result.get("metadata") else []
        jurisdiction = result.get("metadata", {}).get("juridiction", None) if result.get("metadata") else None
        
        # Conversion en types énumérés
        try:
            type_enum = SourceType(source_type)
        except ValueError:
            type_enum = SourceType.AUTRE
            
        try:
            origin_enum = SourceOrigin(source_origin)
        except ValueError:
            origin_enum = SourceOrigin.AUTRE
            
        # Conversion des domaines
        domain_enums = []
        for domain in domains:
            try:
                domain_enums.append(LegalDomain(domain.lower()))
            except ValueError:
                continue
                
        # Conversion de la juridiction
        jurisdiction_enum = None
        if jurisdiction:
            try:
                jurisdiction_enum = JurisdictionType(jurisdiction.lower())
            except ValueError:
                jurisdiction_enum = None
        
        # Création de l'objet LegalSource
        source = LegalSource(
            id=result.get("id", ""),
            title=result.get("title", ""),
            type=type_enum,
            content=result.get("content", ""),
            date=result.get("date", ""),
            url=result.get("url", ""),
            metadata=result.get("metadata", {}),
            origin=origin_enum,
            domain=domain_enums,
            jurisdiction=jurisdiction_enum
        )
        
        return source
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la source: {str(e)}"
        )

@router.get("/sources/search", response_model=List[Dict])
async def search_sources(
    query: str,
    limit: int = 10,
    doc_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> List[Dict]:
    """
    Recherche des sources juridiques similaires à la requête
    """
    logger.info(f"Recherche de sources pour: '{query}', type: {doc_type}, limite: {limit}")
    
    if not vector_store or not vector_store.is_functional:
        logger.error("Vector store non disponible")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de recherche vectorielle non disponible actuellement"
        )
    
    results = vector_store.search(
        query=query,
        limit=limit,
        doc_type=doc_type
    )
    
    logger.info(f"Nombre de résultats trouvés: {len(results)}")
    return results 