"""
Agent-Enhanced Query Processor
Integrates multi-agent system with existing QueryProcessor
Provides two modes: standard (OpenAI) and agent-enhanced (CrewAI)
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

from app.agents.legal_crew import LegalResearchCrew, SimpleLegalCrew
from app.models.query import QueryRequest
from app.models.response import LegalResponse
from app.models.processor import QueryProcessor

load_dotenv()


class AgentQueryProcessor(QueryProcessor):
    """
    Enhanced QueryProcessor with multi-agent capabilities

    Modes d'utilisation:
    1. Standard: Utilise l'OpenAI directement (hérite du QueryProcessor)
    2. Agent Simple: 2 agents pour recherche rapide
    3. Agent Complet: 4-5 agents pour analyse approfondie
    """

    def __init__(self, use_agents: bool = False, agent_mode: str = "simple"):
        """
        Initialise le processeur avec ou sans agents

        Args:
            use_agents: Activer le mode multi-agents
            agent_mode: "simple" (2 agents) ou "full" (4-5 agents)
        """
        super().__init__()
        self.use_agents = use_agents
        self.agent_mode = agent_mode

        if use_agents:
            if agent_mode == "simple":
                self.crew = SimpleLegalCrew(verbose=False)
                logger.info("AgentQueryProcessor initialized with SimpleLegalCrew")
            else:
                self.crew = LegalResearchCrew(
                    process_type="sequential",
                    verbose=False
                )
                logger.info("AgentQueryProcessor initialized with full LegalResearchCrew")
        else:
            self.crew = None
            logger.info("AgentQueryProcessor initialized without agents (standard mode)")

    async def process_query(
        self,
        request: QueryRequest,
        is_professional: bool = False,
        force_agents: bool = False
    ) -> LegalResponse:
        """
        Traite une requête avec ou sans agents selon la configuration

        Args:
            request: La requête utilisateur
            is_professional: Si l'utilisateur est un professionnel
            force_agents: Forcer l'utilisation des agents pour cette requête

        Returns:
            Réponse juridique structurée
        """
        use_agents_for_query = self.use_agents or force_agents

        if use_agents_for_query and self.crew:
            return await self._process_with_agents(request, is_professional)
        else:
            # Fallback sur le mode standard (OpenAI direct)
            return await super().process_query(request, is_professional)

    async def _process_with_agents(
        self,
        request: QueryRequest,
        is_professional: bool
    ) -> LegalResponse:
        """
        Traite la requête avec le système multi-agents

        Args:
            request: La requête utilisateur
            is_professional: Si c'est un professionnel

        Returns:
            Réponse juridique structurée
        """
        try:
            logger.info(f"Processing query with {self.agent_mode} agent mode")

            # Préparer le contexte
            context = {
                "query": request.query,
                "domain": request.domain,
                "context": request.context,
                "is_professional": is_professional
            }

            # Exécuter avec les agents
            if isinstance(self.crew, SimpleLegalCrew):
                result = self.crew.quick_research(
                    query=request.query,
                    domain=request.domain
                )
            else:
                result = self.crew.research_legal_query(
                    query=request.query,
                    domain=request.domain,
                    context={"additional_context": request.context},
                    is_professional=is_professional
                )

            if not result.get("success"):
                logger.error(f"Agent processing failed: {result.get('error')}")
                # Fallback sur le mode standard
                return await super().process_query(request, is_professional)

            # Parser le résultat des agents en LegalResponse
            return self._parse_agent_result(result.get("result"), request)

        except Exception as e:
            logger.error(f"Error in agent processing: {str(e)}")
            # Fallback sur le mode standard en cas d'erreur
            return await super().process_query(request, is_professional)

    def _parse_agent_result(self, agent_result: str, request: QueryRequest) -> LegalResponse:
        """
        Parse le résultat des agents en LegalResponse structurée

        Args:
            agent_result: Résultat brut des agents
            request: Requête originale

        Returns:
            LegalResponse structurée
        """
        # Le résultat des agents est déjà structuré
        # On pourrait parser davantage ici si nécessaire

        # Pour l'instant, on retourne une structure simple
        # Dans une vraie implémentation, on utiliserait un LLM pour parser
        # ou on structurerait mieux la sortie des agents

        return LegalResponse(
            introduction=f"Réponse générée par notre équipe d'agents IA spécialisés en droit français.",
            legal_framework=agent_result[:1000] if isinstance(agent_result, str) else str(agent_result)[:1000],
            application="Voir le cadre juridique ci-dessus pour l'application détaillée.",
            exceptions=None,
            recommendations=[
                "Consultez un avocat pour un conseil personnalisé",
                "Vérifiez les textes les plus récents"
            ],
            sources=["Analyse multi-agents CrewAI", "Base de données juridique"],
            date_updated=datetime.now().strftime("%Y-%m-%d"),
            disclaimer="""Cette réponse est fournie à titre informatif uniquement et ne constitue pas un conseil juridique.
Pour un avis juridique personnalisé, consultez un avocat qualifié."""
        )


# ==================== EXEMPLES D'UTILISATION ====================

async def example_simple_usage():
    """
    Exemple 1: Utilisation simple avec 2 agents
    """
    processor = AgentQueryProcessor(
        use_agents=True,
        agent_mode="simple"
    )

    query = QueryRequest(
        query="Quel est le délai de rétractation pour un achat en ligne ?",
        domain="consommation"
    )

    response = await processor.process_query(query, is_professional=False)
    print(response)


async def example_full_agents():
    """
    Exemple 2: Utilisation complète avec 4-5 agents
    Pour des questions complexes
    """
    processor = AgentQueryProcessor(
        use_agents=True,
        agent_mode="full"
    )

    query = QueryRequest(
        query="Quelles sont les conditions de licenciement pour inaptitude suite à un accident du travail ?",
        domain="travail",
        context="Employé avec 10 ans d'ancienneté dans une PME de 50 salariés"
    )

    response = await processor.process_query(query, is_professional=True)
    print(response)


async def example_hybrid_mode():
    """
    Exemple 3: Mode hybride
    Standard par défaut, agents sur demande
    """
    processor = AgentQueryProcessor(
        use_agents=False,  # Standard par défaut
        agent_mode="full"
    )

    # Requête simple: mode standard
    simple_query = QueryRequest(
        query="C'est quoi le Code civil ?",
        domain="général"
    )
    response1 = await processor.process_query(simple_query)

    # Requête complexe: forcer les agents
    complex_query = QueryRequest(
        query="Analyser les implications fiscales d'une donation-partage transgénérationnelle",
        domain="fiscal"
    )
    response2 = await processor.process_query(
        complex_query,
        is_professional=True,
        force_agents=True  # Force l'utilisation des agents
    )


async def example_direct_crew_usage():
    """
    Exemple 4: Utilisation directe des agents (sans QueryProcessor)
    Pour une intégration personnalisée
    """
    # Créer l'équipe
    crew = LegalResearchCrew(
        process_type="sequential",
        domain_specialization="fiscal"  # Expert fiscal en plus
    )

    # Recherche
    result = crew.research_legal_query(
        query="Quelles sont les conditions pour bénéficier du régime de la micro-entreprise ?",
        domain="fiscal",
        context={
            "activity": "Consultant indépendant",
            "estimated_revenue": "40000€"
        },
        is_professional=False
    )

    print(result)


# ==================== CONFIGURATION RECOMMANDÉE ====================

def get_recommended_processor(query_complexity: str = "simple") -> AgentQueryProcessor:
    """
    Factory pour obtenir le bon processeur selon la complexité

    Args:
        query_complexity: "simple", "medium", "complex"

    Returns:
        Processeur configuré
    """
    if query_complexity == "simple":
        # Questions simples: mode standard (OpenAI direct)
        return AgentQueryProcessor(use_agents=False)

    elif query_complexity == "medium":
        # Questions moyennes: 2 agents
        return AgentQueryProcessor(
            use_agents=True,
            agent_mode="simple"
        )

    else:  # complex
        # Questions complexes: 4-5 agents
        return AgentQueryProcessor(
            use_agents=True,
            agent_mode="full"
        )


if __name__ == "__main__":
    import asyncio

    # Tester les exemples
    print("=== Exemple 1: Simple ===")
    asyncio.run(example_simple_usage())

    print("\n=== Exemple 2: Full Agents ===")
    asyncio.run(example_full_agents())

    print("\n=== Exemple 3: Hybrid ===")
    asyncio.run(example_hybrid_mode())

    print("\n=== Exemple 4: Direct Crew ===")
    asyncio.run(example_direct_crew_usage())