import os
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from app.utils.vector_store import vector_store
import aiohttp

# Load environment variables
load_dotenv()

# API configuration
CONSEIL_CONST_API_URL = "https://www.conseil-constitutionnel.fr/api/decisions"

class ConseilConstitutionnelAPI:
    """Client pour l'API du Conseil Constitutionnel français"""
    
    def __init__(self):
        self.base_url = CONSEIL_CONST_API_URL
        
    async def search_decisions(self, query: str = None, limit: int = 10, 
                             date_start: str = None, date_end: str = None) -> List[Dict[str, Any]]:
        """
        Recherche des décisions du Conseil Constitutionnel
        
        Args:
            query: Termes de recherche
            limit: Nombre maximum de résultats
            date_start: Date de début au format YYYY-MM-DD
            date_end: Date de fin au format YYYY-MM-DD
            
        Returns:
            Liste des décisions correspondant aux critères
        """
        try:
            # Construire les paramètres de recherche
            params = {"size": limit}
            
            if query:
                params["q"] = query
                
            if date_start:
                params["date_start"] = date_start
                
            if date_end:
                params["date_end"] = date_end
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Erreur API Conseil Constitutionnel: {response.status}")
                        return self._get_mock_decisions(query, limit)
                        
                    results = await response.json()
            
            # Transformation des résultats
            formatted_results = []
            for item in results.get("decisions", []):
                # Récupérer les détails de chaque décision
                decision_details = await self._get_decision_details(item.get("id", ""))
                
                formatted_results.append({
                    "id": f"CONSCONST-{item.get('id', '')}",
                    "title": item.get("titre", ""),
                    "type": "decision_constitutionnelle",
                    "content": decision_details.get("content", ""),
                    "date": item.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "url": f"https://www.conseil-constitutionnel.fr/decision/{item.get('id', '')}",
                    "metadata": {
                        "numero": item.get("numero", ""),
                        "type_decision": item.get("type", ""),
                        "formation": item.get("formation", ""),
                        "conformite": item.get("solution", ""),
                        "saisine": item.get("saisine", {}).get("type", "")
                    }
                })
                
            return formatted_results
                
        except Exception as e:
            logger.error(f"Échec de recherche dans le Conseil Constitutionnel: {str(e)}")
            return self._get_mock_decisions(query, limit)
    
    async def _get_decision_details(self, decision_id: str) -> Dict[str, Any]:
        """
        Récupérer les détails d'une décision spécifique
        
        Args:
            decision_id: Identifiant de la décision
            
        Returns:
            Détails de la décision incluant son contenu
        """
        try:
            if not decision_id:
                return {"content": ""}
                
            # Endpoint pour les détails d'une décision
            endpoint = f"{self.base_url}/{decision_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint) as response:
                    if response.status != 200:
                        logger.error(f"Erreur API détails Conseil Constitutionnel: {response.status}")
                        return {"content": ""}
                        
                    result = await response.json()
            
            # Extraire le contenu textuel
            content = result.get("contenu", {}).get("texte", "")
            if not content:
                content = result.get("contenu", {}).get("resume", "")
                
            return {
                "content": content,
                "articles_cites": result.get("articles_cites", []),
                "textes_cites": result.get("textes_cites", []),
                "visas": result.get("contenu", {}).get("visas", "")
            }
            
        except Exception as e:
            logger.error(f"Échec de récupération des détails pour la décision {decision_id}: {str(e)}")
            return {"content": ""}
    
    def _get_mock_decisions(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Données de test pour le Conseil Constitutionnel"""
        logger.info("Utilisation de données de test pour le Conseil Constitutionnel")
        
        mock_results = [
            {
                "id": "CONSCONST-2022-1004",
                "title": "Décision n° 2022-1004 QPC du 22 juillet 2022",
                "type": "decision_constitutionnelle",
                "content": "Le Conseil constitutionnel a été saisi le 20 mai 2022 par le Conseil d'État d'une question prioritaire de constitutionnalité relative à la conformité aux droits et libertés que la Constitution garantit du paragraphe V de l'article 1er de la loi n° 2021-1040 du 5 août 2021 relative à la gestion de la crise sanitaire.",
                "date": "2022-07-22",
                "url": "https://www.conseil-constitutionnel.fr/decision/2022/20221004QPC.htm",
                "metadata": {
                    "numero": "2022-1004 QPC",
                    "type_decision": "QPC",
                    "formation": "Le Conseil constitutionnel",
                    "conformite": "Conforme",
                    "saisine": "QPC"
                }
            },
            {
                "id": "CONSCONST-2020-799",
                "title": "Décision n° 2020-799 DC du 26 mars 2020",
                "type": "decision_constitutionnelle",
                "content": "Le Conseil constitutionnel a été saisi, le 23 mars 2020, par le Premier ministre, conformément au cinquième alinéa de l'article 46 et au deuxième alinéa de l'article 61 de la Constitution, de la loi organique d'urgence pour faire face à l'épidémie de covid-19.",
                "date": "2020-03-26",
                "url": "https://www.conseil-constitutionnel.fr/decision/2020/2020799DC.htm",
                "metadata": {
                    "numero": "2020-799 DC",
                    "type_decision": "DC",
                    "formation": "Le Conseil constitutionnel",
                    "conformite": "Conforme",
                    "saisine": "Première ministre"
                }
            }
        ]
        
        return mock_results[:limit]
    
    async def import_to_vector_store(self, sources: List[Dict[str, Any]]):
        """Importe des décisions dans la base vectorielle"""
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
                
            logger.info(f"Importation de {len(sources)} décisions constitutionnelles dans la base vectorielle")
        except Exception as e:
            logger.error(f"Échec d'importation dans la base vectorielle: {str(e)}")
            raise

# Créer l'instance du client API
conseil_constitutionnel_api = ConseilConstitutionnelAPI() 