import os
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# API configuration
JUDILIBRE_KEY_ID = os.getenv("JUDILIBRE_KEY_ID", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
JUDILIBRE_TOKEN = os.getenv("JUDILIBRE_TOKEN", "WnU2HnkvuiQkmt0A9mxcFdcUmf6aIJwWOH9VKd4A3lP8yxFizji8D7")
JUDILIBRE_BASE_URL = "https://api.piste.gouv.fr/cassation/judilibre/v1.0"
JUDILIBRE_SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"

class JudilibreAPI:
    """Client pour l'API Judilibre (jurisprudence de la Cour de cassation)"""
    
    def __init__(self, use_sandbox: bool = False):
        self.key_id = JUDILIBRE_KEY_ID
        self.token = JUDILIBRE_TOKEN
        self.base_url = JUDILIBRE_SANDBOX_URL if use_sandbox else JUDILIBRE_BASE_URL
        
        if not self.key_id or not self.token:
            logger.warning("Clés d'API Judilibre non configurées. Utilisation de données de test uniquement.")
    
    async def search_decisions(self, query: str = None, chamber: str = None, 
                              formation: str = None, jurisdiction: str = None, 
                              location: str = None, solution: str = None,
                              date_start: str = None, date_end: str = None,
                              page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """
        Recherche de décisions dans la base Judilibre
        
        Args:
            query: Terme de recherche
            chamber: Chambre (ex: "Chambre civile 1")
            formation: Formation (ex: "Formation plénière")
            jurisdiction: Juridiction (ex: "Cour de cassation")
            location: Localisation
            solution: Solution (ex: "Cassation")
            date_start: Date de début (format: YYYY-MM-DD)
            date_end: Date de fin (format: YYYY-MM-DD)
            page_size: Nombre de résultats par page
            page: Numéro de la page
        
        Returns:
            Dictionnaire contenant les résultats
        """
        try:
            endpoint = f"{self.base_url}/search"
            
            # Construction des paramètres de recherche
            params = {}
            
            if query:
                params["query"] = query
            if chamber:
                params["chamber"] = chamber
            if formation:
                params["formation"] = formation
            if jurisdiction:
                params["jurisdiction"] = jurisdiction
            if location:
                params["location"] = location
            if solution:
                params["solution"] = solution
            if date_start:
                params["date_start"] = date_start
            if date_end:
                params["date_end"] = date_end
            
            params["page_size"] = page_size
            params["page"] = page
            
            headers = {
                "KeyId": self.key_id,
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json"
            }
            
            logger.debug(f"Requête Judilibre: {endpoint} avec params={params}")
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Recherche Judilibre réussie: {results.get('total', 0)} résultats")
            
            return results
            
        except Exception as e:
            logger.error(f"Échec de recherche dans Judilibre: {str(e)}")
            if not self.key_id or not self.token:
                return self._get_mock_results(query, page_size)
            raise
    
    async def get_decision(self, id: str) -> Dict[str, Any]:
        """
        Récupère une décision spécifique par son ID
        
        Args:
            id: Identifiant de la décision
            
        Returns:
            Dictionnaire contenant les détails de la décision
        """
        try:
            endpoint = f"{self.base_url}/decision/{id}"
            
            headers = {
                "KeyId": self.key_id,
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json"
            }
            
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Récupération de la décision {id} réussie")
            
            return result
            
        except Exception as e:
            logger.error(f"Échec de récupération de la décision {id}: {str(e)}")
            if not self.key_id or not self.token:
                return self._get_mock_decision(id)
            raise
    
    async def export_decisions(self, location: str = None, batch: int = None) -> Dict[str, Any]:
        """
        Exporter un lot de décisions
        
        Args:
            location: Localisation (facultatif)
            batch: Numéro de lot
            
        Returns:
            Dictionnaire contenant les décisions exportées
        """
        try:
            endpoint = f"{self.base_url}/export"
            
            params = {}
            if location:
                params["location"] = location
            if batch:
                params["batch"] = batch
            
            headers = {
                "KeyId": self.key_id,
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json"
            }
            
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Export Judilibre réussi: {len(results.get('decisions', []))} décisions")
            
            return results
            
        except Exception as e:
            logger.error(f"Échec de l'export Judilibre: {str(e)}")
            raise
    
    def _get_mock_results(self, query: str = None, limit: int = 10) -> Dict[str, Any]:
        """Données de test pour la recherche (à utiliser quand l'API n'est pas configurée)"""
        logger.info("Utilisation de données de test pour Judilibre")
        
        mock_results = {
            "total": 2,
            "page_size": limit,
            "page": 1,
            "decisions": [
                {
                    "id": "63a54123d6cd3ecc7dd95cf2",
                    "jurisdiction": "Cour de cassation",
                    "chamber": "Chambre civile 1",
                    "number": "21-19.963",
                    "publication": ["B", "P", "I"],
                    "solution": "Cassation",
                    "decision_date": "2022-11-30",
                    "update_date": "2022-12-23",
                    "portalis": "D5D-KT2-B7D77",
                    "files": ["https://www.courdecassation.fr/decision/63a54123d6cd3ecc7dd95cf2"],
                    "themes": ["PROPRIÉTÉ"],
                    "summary": "Selon l'article 544 du code civil, la propriété est le droit de jouir et disposer des choses de la manière la plus absolue, pourvu qu'on n'en fasse pas un usage prohibé par les lois ou par les règlements.",
                },
                {
                    "id": "63a54123d6cd3ecc7dd95cf3",
                    "jurisdiction": "Cour de cassation",
                    "chamber": "Chambre sociale",
                    "number": "21-18.245",
                    "publication": ["B"],
                    "solution": "Rejet",
                    "decision_date": "2022-11-29",
                    "update_date": "2022-12-23",
                    "portalis": "D9H-KT2-B7C66",
                    "files": ["https://www.courdecassation.fr/decision/63a54123d6cd3ecc7dd95cf3"],
                    "themes": ["CONTRAT DE TRAVAIL"],
                    "summary": "Le licenciement prononcé par un employeur pour un motif lié à l'exercice normal du droit de grève par un salarié est nul.",
                }
            ]
        }
        
        return mock_results
    
    def _get_mock_decision(self, id: str) -> Dict[str, Any]:
        """Données de test pour une décision spécifique (à utiliser quand l'API n'est pas configurée)"""
        logger.info(f"Utilisation de données de test pour la décision {id}")
        
        mock_decision = {
            "id": id,
            "jurisdiction": "Cour de cassation",
            "chamber": "Chambre civile 1",
            "number": "21-19.963",
            "publication": ["B", "P", "I"],
            "solution": "Cassation",
            "decision_date": "2022-11-30",
            "update_date": "2022-12-23",
            "portalis": "D5D-KT2-B7D77",
            "files": ["https://www.courdecassation.fr/decision/63a54123d6cd3ecc7dd95cf2"],
            "themes": ["PROPRIÉTÉ"],
            "summary": "Selon l'article 544 du code civil, la propriété est le droit de jouir et disposer des choses de la manière la plus absolue.",
            "text": "LA COUR DE CASSATION, PREMIÈRE CHAMBRE CIVILE, a rendu l'arrêt suivant :\n\nSur le moyen unique :\n\nVu l'article 544 du code civil ;\n\nAttendu que la propriété est le droit de jouir et disposer des choses de la manière la plus absolue, pourvu qu'on n'en fasse pas un usage prohibé par les lois ou par les règlements ;\n\nAtttendu, selon l'arrêt attaqué, que [décision...] ;\n\nQu'en statuant ainsi, alors que [raisonnement...], la cour d'appel a violé le texte susvisé ;\n\nPAR CES MOTIFS :\n\nCASSE ET ANNULE, en toutes ses dispositions, l'arrêt rendu le [date], entre les parties, par la cour d'appel de [lieu] ; remet, en conséquence, la cause et les parties dans l'état où elles se trouvaient avant ledit arrêt et, pour être fait droit, les renvoie devant la cour d'appel de [lieu] ;"
        }
        
        return mock_decision 