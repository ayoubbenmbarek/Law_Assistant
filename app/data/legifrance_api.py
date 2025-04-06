import os
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger
from app.utils.vector_store import vector_store

# Load environment variables
load_dotenv()

# API configuration
LEGIFRANCE_API_KEY = os.getenv("PISTE_API_KEY", "3ae7cb04-6b64-42b7-abd7-cd3f10f2e72c")
LEGIFRANCE_API_SECRET = os.getenv("PISTE_SECRET_KEY", "b0361bfa-a858-4635-bc11-d351f91345ab")
LEGIFRANCE_API_BASE_URL = "https://api.aife.economie.gouv.fr/dila/legifrance/lf-engine-app"

class LegifranceAPI:
    """Client pour l'API Légifrance PISTE/DILA"""
    
    def __init__(self):
        self.api_key = LEGIFRANCE_API_KEY
        self.api_secret = LEGIFRANCE_API_SECRET
        self.base_url = LEGIFRANCE_API_BASE_URL
        self.token = None
        self.token_expiry = None
        
        if not self.api_key or not self.api_secret:
            logger.warning("Clés d'API Légifrance non configurées. Utilisation de données de test uniquement.")
        
    async def authenticate(self):
        """Authentification à l'API Légifrance pour obtenir un token"""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        try:
            auth_url = "https://oauth.aife.economie.gouv.fr/api/oauth/token"
            auth_data = {
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "grant_type": "client_credentials",
                "scope": "openid"
            }
            
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.token = auth_result.get("access_token")
            
            # Token expires in (default 30min)
            expires_in = auth_result.get("expires_in", 1800)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Authentification Légifrance réussie")
            return self.token
            
        except Exception as e:
            logger.error(f"Échec d'authentification à l'API Légifrance: {str(e)}")
            raise
    
    async def search_codes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche dans les codes (Code Civil, Code du Travail, etc.)"""
        try:
            await self.authenticate()
            
            endpoint = f"{self.base_url}/consult/code"
            
            payload = {
                "recherche": {
                    "champ": query,
                    "pageNumber": 1,
                    "pageSize": limit
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            results = response.json()
            
            # Transformation des résultats
            formatted_results = []
            for item in results.get("results", []):
                formatted_results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "type": "loi",
                    "content": item.get("text", ""),
                    "date": item.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "url": item.get("url", ""),
                    "metadata": {
                        "code": item.get("code", {}).get("title", ""),
                        "section": item.get("context", "")
                    }
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Échec de recherche dans les codes: {str(e)}")
            if not self.api_key or not self.api_secret:
                return self._get_mock_code_results(query, limit)
            raise
    
    async def search_jurisprudence(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche dans la jurisprudence (Cour de cassation, Conseil d'État, etc.)"""
        try:
            await self.authenticate()
            
            endpoint = f"{self.base_url}/consult/juri"
            
            payload = {
                "recherche": {
                    "champ": query,
                    "pageNumber": 1,
                    "pageSize": limit,
                    "sort": "date desc"
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            results = response.json()
            
            # Transformation des résultats
            formatted_results = []
            for item in results.get("results", []):
                formatted_results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "type": "jurisprudence",
                    "content": item.get("text", ""),
                    "date": item.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "url": item.get("url", ""),
                    "metadata": {
                        "juridiction": item.get("formation", ""),
                        "solution": item.get("solution", "")
                    }
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Échec de recherche dans la jurisprudence: {str(e)}")
            if not self.api_key or not self.api_secret:
                return self._get_mock_jurisprudence_results(query, limit)
            raise
    
    def _get_mock_code_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Données de test pour les codes (à utiliser quand l'API n'est pas configurée)"""
        logger.info("Utilisation de données de test pour les codes")
        
        mock_results = [
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
                }
            },
            {
                "id": "LEGIARTI000037730625",
                "title": "Article L1231-1 du Code du travail",
                "type": "loi",
                "content": "Le contrat de travail à durée indéterminée peut être rompu à l'initiative de l'employeur ou du salarié, ou d'un commun accord, dans les conditions prévues par les dispositions du présent titre.",
                "date": "2023-01-01",
                "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037730625",
                "metadata": {
                    "code": "Code du travail",
                    "section": "Rupture du contrat de travail à durée indéterminée"
                }
            }
        ]
        
        return mock_results[:limit]
    
    def _get_mock_jurisprudence_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Données de test pour la jurisprudence (à utiliser quand l'API n'est pas configurée)"""
        logger.info("Utilisation de données de test pour la jurisprudence")
        
        mock_results = [
            {
                "id": "JURITEXT000045932183",
                "title": "Cour de Cassation, civile, Chambre sociale, 25 mai 2022, 20-23.428",
                "type": "jurisprudence",
                "content": "Attendu que pour fixer la créance du salarié au titre d'un rappel de salaire pour la période du 1er décembre 2015 au 30 mai 2016, l'arrêt retient qu'il n'est pas contesté que le salarié a perçu la somme brute de 9 274,32 euros pour cette période alors qu'il aurait dû percevoir la somme de 11 400 euros...",
                "date": "2022-05-25",
                "url": "https://www.legifrance.gouv.fr/juri/id/JURITEXT000045932183",
                "metadata": {
                    "juridiction": "Cour de Cassation",
                    "chambre": "Chambre sociale"
                }
            },
            {
                "id": "CETATEXT000044615886",
                "title": "Conseil d'État, 5ème chambre, 22/12/2021, 453080",
                "type": "jurisprudence",
                "content": "Vu la procédure suivante : Par une requête sommaire et un mémoire complémentaire, enregistrés les 28 mai et 30 août 2021 au secrétariat du contentieux du Conseil d'Etat, la société Getaround demande au Conseil d'Etat...",
                "date": "2021-12-22",
                "url": "https://www.legifrance.gouv.fr/ceta/id/CETATEXT000044615886",
                "metadata": {
                    "juridiction": "Conseil d'État",
                    "chambre": "5ème chambre"
                }
            }
        ]
        
        return mock_results[:limit]
        
    async def import_to_vector_store(self, sources: List[Dict[str, Any]]):
        """Importe des sources juridiques dans la base vectorielle"""
        try:
            for source in sources:
                vector_store.add_document(
                    doc_id=source["id"],
                    title=source["title"],
                    content=source["content"],
                    doc_type=source["type"],
                    date=source["date"],
                    url=source["url"],
                    metadata=source["metadata"]
                )
                
            logger.info(f"Importation de {len(sources)} sources dans la base vectorielle")
        except Exception as e:
            logger.error(f"Échec d'importation dans la base vectorielle: {str(e)}")
            raise

    async def import_codes(self, limit: int = 20, search_terms: List[str] = None):
        """
        Importe des articles de codes juridiques dans la base vectorielle
        
        Args:
            limit: Nombre maximum d'articles à importer par terme de recherche
            search_terms: Liste de termes de recherche pour trouver des articles pertinents
        """
        if search_terms is None:
            search_terms = [
                "droit", "obligation", "contrat", "travail", "vente", 
                "penal", "impot", "famille", "société", "commerce",
                "environnement", "propriété", "construction", "consommation"
            ]
        
        imported_count = 0
        
        logger.info(f"Début de l'importation des codes avec {len(search_terms)} termes de recherche")
        
        for term in search_terms:
            try:
                logger.info(f"Recherche dans les codes avec le terme: {term}")
                results = await self.search_codes(term, limit)
                
                if results:
                    await self.import_to_vector_store(results)
                    imported_count += len(results)
                    logger.info(f"Importé {len(results)} articles de code pour le terme '{term}'")
                else:
                    logger.warning(f"Aucun résultat trouvé pour le terme '{term}'")
            
            except Exception as e:
                logger.error(f"Erreur lors de l'importation des codes pour le terme '{term}': {str(e)}")
        
        logger.info(f"Importation des codes terminée. Total: {imported_count} articles importés")
        return {"imported_count": imported_count}

    async def import_jurisprudence(self, limit: int = 20, search_terms: List[str] = None):
        """
        Importe des décisions de jurisprudence dans la base vectorielle
        
        Args:
            limit: Nombre maximum de décisions à importer par terme de recherche
            search_terms: Liste de termes de recherche pour trouver des décisions pertinentes
        """
        if search_terms is None:
            search_terms = [
                "licenciement", "faute grave", "contrat de travail", "rupture conventionnelle",
                "divorce", "garde enfant", "succession", "bail", "loyer",
                "consommation", "vice caché", "garantie", "responsabilité", "préjudice",
                "dommages et intérêts", "assurance", "fraude", "impôt"
            ]
        
        imported_count = 0
        
        logger.info(f"Début de l'importation de jurisprudence avec {len(search_terms)} termes de recherche")
        
        for term in search_terms:
            try:
                logger.info(f"Recherche dans la jurisprudence avec le terme: {term}")
                results = await self.search_jurisprudence(term, limit)
                
                if results:
                    await self.import_to_vector_store(results)
                    imported_count += len(results)
                    logger.info(f"Importé {len(results)} décisions pour le terme '{term}'")
                else:
                    logger.warning(f"Aucun résultat trouvé pour le terme '{term}'")
            
            except Exception as e:
                logger.error(f"Erreur lors de l'importation de jurisprudence pour le terme '{term}': {str(e)}")
        
        logger.info(f"Importation de jurisprudence terminée. Total: {imported_count} décisions importées")
        return {"imported_count": imported_count}

# Créer l'instance du client API
legifrance_api = LegifranceAPI() 