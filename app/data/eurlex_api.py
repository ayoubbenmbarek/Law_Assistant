import os
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from app.utils.vector_store import vector_store

# Load environment variables
load_dotenv()

# API configuration
EURLEX_API_KEY = os.getenv("EURLEX_API_KEY")
EURLEX_API_BASE_URL = "https://eur-lex.europa.eu/api"

class EURLexAPI:
    """Client pour l'API EUR-Lex d'accès à la législation européenne"""
    
    def __init__(self):
        self.api_key = EURLEX_API_KEY
        self.base_url = EURLEX_API_BASE_URL
        
        if not self.api_key:
            logger.warning("Clé d'API EUR-Lex non configurée. Utilisation de données de test uniquement.")
        
    async def search_regulations(self, query: str, limit: int = 10, apply_to_france: bool = True) -> List[Dict[str, Any]]:
        """
        Recherche des règlements et directives européens
        
        Args:
            query: Termes de recherche
            limit: Nombre maximum de résultats
            apply_to_france: Filtrer uniquement les textes applicables en France
            
        Returns:
            Liste de règlements/directives correspondant à la recherche
        """
        try:
            # Endpoint de recherche
            endpoint = f"{self.base_url}/search"
            
            # Paramètres de recherche
            params = {
                "qid": query,
                "pageSize": limit,
                "page": 1,
                "apiKey": self.api_key
            }
            
            # Filtrer pour la France si demandé
            if apply_to_france:
                params["filter"] = "NATIONAL_LAW_RESPONSIBLE_COUNTRY_CODE:FRA"
            
            # Exécuter la recherche
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            results = response.json()
            
            # Transformation des résultats
            formatted_results = []
            for item in results.get("results", []):
                # Récupérer les détails de chaque document
                doc_details = await self._get_document_details(item.get("celex", ""))
                
                formatted_results.append({
                    "id": f"EURLEX-{item.get('celex', '')}",
                    "title": item.get("title", ""),
                    "type": "regulation_eu" if "regulation" in item.get("documentType", "").lower() else "directive_eu",
                    "content": doc_details.get("content", ""),
                    "date": item.get("dateDocument", datetime.now().strftime("%Y-%m-%d")),
                    "url": f"https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:{item.get('celex', '')}",
                    "metadata": {
                        "celex": item.get("celex", ""),
                        "documentType": item.get("documentType", ""),
                        "application": "France",
                        "original_language": item.get("languageCodes", ["fr"])[0]
                    }
                })
                
            return formatted_results
                
        except Exception as e:
            logger.error(f"Échec de recherche dans EUR-Lex: {str(e)}")
            if not self.api_key:
                return self._get_mock_eurlex_results(query, limit)
            raise
    
    async def _get_document_details(self, celex: str) -> Dict[str, Any]:
        """
        Récupérer les détails d'un document EUR-Lex spécifique
        
        Args:
            celex: Identifiant CELEX du document
            
        Returns:
            Détails du document incluant son contenu
        """
        try:
            if not celex:
                return {"content": ""}
                
            # Endpoint pour les détails d'un document
            endpoint = f"{self.base_url}/document/{celex}"
            
            params = {
                "apiKey": self.api_key,
                "language": "FR"
            }
            
            # Récupérer les détails
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            # Extraire le contenu textuel
            content = result.get("content", "")
            if isinstance(content, dict):
                content = content.get("value", "")
                
            return {
                "content": content,
                "languages": result.get("availableLanguages", []),
                "consolidated": result.get("isConsolidated", False)
            }
            
        except Exception as e:
            logger.error(f"Échec de récupération des détails pour CELEX {celex}: {str(e)}")
            return {"content": ""}
    
    def _get_mock_eurlex_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Données de test pour EUR-Lex (à utiliser quand l'API n'est pas configurée)"""
        logger.info("Utilisation de données de test pour EUR-Lex")
        
        mock_results = [
            {
                "id": "EURLEX-32016R0679",
                "title": "Règlement (UE) 2016/679 du Parlement européen et du Conseil (RGPD)",
                "type": "regulation_eu",
                "content": "Le règlement (UE) 2016/679 du Parlement européen et du Conseil du 27 avril 2016 relatif à la protection des personnes physiques à l'égard du traitement des données à caractère personnel et à la libre circulation de ces données, et abrogeant la directive 95/46/CE (règlement général sur la protection des données).",
                "date": "2016-04-27",
                "url": "https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32016R0679",
                "metadata": {
                    "celex": "32016R0679",
                    "documentType": "REGULATION",
                    "application": "France",
                    "original_language": "en"
                }
            },
            {
                "id": "EURLEX-32019L0790",
                "title": "Directive (UE) 2019/790 sur le droit d'auteur et les droits voisins dans le marché unique numérique",
                "type": "directive_eu",
                "content": "La directive (UE) 2019/790 du Parlement européen et du Conseil du 17 avril 2019 sur le droit d'auteur et les droits voisins dans le marché unique numérique et modifiant les directives 96/9/CE et 2001/29/CE.",
                "date": "2019-04-17",
                "url": "https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32019L0790",
                "metadata": {
                    "celex": "32019L0790",
                    "documentType": "DIRECTIVE",
                    "application": "France",
                    "original_language": "en"
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
                
            logger.info(f"Importation de {len(sources)} sources européennes dans la base vectorielle")
        except Exception as e:
            logger.error(f"Échec d'importation dans la base vectorielle: {str(e)}")
            raise

# Créer l'instance du client API
eurlex_api = EURLexAPI() 