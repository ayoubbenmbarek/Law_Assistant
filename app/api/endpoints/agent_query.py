"""
API Endpoint for Agent-Enhanced Legal Queries
New endpoint that uses multi-agent system
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from loguru import logger

from app.models.query import QueryRequest
from app.models.response import LegalResponse
from app.models.agent_processor import AgentQueryProcessor, get_recommended_processor
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("/agent-query", response_model=LegalResponse)
async def agent_enhanced_query(
    request: QueryRequest,
    agent_mode: Optional[str] = Query("auto", enum=["auto", "simple", "full", "disabled"]),
    current_user = Depends(get_current_user)
):
    """
    Traite une requête juridique avec le système multi-agents

    **Modes disponibles:**
    - `auto` (défaut): Sélection automatique selon la complexité
    - `simple`: 2 agents (recherche + rédaction) - rapide
    - `full`: 4-5 agents (recherche + expert + vérification + rédaction + qualité) - approfondi
    - `disabled`: Mode standard sans agents (OpenAI direct)

    **Exemple de requête:**
    ```json
    {
        "query": "Quel est le délai de rétractation pour un achat en ligne ?",
        "domain": "consommation",
        "context": "Achat effectué sur un site français"
    }
    ```
    """
    try:
        # Déterminer le processeur à utiliser
        if agent_mode == "auto":
            # Logique simple de détection de complexité
            complexity = _detect_query_complexity(request.query)
            processor = get_recommended_processor(complexity)
        elif agent_mode == "disabled":
            processor = AgentQueryProcessor(use_agents=False)
        else:
            processor = AgentQueryProcessor(
                use_agents=True,
                agent_mode=agent_mode
            )

        # Déterminer si l'utilisateur est professionnel
        is_professional = current_user.is_professional if hasattr(current_user, 'is_professional') else False

        # Traiter la requête
        logger.info(f"Processing query with agent_mode={agent_mode} for user {current_user.id if hasattr(current_user, 'id') else 'unknown'}")

        response = await processor.process_query(
            request=request,
            is_professional=is_professional
        )

        return response

    except Exception as e:
        logger.error(f"Error in agent query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement de la requête: {str(e)}")


@router.post("/agent-research", response_model=dict)
async def direct_agent_research(
    query: str,
    domain: Optional[str] = None,
    use_domain_specialist: bool = False,
    current_user = Depends(get_current_user)
):
    """
    Recherche juridique directe avec les agents (sans structure LegalResponse)

    Retourne le résultat brut des agents pour intégration personnalisée

    Args:
        query: La question juridique
        domain: Domaine juridique spécifique
        use_domain_specialist: Ajouter un agent expert du domaine
    """
    try:
        from app.agents.legal_crew import LegalResearchCrew

        crew = LegalResearchCrew(
            process_type="sequential",
            verbose=False,
            domain_specialization=domain if use_domain_specialist else None
        )

        is_professional = current_user.is_professional if hasattr(current_user, 'is_professional') else False

        result = crew.research_legal_query(
            query=query,
            domain=domain,
            is_professional=is_professional
        )

        return result

    except Exception as e:
        logger.error(f"Error in agent research endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-status")
async def agent_system_status():
    """
    Vérifie le statut du système multi-agents

    Returns:
        Informations sur la disponibilité et configuration des agents
    """
    import os

    status = {
        "agents_available": True,
        "llm_backend": "ollama" if "localhost" in os.getenv("OPENAI_BASE_URL", "") else "openai",
        "ollama_model": os.getenv("OLLAMA_MODEL", "mistral:latest"),
        "modes_available": ["simple", "full"],
        "agent_types": [
            "Legal Researcher",
            "Citation Verifier",
            "Legal Writer",
            "Quality Reviewer",
            "Domain Specialists"
        ]
    }

    # Vérifier la connexion au LLM
    try:
        from app.agents.agents import get_llm
        llm = get_llm()
        status["llm_connected"] = True
    except Exception as e:
        status["llm_connected"] = False
        status["llm_error"] = str(e)

    return status


def _detect_query_complexity(query: str) -> str:
    """
    Détecte automatiquement la complexité d'une requête

    Args:
        query: La question posée

    Returns:
        "simple", "medium" ou "complex"
    """
    # Indicateurs de complexité
    complex_keywords = [
        "implications", "conséquences", "analyser", "comparer",
        "conditions", "procédure", "recours", "stratégie",
        "fiscales", "régime", "statut juridique"
    ]

    simple_keywords = [
        "c'est quoi", "définition", "qu'est-ce que",
        "délai", "montant", "taux"
    ]

    query_lower = query.lower()

    # Critères de complexité
    word_count = len(query.split())
    has_complex_keywords = any(kw in query_lower for kw in complex_keywords)
    has_simple_keywords = any(kw in query_lower for kw in simple_keywords)

    if has_simple_keywords or word_count < 10:
        return "simple"
    elif has_complex_keywords or word_count > 30:
        return "complex"
    else:
        return "medium"