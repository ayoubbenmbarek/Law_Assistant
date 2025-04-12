from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.query import QueryRequest
from app.models.response import LegalResponse
from app.utils.database import get_db
from app.utils.vector_store import vector_store
from loguru import logger
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/query", response_model=LegalResponse)
async def create_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Endpoint pour traiter une requête juridique et retourner une réponse structurée
    """
    try:
        # Log de la requête
        logger.info(f"Requête reçue: {query_request.query} (Domaine: {query_request.domain})")
        
        # Vérifier si le vector_store est disponible et fonctionnel
        if not vector_store or not hasattr(vector_store, "is_functional") or not vector_store.is_functional or not vector_store.client:
            logger.error("Base vectorielle non disponible ou non fonctionnelle pour la recherche")
            # On retourne une réponse par défaut pour éviter de bloquer l'application
            return LegalResponse(
                introduction=f"Votre question sur '{query_request.query}' concerne le domaine {query_request.domain or 'général'}",
                legal_framework="La base de connaissances juridiques n'est pas disponible actuellement.",
                application="Impossible d'analyser votre cas spécifique sans accès à la base de données.",
                recommendations=["Réessayer ultérieurement", "Contacter le support technique"],
                sources=[],
                date_updated=datetime.now().isoformat(),
                disclaimer="Service temporairement indisponible. Cette réponse est générée automatiquement."
            )
        
        # Recherche de sources pertinentes dans la base vectorielle
        logger.info(f"Recherche dans {vector_store.db_type} avec la requête: {query_request.query}")
        relevant_docs = vector_store.search(
            query=query_request.query, 
            limit=5,
            doc_type=query_request.domain if query_request.domain else None
        )
        
        logger.info(f"Nombre de documents pertinents trouvés: {len(relevant_docs)}")
        
        # Si aucun document n'est trouvé, retourner une réponse appropriée
        if not relevant_docs:
            return LegalResponse(
                introduction=f"Votre question sur '{query_request.query}' a été traitée.",
                legal_framework="Aucune source juridique pertinente n'a été trouvée dans notre base de données.",
                application="Impossible de fournir une analyse spécifique sans sources juridiques pertinentes.",
                recommendations=["Reformuler votre question", "Préciser le domaine juridique", "Consulter un professionnel du droit"],
                sources=[],
                date_updated=datetime.now().isoformat(),
                disclaimer="Cette réponse est fournie à titre informatif uniquement et ne constitue pas un avis juridique professionnel."
            )
        
        # Construction de la liste des sources (en tant que chaînes de caractères)
        sources_raw = []
        sources_strings = []
        
        for doc in relevant_docs:
            # Garder la structure complète pour une utilisation potentielle
            source_dict = {
                "id": doc.get("id", str(uuid.uuid4())),
                "title": doc.get("title", "Sans titre"),
                "type": doc.get("type", "Non spécifié"),
                "content": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                "date": doc.get("date", datetime.now().isoformat()),
                "url": doc.get("url", "")
            }
            sources_raw.append(source_dict)
            
            # Créer une représentation textuelle pour chaque source
            source_text = f"{source_dict['title']} ({source_dict.get('date', 'N/A')})"
            if source_dict.get('url'):
                source_text += f" - {source_dict['url']}"
            
            sources_strings.append(source_text)
        
        # Exemple de réponse (à remplacer par la génération réelle)
        legal_response = LegalResponse(
            introduction="Votre question concerne le domaine du droit " + (query_request.domain or "général"),
            legal_framework="Selon les articles pertinents du Code...",
            application="Dans votre cas spécifique...",
            exceptions="Il existe cependant des exceptions...",
            recommendations=["Consulter un avocat spécialisé", "Rassembler les documents pertinents"],
            sources=sources_strings,  # Utiliser la liste de chaînes de caractères
            date_updated=datetime.now().isoformat(),
            disclaimer="Cette réponse est fournie à titre informatif uniquement et ne constitue pas un avis juridique professionnel."
        )
        
        return legal_response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/domains")
async def get_domains():
    """
    Récupérer la liste des domaines juridiques disponibles
    """
    domains = [
        {"id": "fiscal", "name": "Droit Fiscal"},
        {"id": "travail", "name": "Droit du Travail"},
        {"id": "affaires", "name": "Droit des Affaires"},
        {"id": "famille", "name": "Droit de la Famille"},
        {"id": "immobilier", "name": "Droit Immobilier"},
        {"id": "consommation", "name": "Droit de la Consommation"},
        {"id": "penal", "name": "Droit Pénal"},
        {"id": "administratif", "name": "Droit Administratif"},
        {"id": "constitutionnel", "name": "Droit Constitutionnel"},
        {"id": "rgpd", "name": "Protection des Données (RGPD)"},
        {"id": "propriete", "name": "Propriété Intellectuelle"},
        {"id": "environnement", "name": "Droit de l'Environnement"},
        {"id": "sante", "name": "Droit de la Santé"},
        {"id": "social", "name": "Sécurité Sociale"},
        {"id": "europeen", "name": "Droit Européen"}
    ]
    return domains 