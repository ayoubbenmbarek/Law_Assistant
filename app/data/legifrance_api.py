import os
import requests
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger
from app.utils.vector_store import vector_store

# Load environment variables
load_dotenv()

# API configuration
LEGIFRANCE_API_KEY = os.getenv("PISTE_API_KEY", "")
LEGIFRANCE_API_SECRET = os.getenv("PISTE_SECRET_KEY", "")
LEGIFRANCE_API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
LEGIFRANCE_API_SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
LEGIFRANCE_AUTH_URL = "https://oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_SANDBOX_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

class LegifranceAPI:
    """Client pour l'API Légifrance PISTE/DILA organisé selon la documentation Swagger"""
    
    def __init__(self, use_sandbox: bool = True):
        """
        Initialise le client API Légifrance
        
        Args:
            use_sandbox: Utiliser l'environnement sandbox (par défaut) ou production
        """
        self.api_key = LEGIFRANCE_API_KEY
        self.api_secret = LEGIFRANCE_API_SECRET
        self.token = ""
        self.base_url = LEGIFRANCE_API_SANDBOX_URL if use_sandbox else LEGIFRANCE_API_BASE_URL
        self.auth_url = LEGIFRANCE_SANDBOX_AUTH_URL if use_sandbox else LEGIFRANCE_AUTH_URL
        self.token_expiry = None
        self.use_sandbox = use_sandbox
        
        if not (self.api_key and self.api_secret):
            logger.warning("Clés d'API Légifrance non configurées. Utilisation de données de test uniquement.")
        
    async def authenticate(self):
        """Authentification à l'API Légifrance pour obtenir un token"""
        # Si nous avons un token valide, nous l'utilisons directement
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        try:
            auth_data = {
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "grant_type": "client_credentials",
                "scope": "openid"
            }
            
            response = requests.post(self.auth_url, data=auth_data)
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

    async def _make_api_request(self, endpoint: str, method: str = "POST", payload: Dict = None) -> Any:
        """
        Méthode interne pour effectuer des requêtes API avec gestion d'authentification
        
        Args:
            endpoint: Endpoint API à appeler
            method: Méthode HTTP (GET, POST)
            payload: Données JSON pour la requête
            
        Returns:
            Réponse JSON de l'API
        """
        await self.authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        full_url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(full_url, headers=headers, params=payload)
            else:
                response = requests.post(full_url, headers=headers, json=payload)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP {e.response.status_code} pour {endpoint}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à {endpoint}: {str(e)}")
            raise

    # ===== CONSULT CONTROLLER =====
    
    async def get_tables(self, start_year: int = None, end_year: int = None) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Récupère l'ensemble des tables annuelles pour une période donnée
        
        Args:
            start_year: Année de début (optionnel)
            end_year: Année de fin (optionnel)
            
        Returns:
            Résultat de l'API (liste des tables ou dictionnaire contenant les tables)
        """
        # Format exact comme montré dans l'interface Swagger
        payload = {}
        if start_year is not None:
            payload["startYear"] = start_year
        if end_year is not None:
            payload["endYear"] = end_year
            
        try:
            # On renvoie directement la réponse sans la traiter
            # Le traitement sera fait dans le script import_legifrance_tables.py
            response = await self._make_api_request("consult/getTables", "POST", payload)
            logger.info(f"Récupération des tables réussie, format de réponse: {type(response)}")
            return response
        except Exception as e:
            logger.error(f"Échec de récupération des tables: {str(e)}")
            return []
    
    async def get_cnil_with_ancien_id(self, ancien_id: str) -> Dict[str, Any]:
        """
        Récupère un texte du fond CNIL en fonction de son Ancien ID
        
        Args:
            ancien_id: Ancien identifiant de la délibération CNIL
            
        Returns:
            Dictionnaire contenant les détails de la délibération
        """
        payload = {
            "ancienId": ancien_id
        }
        
        try:
            return await self._make_api_request("consult/getCnilWithAncienId", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération de la délibération CNIL {ancien_id}: {str(e)}")
            if not self.token:
                return self._get_mock_cnil_result(ancien_id)
            raise
    
    async def get_article_with_id_eli_or_alias(self, id_eli: str = None, id_alias: str = None) -> Dict[str, Any]:
        """
        Récupère un article par son identifiant Eli ou Alias
        
        Args:
            id_eli: Identifiant ELI de l'article (optionnel)
            id_alias: Identifiant alias de l'article (optionnel)
            
        Returns:
            Détails de l'article
        """
        if not id_eli and not id_alias:
            raise ValueError("Au moins un des identifiants (ELI ou Alias) doit être fourni")
            
        payload = {}
        if id_eli:
            payload["idEli"] = id_eli
        if id_alias:
            payload["idAlias"] = id_alias
            
        try:
            return await self._make_api_request("consult/getArticleWithIdEliOrAlias", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération de l'article: {str(e)}")
            raise
    
    async def get_kali_article(self, article_id: str) -> Dict[str, Any]:
        """
        Récupère le contenu d'un texte du fonds des conventions collectives (KALI) 
        à partir de l'identifiant de son article
        
        Args:
            article_id: Identifiant technique de l'article
            
        Returns:
            Contenu du texte KALI
        """
        payload = {
            "id": article_id
        }
        
        try:
            return await self._make_api_request("consult/kaliArticle", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération de l'article KALI {article_id}: {str(e)}")
            raise
    
    async def get_same_num_article(self, text_id: str, article_id: str, 
                                  article_num: str, ref_date: str) -> Dict[str, Any]:
        """
        Récupère les liens des articles ayant eu le même numéro dans des versions précédentes
        
        Args:
            text_id: Identifiant commun du texte
            article_id: Identifiant commun de l'article
            article_num: Numéro de l'article
            ref_date: Date de référence au format YYYYMMDD
            
        Returns:
            Liens vers les articles de même numéro
        """
        payload = {
            "textId": text_id,
            "articleId": article_id,
            "articleNum": article_num,
            "date": ref_date
        }
        
        try:
            return await self._make_api_request("consult/sameNumArticle", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des articles de même numéro: {str(e)}")
            raise
    
    async def get_concordance_links_article(self, article_id: str) -> Dict[str, Any]:
        """
        Récupère les liens de concordance d'un article
        
        Args:
            article_id: Identifiant technique de l'article
            
        Returns:
            Liens de concordance
        """
        payload = {
            "id": article_id
        }
        
        try:
            return await self._make_api_request("consult/concordanceLinksArticle", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des liens de concordance: {str(e)}")
            raise
    
    # ===== LIST CONTROLLER =====
    
    async def list_docs_admins(self, years: List[int]) -> Dict[str, Any]:
        """
        Récupère la liste des documents administratifs pour une période donnée
        
        Args:
            years: Liste des années recherchées
            
        Returns:
            Liste des documents administratifs
        """
        payload = {
            "years": years
        }
        
        try:
            return await self._make_api_request("list/docsAdmins", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des documents administratifs: {str(e)}")
            raise
    
    async def list_bodmr(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Récupère la liste des bulletins officiels des décorations, médailles et récompenses
        
        Args:
            page: Numéro de page
            page_size: Nombre d'éléments par page
            
        Returns:
            Liste paginée des bulletins BODMR
        """
        payload = {
            "page": page,
            "pageSize": page_size
        }
        
        try:
            return await self._make_api_request("list/bodmr", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des BODMR: {str(e)}")
            raise
    
    async def list_dossiers_legislatifs(self, page: int = 1, page_size: int = 10, 
                                       sort: str = None) -> Dict[str, Any]:
        """
        Récupère les dossiers législatifs dans une liste paginée
        
        Args:
            page: Numéro de page
            page_size: Nombre d'éléments par page
            sort: Critère de tri
            
        Returns:
            Liste paginée des dossiers législatifs
        """
        payload = {
            "page": page,
            "pageSize": page_size
        }
        
        if sort:
            payload["sort"] = sort
            
        try:
            return await self._make_api_request("list/dossiersLegislatifs", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des dossiers législatifs: {str(e)}")
            raise
    
    async def list_questions_ecrites(self, page: int = 1, page_size: int = 10, 
                                    legislature: int = None) -> Dict[str, Any]:
        """
        Récupère la liste paginée des questions écrites parlementaires
        
        Args:
            page: Numéro de page
            page_size: Nombre d'éléments par page
            legislature: Numéro de législature
            
        Returns:
            Liste paginée des questions écrites
        """
        payload = {
            "page": page,
            "pageSize": page_size
        }
        
        if legislature:
            payload["legislature"] = legislature
            
        try:
            return await self._make_api_request("list/questionsEcritesParlementaires", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des questions écrites: {str(e)}")
            raise
    
    async def list_conventions(self, page: int = 1, page_size: int = 10, 
                              sort: str = None) -> Dict[str, Any]:
        """
        Récupère les conventions dans une liste paginée
        
        Args:
            page: Numéro de page
            page_size: Nombre d'éléments par page
            sort: Critère de tri
            
        Returns:
            Liste paginée des conventions
        """
        payload = {
            "page": page,
            "pageSize": page_size
        }
        
        if sort:
            payload["sort"] = sort
            
        try:
            return await self._make_api_request("list/conventions", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des conventions: {str(e)}")
            raise
    
    async def list_loda(self, page: int = 1, page_size: int = 10, 
                       nature: str = None, sort: str = None) -> Dict[str, Any]:
        """
        Récupère les éléments de type LODA dans une liste paginée
        
        Args:
            page: Numéro de page
            page_size: Nombre d'éléments par page
            nature: Nature des textes (LOI, ORDONNANCE, etc.)
            sort: Critère de tri
            
        Returns:
            Liste paginée des textes LODA
        """
        payload = {
            "page": page,
            "pageSize": page_size
        }
        
        if nature:
            payload["nature"] = nature
        
        if sort:
            payload["sort"] = sort
            
        try:
            return await self._make_api_request("list/loda", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de récupération des textes LODA: {str(e)}")
            raise
    
    # ===== SEARCH CONTROLLER =====
    
    async def search_codes(self, query: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Recherche dans les codes (Code Civil, Code du Travail, etc.)
        
        Args:
            query: Texte à rechercher
            page: Numéro de page
            page_size: Nombre de résultats par page
            
        Returns:
            Résultats de recherche dans les codes
        """
        payload = {
            "recherche": {
                "champ": query,
                "pageNumber": page,
                "pageSize": page_size
            }
        }
        
        try:
            return await self._make_api_request("search/code", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de recherche dans les codes: {str(e)}")
            if not self.api_key or not self.api_secret:
                return {"results": self._get_mock_code_results(query, page_size)}
            raise
    
    async def search_jurisprudence(self, query: str, page: int = 1, page_size: int = 10, 
                                  sort: str = "date desc") -> Dict[str, Any]:
        """
        Recherche dans la jurisprudence (Cour de cassation, Conseil d'État, etc.)
        
        Args:
            query: Texte à rechercher
            page: Numéro de page
            page_size: Nombre de résultats par page
            sort: Critère de tri
            
        Returns:
            Résultats de recherche dans la jurisprudence
        """
        payload = {
            "recherche": {
                "champ": query,
                "pageNumber": page,
                "pageSize": page_size,
                "sort": sort
            }
        }
        
        try:
            return await self._make_api_request("search/juri", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de recherche dans la jurisprudence: {str(e)}")
            if not self.api_key or not self.api_secret:
                return {"results": self._get_mock_jurisprudence_results(query, page_size)}
            raise
    
    # ===== SUGGEST CONTROLLER =====
    
    async def suggest_acco(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Effectue les suggestions de siret et raisons sociales sur les accords d'entreprise
        
        Args:
            query: Texte pour la suggestion
            max_results: Nombre maximum de résultats
            
        Returns:
            Suggestions de siret et raisons sociales
        """
        payload = {
            "query": query,
            "maxSuggestion": max_results
        }
        
        try:
            return await self._make_api_request("suggest/acco", "POST", payload)
        except Exception as e:
            logger.error(f"Échec de suggestion d'accords: {str(e)}")
            raise
    
    # ===== MISC CONTROLLER =====
    
    async def get_commit_id(self) -> Dict[str, str]:
        """
        Récupère les informations relatives au déploiement et au versionning de l'application
        
        Returns:
            Informations de déploiement et versionning
        """
        try:
            return await self._make_api_request("misc/commitId", "GET")
        except Exception as e:
            logger.error(f"Échec de récupération des informations de version: {str(e)}")
            raise
    
    # ===== HELPER METHODS =====
    
    async def download_pdf(self, pdf_url: str) -> bytes:
        """
        Télécharge un fichier PDF depuis une URL avec authentification
        
        Args:
            pdf_url: URL du fichier PDF
            
        Returns:
            Contenu binaire du PDF
        """
        await self.authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            response = requests.get(pdf_url, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Échec de téléchargement du PDF {pdf_url}: {str(e)}")
            raise
    
    # ===== MOCK DATA METHODS =====
    
    def _get_mock_cnil_result(self, ancien_id: str) -> Dict[str, Any]:
        """Données de test pour une délibération CNIL"""
        logger.info(f"Utilisation de données de test pour la délibération CNIL {ancien_id}")
        
        return {
            "id": f"CNILTEXT000{ancien_id}",
            "title": f"Délibération n°{ancien_id} relative à la protection des données personnelles",
            "text": "La Commission Nationale de l'Informatique et des Libertés...",
            "date": "2023-01-01"
        }
    
    def _get_mock_code_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Données de test pour les codes"""
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
        """Données de test pour la jurisprudence"""
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
                    "juridiction": "Cour de cassation",
                    "formation": "Chambre sociale",
                    "solution": "Rejet"
                }
            },
            {
                "id": "CETATEXT000045694274",
                "title": "Conseil d'État, 6ème chambre, 13/04/2022, 453737",
                "type": "jurisprudence",
                "content": "Vu la procédure suivante : M. A... B... a demandé au juge des référés du tribunal administratif de Paris, statuant sur le fondement de l'article L. 521-2 du code de justice administrative, d'enjoindre au ministre de l'intérieur de procéder au réexamen de sa demande de visa...",
                "date": "2022-04-13",
                "url": "https://www.legifrance.gouv.fr/ceta/id/CETATEXT000045694274",
                "metadata": {
                    "juridiction": "Conseil d'État",
                    "formation": "6ème chambre",
                    "solution": "Rejet"
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
