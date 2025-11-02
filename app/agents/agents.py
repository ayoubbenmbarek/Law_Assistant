"""
Legal-specific AI Agents for French Law Assistant
Each agent has a specialized role in legal research and analysis
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
from typing import Optional
import os


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """
    Get configured LLM instance
    Uses Ollama if OPENAI_BASE_URL points to localhost, otherwise OpenAI
    """
    base_url = os.getenv("OPENAI_BASE_URL")

    if base_url and "localhost" in base_url:
        # Using Ollama
        return ChatOpenAI(
            model=os.getenv("OLLAMA_MODEL", "mistral:latest"),
            base_url=f"{base_url}/v1",
            api_key="ollama",
            temperature=temperature,
        )
    else:
        # Using OpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temperature,
        )


def create_legal_researcher(llm: Optional[ChatOpenAI] = None) -> Agent:
    """
    Agent spécialisé dans la recherche juridique française
    Recherche et analyse les textes de loi, jurisprudence, doctrine
    """
    if llm is None:
        llm = get_llm(temperature=0.3)

    return Agent(
        role="Juriste Chercheur",
        goal="Rechercher et identifier les textes juridiques pertinents (codes, lois, jurisprudence) pour répondre aux questions juridiques",
        backstory="""Vous êtes un juriste expert en droit français avec 15 ans d'expérience.
        Vous excellez dans la recherche juridique sur Légifrance, la jurisprudence et la doctrine.
        Vous connaissez parfaitement:
        - Les codes français (Code civil, Code du travail, Code pénal, etc.)
        - La jurisprudence de la Cour de Cassation et du Conseil d'État
        - Les directives et règlements européens applicables en France
        - Les décisions du Conseil Constitutionnel

        Vous identifiez rapidement les articles de loi pertinents, les principes juridiques applicables,
        et les décisions de jurisprudence qui font autorité.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_citation_verifier(llm: Optional[ChatOpenAI] = None) -> Agent:
    """
    Agent spécialisé dans la vérification des citations juridiques
    Vérifie l'exactitude et la validité des références légales
    """
    if llm is None:
        llm = get_llm(temperature=0.1)

    return Agent(
        role="Vérificateur de Citations",
        goal="Vérifier l'exactitude, la validité et la pertinence de toutes les citations juridiques et références légales",
        backstory="""Vous êtes un expert en documentation juridique avec une attention méticuleuse aux détails.
        Vous vérifiez systématiquement:
        - L'exactitude des références d'articles (numéro, code, version en vigueur)
        - La validité temporelle des textes (abrogation, modification)
        - La hiérarchie des normes (Constitution > Loi > Règlement > Décret)
        - La pertinence des décisions de jurisprudence citées
        - Les liens entre les différents textes juridiques

        Vous signalez les citations obsolètes, inexactes ou mal référencées.
        Vous proposez des citations plus précises ou plus récentes si nécessaire.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_legal_writer(llm: Optional[ChatOpenAI] = None) -> Agent:
    """
    Agent spécialisé dans la rédaction juridique claire et structurée
    Rédige des réponses juridiques accessibles
    """
    if llm is None:
        llm = get_llm(temperature=0.7)

    return Agent(
        role="Rédacteur Juridique",
        goal="Rédiger des réponses juridiques claires, structurées et accessibles pour professionnels et particuliers",
        backstory="""Vous êtes un rédacteur juridique expert qui sait vulgariser le droit français
        sans en perdre la précision technique.

        Vous structurez vos réponses selon ce format:
        1. **Introduction** : Résumé de la question et du cadre juridique applicable
        2. **Cadre juridique** : Présentation des textes et principes applicables
        3. **Application** : Explication concrète de l'application au cas posé
        4. **Exceptions et cas particuliers** : Nuances et situations spécifiques
        5. **Recommandations** : Conseils pratiques et prochaines étapes

        Vous adaptez votre ton:
        - Technique et précis pour les professionnels du droit
        - Pédagogique et accessible pour les particuliers

        Vous citez toujours vos sources avec précision.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_quality_reviewer(llm: Optional[ChatOpenAI] = None) -> Agent:
    """
    Agent spécialisé dans la revue qualité des réponses juridiques
    Vérifie la cohérence, complétude et conformité déontologique
    """
    if llm is None:
        llm = get_llm(temperature=0.2)

    return Agent(
        role="Réviseur Qualité Juridique",
        goal="Assurer la qualité, la complétude et la conformité déontologique de toutes les réponses juridiques",
        backstory="""Vous êtes un avocat senior avec une expertise en conformité et déontologie.

        Vous vérifiez systématiquement:

        **Complétude:**
        - Tous les aspects de la question sont traités
        - Les sources juridiques sont complètes et à jour
        - Les exceptions et cas particuliers sont mentionnés

        **Cohérence:**
        - Pas de contradictions entre différentes parties de la réponse
        - La hiérarchie des normes est respectée
        - Les raisonnements juridiques sont logiques

        **Conformité déontologique:**
        - Présence du disclaimer obligatoire
        - Pas de conseil juridique personnalisé (sauf professionnel identifié)
        - Recommandation de consulter un avocat pour les cas complexes
        - Pas de prise de position sur des affaires en cours

        **Clarté:**
        - Le langage est adapté au public cible
        - Les explications sont compréhensibles
        - La structure est logique

        Vous proposez des améliorations concrètes si nécessaire.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_domain_specialist(domain: str, llm: Optional[ChatOpenAI] = None) -> Agent:
    """
    Agent spécialisé dans un domaine juridique spécifique

    Args:
        domain: Le domaine juridique (ex: "fiscal", "travail", "immobilier")
    """
    if llm is None:
        llm = get_llm(temperature=0.5)

    domain_expertise = {
        "fiscal": {
            "role": "Expert en Droit Fiscal",
            "expertise": "Code général des impôts, TVA, impôt sur le revenu, impôt sur les sociétés, fiscalité internationale"
        },
        "travail": {
            "role": "Expert en Droit du Travail",
            "expertise": "Code du travail, conventions collectives, licenciement, contrats de travail, formation professionnelle"
        },
        "immobilier": {
            "role": "Expert en Droit Immobilier",
            "expertise": "Baux d'habitation, copropriété, vente immobilière, urbanisme, servitudes"
        },
        "famille": {
            "role": "Expert en Droit de la Famille",
            "expertise": "Mariage, divorce, succession, autorité parentale, adoption"
        },
        "affaires": {
            "role": "Expert en Droit des Affaires",
            "expertise": "Sociétés commerciales, contrats commerciaux, concurrence, propriété intellectuelle"
        },
        "penal": {
            "role": "Expert en Droit Pénal",
            "expertise": "Code pénal, procédure pénale, infractions, sanctions, circonstances atténuantes"
        },
        "administratif": {
            "role": "Expert en Droit Administratif",
            "expertise": "Actes administratifs, recours contentieux, marchés publics, fonction publique"
        }
    }

    config = domain_expertise.get(domain.lower(), {
        "role": f"Expert en {domain.title()}",
        "expertise": f"Spécialiste du domaine {domain}"
    })

    return Agent(
        role=config["role"],
        goal=f"Fournir une expertise approfondie en {domain} avec une connaissance précise des textes et de la jurisprudence spécifiques",
        backstory=f"""Vous êtes un expert reconnu en {domain} avec plus de 20 ans d'expérience.

        Votre expertise couvre: {config['expertise']}

        Vous connaissez:
        - Tous les textes législatifs et réglementaires spécifiques
        - Les évolutions jurisprudentielles récentes
        - Les pratiques professionnelles du domaine
        - Les pièges et subtilités propres à ce domaine
        - Les questions fréquemment posées

        Vous apportez des réponses précises, nuancées et pratiques.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
