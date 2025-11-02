"""
Legal Research Crew - Orchestrates multiple legal agents
Integrates with existing QueryProcessor for enhanced legal analysis
"""

from crewai import Task, Crew, Process
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from .agents import (
    create_legal_researcher,
    create_citation_verifier,
    create_legal_writer,
    create_quality_reviewer,
    create_domain_specialist
)


class LegalResearchCrew:
    """
    Coordonne une équipe d'agents IA pour traiter les requêtes juridiques

    Architecture:
    1. Legal Researcher: Recherche les textes et jurisprudence pertinents
    2. Citation Verifier: Vérifie l'exactitude des références
    3. Legal Writer: Rédige une réponse structurée
    4. Quality Reviewer: Contrôle qualité final
    """

    def __init__(
        self,
        process_type: str = "sequential",
        verbose: bool = True,
        domain_specialization: Optional[str] = None
    ):
        """
        Initialise l'équipe d'agents juridiques

        Args:
            process_type: "sequential" ou "hierarchical"
            verbose: Mode verbeux pour le debug
            domain_specialization: Domaine juridique spécifique (optionnel)
        """
        self.process_type = process_type
        self.verbose = verbose
        self.domain_specialization = domain_specialization

        # Créer les agents
        self.legal_researcher = create_legal_researcher()
        self.citation_verifier = create_citation_verifier()
        self.legal_writer = create_legal_writer()
        self.quality_reviewer = create_quality_reviewer()

        # Ajouter un expert de domaine si spécifié
        self.domain_specialist = None
        if domain_specialization:
            self.domain_specialist = create_domain_specialist(domain_specialization)

        logger.info(f"LegalResearchCrew initialized with {process_type} process")

    def research_legal_query(
        self,
        query: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        is_professional: bool = False
    ) -> Dict[str, Any]:
        """
        Traite une requête juridique avec l'équipe d'agents

        Args:
            query: La question juridique
            domain: Domaine juridique (fiscal, travail, etc.)
            context: Contexte additionnel (sources existantes, etc.)
            is_professional: Si l'utilisateur est un professionnel

        Returns:
            Résultat structuré de l'analyse
        """
        try:
            # Préparer le contexte
            full_context = {
                "query": query,
                "domain": domain or "général",
                "is_professional": is_professional,
                "timestamp": datetime.now().isoformat(),
                **(context or {})
            }

            # Créer les tâches
            tasks = self._create_tasks(full_context)

            # Créer l'équipe
            agents = [
                self.legal_researcher,
                self.citation_verifier,
                self.legal_writer,
                self.quality_reviewer
            ]

            # Ajouter l'expert de domaine si disponible
            if self.domain_specialist:
                agents.insert(1, self.domain_specialist)

            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=self.verbose,
                process=Process.sequential if self.process_type == "sequential" else Process.hierarchical
            )

            # Exécuter
            logger.info(f"Starting legal research crew for query: {query[:100]}")
            result = crew.kickoff(inputs=full_context)

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in legal research crew: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _create_tasks(self, context: Dict[str, Any]) -> List[Task]:
        """
        Crée les tâches pour l'équipe d'agents

        Args:
            context: Contexte de la requête

        Returns:
            Liste des tâches à exécuter
        """
        is_professional = context.get("is_professional", False)
        domain = context.get("domain", "général")

        tasks = []

        # Tâche 1: Recherche juridique
        research_task = Task(
            description=f"""Analyser la question juridique suivante et identifier tous les textes juridiques pertinents:

Question: {context['query']}
Domaine: {domain}

Vous devez:
1. Identifier les articles de loi applicables (codes, lois, règlements)
2. Trouver la jurisprudence pertinente (Cour de Cassation, Conseil d'État)
3. Identifier les principes juridiques généraux applicables
4. Noter les textes européens pertinents le cas échéant
5. Signaler les évolutions législatives récentes

Fournir une liste structurée des sources avec:
- Référence exacte (ex: Article 1134 du Code civil)
- Contenu pertinent
- Pertinence par rapport à la question""",
            expected_output="""Liste structurée des sources juridiques:
- Articles de loi avec références exactes
- Jurisprudence pertinente avec numéros de décision
- Principes juridiques applicables
- Textes européens si applicable""",
            agent=self.legal_researcher,
        )
        tasks.append(research_task)

        # Tâche 2: Expert de domaine (si applicable)
        if self.domain_specialist:
            domain_task = Task(
                description=f"""En tant qu'expert en {domain}, analyser la question et les sources identifiées.

Apporter votre expertise spécifique sur:
1. Les subtilités propres à ce domaine
2. Les pièges à éviter
3. Les évolutions jurisprudentielles récentes dans ce domaine
4. Les pratiques professionnelles courantes
5. Les cas particuliers et exceptions

Question: {context['query']}

Enrichir l'analyse avec votre expertise de domaine.""",
                expected_output="""Analyse experte du domaine avec:
- Points d'attention spécifiques
- Jurisprudence de référence du domaine
- Recommandations pratiques
- Cas particuliers à considérer""",
                agent=self.domain_specialist,
            )
            tasks.append(domain_task)

        # Tâche 3: Vérification des citations
        verification_task = Task(
            description="""Vérifier rigoureusement toutes les références juridiques identifiées:

1. Exactitude des références d'articles
2. Validité temporelle (texte en vigueur? abrogé? modifié?)
3. Hiérarchie des normes respectée
4. Pertinence des décisions de jurisprudence
5. Cohérence entre les différentes sources

Signaler:
- Toute erreur de référence
- Les textes obsolètes
- Les sources manquantes importantes
- Les contradictions éventuelles

Proposer des corrections si nécessaire.""",
            expected_output="""Rapport de vérification avec:
- Validation de chaque référence
- Signalement des erreurs ou incohérences
- Propositions de corrections
- Confirmation de la validité temporelle""",
            agent=self.citation_verifier,
        )
        tasks.append(verification_task)

        # Tâche 4: Rédaction
        writing_task = Task(
            description=f"""Rédiger une réponse juridique complète, claire et structurée.

Question: {context['query']}
Public: {"Professionnel du droit" if is_professional else "Grand public"}

Structurer la réponse ainsi:

1. **Introduction**
   - Reformulation de la question
   - Enjeux juridiques identifiés
   - Cadre juridique applicable (1 paragraphe)

2. **Cadre juridique**
   - Présentation des textes applicables
   - Principes juridiques pertinents
   - Jurisprudence de référence

3. **Application**
   - Explication concrète de l'application au cas posé
   - Raisonnement juridique détaillé
   - Conséquences pratiques

4. **Exceptions et cas particuliers**
   - Nuances importantes
   - Situations spécifiques
   - Conditions d'application

5. **Recommandations**
   - Conseils pratiques
   - Démarches à entreprendre
   - Points de vigilance

Adapter le ton: {"technique et précis" if is_professional else "pédagogique et accessible"}
Citer systématiquement les sources vérifiées.""",
            expected_output="""Réponse juridique complète et structurée avec:
- Introduction claire
- Cadre juridique détaillé avec citations
- Application pratique au cas posé
- Exceptions et cas particuliers
- Recommandations concrètes
- Sources citées avec précision""",
            agent=self.legal_writer,
        )
        tasks.append(writing_task)

        # Tâche 5: Revue qualité
        quality_task = Task(
            description="""Effectuer un contrôle qualité complet de la réponse juridique.

Vérifier:

**Complétude:**
- Tous les aspects de la question sont traités
- Les sources sont complètes et à jour
- Les exceptions importantes sont mentionnées

**Cohérence:**
- Pas de contradictions internes
- Hiérarchie des normes respectée
- Raisonnement juridique logique

**Conformité déontologique:**
- Disclaimer présent et approprié
- Pas de conseil personnalisé inapproprié
- Recommandation de consulter un avocat si nécessaire
- Neutralité sur les affaires en cours

**Clarté:**
- Langage adapté au public
- Structure logique
- Explications compréhensibles

Fournir:
1. Validation globale (OK / À améliorer)
2. Points forts de la réponse
3. Points à améliorer (le cas échéant)
4. Ajout du disclaimer final si manquant""",
            expected_output="""Rapport de qualité avec:
- Validation globale
- Points forts identifiés
- Recommandations d'amélioration
- Version finale approuvée avec disclaimer""",
            agent=self.quality_reviewer,
        )
        tasks.append(quality_task)

        return tasks


class SimpleLegalCrew:
    """
    Version simplifiée avec 2 agents pour des cas simples
    Plus rapide mais moins approfondie
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.researcher = create_legal_researcher()
        self.writer = create_legal_writer()
        logger.info("SimpleLegalCrew initialized")

    def quick_research(
        self,
        query: str,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recherche rapide pour des questions simples

        Args:
            query: La question juridique
            domain: Domaine juridique

        Returns:
            Résultat de l'analyse rapide
        """
        try:
            # Tâche de recherche
            research_task = Task(
                description=f"Rechercher les textes juridiques pertinents pour: {query}",
                expected_output="Liste des sources juridiques avec références",
                agent=self.researcher,
            )

            # Tâche de rédaction
            writing_task = Task(
                description=f"Rédiger une réponse claire et concise basée sur les sources identifiées",
                expected_output="Réponse juridique structurée",
                agent=self.writer,
            )

            crew = Crew(
                agents=[self.researcher, self.writer],
                tasks=[research_task, writing_task],
                verbose=self.verbose,
                process=Process.sequential
            )

            result = crew.kickoff(inputs={"query": query, "domain": domain or "général"})

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in simple legal crew: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }