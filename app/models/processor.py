import os
import json
import openai
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
from app.data.legifrance_api import legifrance_api
from app.utils.vector_store import vector_store
from app.models.query import QueryRequest
from app.models.response import LegalResponse

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class QueryProcessor:
    """
    Processeur de requêtes juridiques
    
    Cette classe orchestre le traitement des requêtes juridiques:
    1. Analyse la question pour déterminer le domaine et les concepts juridiques clés
    2. Recherche des sources juridiques pertinentes
    3. Génère une réponse structurée
    """
    
    async def process_query(self, request: QueryRequest, is_professional: bool = False) -> LegalResponse:
        """
        Traite une requête juridique et génère une réponse
        
        Args:
            request: La requête utilisateur
            is_professional: Si l'utilisateur est un professionnel du droit
            
        Returns:
            Une réponse juridique structurée
        """
        try:
            # 1. Analyser la question pour déterminer les concepts juridiques clés
            analysis = await self._analyze_query(request.query, request.domain)
            
            # 2. Rechercher des sources juridiques pertinentes
            sources = await self._get_relevant_sources(
                query=request.query,
                domain=request.domain or analysis.get("domain"),
                concepts=analysis.get("key_concepts", [])
            )
            
            # 3. Générer une réponse
            response = await self._generate_response(
                request=request,
                sources=sources,
                analysis=analysis,
                is_professional=is_professional
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête: {str(e)}")
            # Retourner une réponse d'erreur plutôt que de planter
            return LegalResponse(
                introduction=f"Nous avons rencontré une difficulté lors du traitement de votre question.",
                legal_framework="Nous ne pouvons pas fournir le cadre légal pour le moment.",
                application="Veuillez nous excuser pour ce désagrément.",
                exceptions=None,
                recommendations=["Réessayez ultérieurement", "Contactez notre support si le problème persiste"],
                sources=["Aucune source disponible"],
                date_updated=datetime.now().strftime("%Y-%m-%d"),
                disclaimer="Cette réponse est fournie à titre informatif uniquement. Consultez un professionnel du droit pour un avis personnalisé."
            )
    
    async def _analyze_query(self, query: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyse la question pour identifier le domaine juridique et les concepts clés
        
        Args:
            query: La question posée
            domain: Le domaine juridique spécifié (optionnel)
            
        Returns:
            Dictionnaire avec le domaine détecté et les concepts clés
        """
        try:
            # Si l'API OpenAI est configurée, utiliser GPT pour l'analyse
            if openai.api_key:
                system_prompt = """
                Tu es un assistant juridique spécialisé en droit français. Analyse la question juridique.
                Identifie le domaine juridique principal et les concepts juridiques clés dans la question.
                Réponds uniquement au format JSON avec les champs suivants:
                {
                    "domain": "domaine juridique identifié (fiscal, travail, affaires, famille, immobilier, consommation, penal, autre)",
                    "key_concepts": ["liste", "des", "concepts", "juridiques", "clés"],
                    "possible_laws": ["liste", "des", "lois", "pertinentes"],
                    "query_rephrased": "question reformulée de manière juridique précise"
                }
                """
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
                
                # Si un domaine est déjà spécifié, l'inclure dans l'analyse
                if domain:
                    messages.append({
                        "role": "user", 
                        "content": f"Le domaine spécifié par l'utilisateur est: {domain}"
                    })
                
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500
                )
                
                analysis = json.loads(response.choices[0].message.content)
                
                # Si un domaine était spécifié, le conserver
                if domain:
                    analysis["domain"] = domain
                    
                return analysis
                
            # Sinon, faire une analyse basique
            else:
                logger.warning("Clé API OpenAI non configurée. Utilisation d'une analyse basique.")
                
                # Analyse basique avec mots-clés
                domains = {
                    "fiscal": ["impôt", "taxe", "fiscal", "imposition", "revenu", "TVA"],
                    "travail": ["emploi", "salarié", "employeur", "contrat de travail", "licenciement", "embauche"],
                    "affaires": ["entreprise", "société", "commercial", "contrat", "concurrence"],
                    "famille": ["mariage", "divorce", "pension", "filiation", "succession", "héritage"],
                    "immobilier": ["bail", "propriété", "copropriété", "location", "loyer", "immeuble"],
                    "consommation": ["consommateur", "garantie", "défaut", "remboursement", "achat"],
                    "penal": ["infraction", "délit", "crime", "peine", "amende", "prison"]
                }
                
                # Détecter le domaine basé sur les mots-clés
                detected_domain = domain or "autre"
                max_matches = 0
                
                for dom, keywords in domains.items():
                    matches = sum(1 for kw in keywords if kw.lower() in query.lower())
                    if matches > max_matches:
                        max_matches = matches
                        detected_domain = dom
                
                # Extraire des mots-clés simples
                keywords = [word for word in query.split() if len(word) > 4]
                
                return {
                    "domain": detected_domain,
                    "key_concepts": keywords[:5],
                    "possible_laws": [],
                    "query_rephrased": query
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la question: {str(e)}")
            # Valeur par défaut en cas d'erreur
            return {
                "domain": domain or "autre",
                "key_concepts": [],
                "possible_laws": [],
                "query_rephrased": query
            }
    
    async def _get_relevant_sources(self, query: str, domain: Optional[str] = None, 
                                  concepts: List[str] = None) -> List[Dict[str, Any]]:
        """
        Recherche des sources juridiques pertinentes pour la question
        
        Args:
            query: La question posée
            domain: Le domaine juridique
            concepts: Les concepts juridiques clés
            
        Returns:
            Liste des sources juridiques pertinentes
        """
        try:
            # Recherche dans la base vectorielle
            vector_results = vector_store.search(query=query, limit=5, doc_type=None)
            
            # Si aucun résultat ou peu de résultats de la base vectorielle, chercher via l'API
            if len(vector_results) < 3:
                # Recherche dans les codes
                code_results = await legifrance_api.search_codes(query, limit=3)
                
                # Recherche dans la jurisprudence
                jurisprudence_results = await legifrance_api.search_jurisprudence(query, limit=2)
                
                # Combiner les résultats
                api_results = code_results + jurisprudence_results
                
                # Importer dans la base vectorielle pour les futures requêtes
                await legifrance_api.import_to_vector_store(api_results)
                
                # Combiner avec les résultats existants s'il y en a
                combined_results = vector_results + api_results
                
                # Dédupliquer par ID
                unique_results = {}
                for result in combined_results:
                    unique_results[result["id"]] = result
                
                return list(unique_results.values())
            
            return vector_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de sources: {str(e)}")
            # En cas d'erreur, renvoyer les données de test
            mock_sources = [
                {
                    "id": "LEGIARTI000006436298",
                    "title": "Article 1134 du Code Civil",
                    "type": "loi",
                    "content": "Les conventions légalement formées tiennent lieu de loi à ceux qui les ont faites.",
                    "date": "2023-01-01",
                    "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006436298",
                    "metadata": {
                        "code": "Code Civil",
                        "section": "Des contrats"
                    },
                    "score": 0.95
                }
            ]
            return mock_sources
    
    async def _generate_response(self, request: QueryRequest, sources: List[Dict[str, Any]], 
                               analysis: Dict[str, Any], is_professional: bool) -> LegalResponse:
        """
        Génère une réponse structurée à partir des sources et de l'analyse
        
        Args:
            request: La requête d'origine
            sources: Les sources juridiques pertinentes
            analysis: L'analyse de la question
            is_professional: Si l'utilisateur est un professionnel du droit
            
        Returns:
            Une réponse juridique structurée
        """
        try:
            # Si l'API OpenAI est configurée, utiliser GPT pour générer la réponse
            if openai.api_key:
                # Formater les sources pour le prompt
                sources_text = "\n\n".join([
                    f"SOURCE {i+1}:\nTitre: {s['title']}\nType: {s['type']}\nContenu: {s['content']}\nURL: {s.get('url', 'N/A')}"
                    for i, s in enumerate(sources)
                ])
                
                # Déterminer le niveau de technicité en fonction du profil
                technical_level = "technique avec terminologie juridique précise" if is_professional else "accessible avec explications des termes juridiques"
                
                system_prompt = f"""
                Tu es un assistant juridique spécialisé en droit français. Ton objectif est de fournir une réponse juridique structurée et précise.

                QUESTION DE L'UTILISATEUR:
                {request.query}

                CONTEXTE SUPPLÉMENTAIRE FOURNI:
                {request.context or "Aucun contexte supplémentaire fourni."}

                DOMAINE JURIDIQUE:
                {analysis.get("domain", "Non spécifié")}

                SOURCES JURIDIQUES PERTINENTES:
                {sources_text}

                INSTRUCTIONS:
                - Fournis une réponse {technical_level}
                - Cite précisément les articles de loi et la jurisprudence
                - Structure ta réponse selon les sections demandées
                - L'information doit être à jour au {datetime.now().strftime("%d/%m/%Y")}
                - Sois objectif et factuel, sans donner d'opinion personnelle

                Réponds uniquement au format JSON avec les champs suivants:
                {{
                    "introduction": "Introduction et résumé de la question juridique",
                    "legal_framework": "Cadre légal, lois et règlements applicables, avec citations précises",
                    "application": "Application de la loi au cas spécifique décrit par l'utilisateur",
                    "exceptions": "Exceptions et cas particuliers applicables à cette situation",
                    "recommendations": ["Liste", "des", "recommandations", "et", "prochaines", "étapes"],
                    "sources": ["Liste", "des", "références", "précises"]
                }}
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "system", "content": system_prompt}],
                    temperature=0.2,
                    max_tokens=1500
                )
                
                content = json.loads(response.choices[0].message.content)
                
                # Compléter avec les champs manquants si nécessaire
                if "disclaimer" not in content:
                    content["disclaimer"] = "Cette réponse est fournie à titre informatif uniquement et ne constitue pas un avis juridique. Consultez un professionnel pour une analyse personnalisée."
                
                if "date_updated" not in content:
                    content["date_updated"] = datetime.now().strftime("%Y-%m-%d")
                
                return LegalResponse(**content)
                
            # Sinon, créer une réponse basique
            else:
                logger.warning("Clé API OpenAI non configurée. Génération d'une réponse basique.")
                
                # Format simple en utilisant les sources directement
                sources_content = [s.get("content", "") for s in sources if isinstance(s, dict)]
                
                # Assurez-vous que sources_titles est toujours une liste de chaînes
                sources_titles = []
                for s in sources:
                    if isinstance(s, dict):
                        title = s.get("title", "")
                        if title:
                            sources_titles.append(title)
                    elif isinstance(s, str):
                        sources_titles.append(s)
                
                # Si pas de sources, ajouter une source par défaut
                if not sources_titles:
                    sources_titles = ["Aucune source spécifique n'a été trouvée"]
                
                response = LegalResponse(
                    introduction=f"Votre question concerne le domaine du droit {analysis.get('domain', 'non spécifié')}.",
                    legal_framework=f"Selon les sources juridiques disponibles: {'. '.join(sources_content[:2]) if sources_content else 'Aucune information spécifique disponible.'}",
                    application="L'application à votre cas spécifique nécessite une analyse détaillée par un professionnel.",
                    exceptions="Des exceptions peuvent s'appliquer selon les circonstances particulières.",
                    recommendations=[
                        "Consultez un avocat spécialisé en droit " + analysis.get('domain', 'applicable'),
                        "Conservez tous les documents pertinents",
                        "Vérifiez les délais applicables à votre situation"
                    ],
                    sources=sources_titles,
                    date_updated=datetime.now().strftime("%Y-%m-%d"),
                    disclaimer="Cette réponse est générée automatiquement et fournie à titre indicatif uniquement. Consultez un professionnel du droit pour un avis personnalisé."
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")
            # Réponse par défaut en cas d'erreur
            return LegalResponse(
                introduction="Nous avons analysé votre question juridique.",
                legal_framework="Les dispositions légales applicables n'ont pas pu être déterminées avec précision.",
                application="Pour une application spécifique à votre cas, veuillez consulter un professionnel.",
                exceptions=None,
                recommendations=[
                    "Consultez un professionnel du droit pour une analyse complète",
                    "Précisez davantage votre situation pour obtenir une réponse plus précise"
                ],
                sources=["Sources non disponibles"],
                date_updated=datetime.now().strftime("%Y-%m-%d"),
                disclaimer="Cette réponse est fournie à titre informatif uniquement et ne constitue pas un avis juridique."
            )

# Instance singleton du processeur de requêtes
query_processor = QueryProcessor() 