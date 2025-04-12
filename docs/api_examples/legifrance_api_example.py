#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API Légifrance pour le projet d'assistant juridique
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("legifrance_api")

# Charger les variables d'environnement
load_dotenv()

# Configuration
PISTE_API_KEY = os.getenv("PISTE_API_KEY", "votre_client_id")
PISTE_SECRET_KEY = os.getenv("PISTE_SECRET_KEY", "votre_client_secret")
PISTE_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"

# Stockage du token
TOKEN_INFO = {
    "token": None,
    "expiry": None
}

class LegifranceAPI:
    """Client pour l'API Légifrance"""
    
    def __init__(self, api_key=None, api_secret=None):
        """Initialise le client API"""
        self.api_key = api_key or PISTE_API_KEY
        self.api_secret = api_secret or PISTE_SECRET_KEY
        self.base_url = LEGIFRANCE_API_BASE_URL
        self.auth_url = PISTE_AUTH_URL
        
        if not self.api_key or not self.api_secret:
            logger.warning("Clés d'API Légifrance non configurées. Définissez PISTE_API_KEY et PISTE_SECRET_KEY.")
    
    def authenticate(self):
        """Authentification à l'API Légifrance pour obtenir un token"""
        # Vérifier si le token actuel est encore valide
        if TOKEN_INFO["token"] and TOKEN_INFO["expiry"] and datetime.now() < TOKEN_INFO["expiry"]:
            logger.debug("Utilisation du token existant (encore valide)")
            return TOKEN_INFO["token"]
            
        try:
            logger.info("Authentification à l'API Légifrance...")
            
            auth_data = {
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "grant_type": "client_credentials",
                "scope": "openid"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
                
            response = requests.post(self.auth_url, data=auth_data, headers=headers, timeout=10)
            response.raise_for_status()
            
            auth_result = response.json()
            token = auth_result.get("access_token")
            
            # Token expires in (default 30min)
            expires_in = auth_result.get("expires_in", 1800)
            expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Mettre à jour les informations du token
            TOKEN_INFO["token"] = token
            TOKEN_INFO["expiry"] = expiry
            
            logger.info(f"Authentification réussie! Token valide jusqu'à {expiry.strftime('%H:%M:%S')}")
            return token
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP lors de l'authentification: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Statut: {e.response.status_code}")
                logger.error(f"Réponse: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification: {str(e)}")
            return None
    
    def search_codes(self, query, limit=10, page=1, filters=None):
        """Recherche dans les codes"""
        token = self.authenticate()
        if not token:
            logger.error("Impossible de s'authentifier. Recherche annulée.")
            return None
            
        try:
            endpoint = f"{self.base_url}/consult/code"
            
            # Construire la requête
            payload = {
                "recherche": {
                    "champ": query,
                    "pageNumber": page,
                    "pageSize": limit,
                    "sort": "pertinence",
                    "typePagination": "ARTICLE"
                }
            }
            
            # Ajouter les filtres si fournis
            if filters:
                payload["recherche"]["filtres"] = filters
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.info(f"Recherche dans les codes avec le terme: '{query}'")
            logger.debug(f"Payload: {json.dumps(payload)}")
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            results = response.json()
            
            if "results" in results:
                logger.info(f"Recherche réussie: {len(results['results'])} résultats trouvés")
            
            return results
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP lors de la recherche: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Statut: {e.response.status_code}")
                logger.error(f"Réponse: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return None
    
    def search_jurisprudence(self, query, limit=10, page=1, jurisdiction=None, date_from=None, date_to=None):
        """Recherche dans la jurisprudence"""
        token = self.authenticate()
        if not token:
            logger.error("Impossible de s'authentifier. Recherche annulée.")
            return None
            
        try:
            endpoint = f"{self.base_url}/consult/juri"
            
            # Construire la requête
            payload = {
                "recherche": {
                    "champ": query,
                    "pageNumber": page,
                    "pageSize": limit,
                    "sort": "date desc"
                }
            }
            
            # Ajouter des filtres
            filters = []
            
            if jurisdiction:
                filters.append({
                    "name": "JURIDICTION",
                    "value": jurisdiction
                })
            
            if date_from or date_to:
                date_filter = {"name": "DATE_DECISION"}
                if date_from:
                    date_filter["start"] = date_from
                if date_to:
                    date_filter["end"] = date_to
                filters.append(date_filter)
            
            if filters:
                payload["recherche"]["filtres"] = filters
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.info(f"Recherche dans la jurisprudence avec le terme: '{query}'")
            logger.debug(f"Payload: {json.dumps(payload)}")
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            results = response.json()
            
            if "results" in results:
                logger.info(f"Recherche réussie: {len(results['results'])} résultats trouvés")
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche dans la jurisprudence: {str(e)}")
            return None
    
    def format_result(self, result, source_type):
        """Formate un résultat pour l'affichage ou le stockage"""
        formatted = {
            "id": result.get("id", ""),
            "title": result.get("title", ""),
            "text": result.get("text", ""),
            "date": result.get("date", ""),
            "source_type": source_type
        }
        
        # Ajouter des champs spécifiques selon le type de source
        if source_type == "code":
            formatted["nature"] = result.get("nature", "")
            formatted["code_name"] = result.get("title", "").split(" - ")[-1] if " - " in result.get("title", "") else ""
            formatted["url"] = f"https://www.legifrance.gouv.fr{result.get('url', '')}"
        
        elif source_type == "jurisprudence":
            formatted["jurisdiction"] = result.get("formation", "")
            formatted["solution"] = result.get("solution", "")
            formatted["url"] = f"https://www.legifrance.gouv.fr{result.get('url', '')}"
        
        return formatted
    
    def format_results(self, api_results, source_type):
        """Formate une liste de résultats"""
        if not api_results or "results" not in api_results:
            return []
            
        formatted_results = []
        
        for result in api_results["results"]:
            formatted_results.append(self.format_result(result, source_type))
        
        # Ajouter les informations de pagination
        pagination = {
            "page": api_results.get("pagination", {}).get("page", 1),
            "pageSize": api_results.get("pagination", {}).get("pageSize", 10),
            "totalResults": api_results.get("pagination", {}).get("totalResults", 0)
        }
        
        return {
            "results": formatted_results,
            "pagination": pagination
        }


def main():
    """Fonction principale de démonstration"""
    # Parsing des arguments
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "rupture conventionnelle"
    
    # Initialisation du client API
    client = LegifranceAPI()
    
    # Exemple de recherche dans les codes
    print("\n--- RECHERCHE DANS LES CODES ---")
    results_codes = client.search_codes(query, limit=3)
    
    # Formatage et affichage des résultats
    if results_codes and "results" in results_codes:
        formatted_results = client.format_results(results_codes, "code")
        
        print(f"\nRésultats pour '{query}' dans les codes:")
        for i, item in enumerate(formatted_results["results"]):
            print(f"\n--- Résultat {i+1} ---")
            print(f"Titre: {item['title']}")
            print(f"Date: {item['date']}")
            print(f"URL: {item['url']}")
            print(f"Extrait: {item['text'][:150]}..." if len(item['text']) > 150 else f"Extrait: {item['text']}")
        
        pagination = formatted_results["pagination"]
        print(f"\nPage {pagination['page']}/{(pagination['totalResults'] // pagination['pageSize']) + 1} - "
              f"Total: {pagination['totalResults']} résultats")
    else:
        print("Aucun résultat trouvé ou erreur lors de la recherche")
    
    # Exemple de recherche dans la jurisprudence
    print("\n--- RECHERCHE DANS LA JURISPRUDENCE ---")
    results_juri = client.search_jurisprudence(query, limit=3)
    
    # Formatage et affichage des résultats
    if results_juri and "results" in results_juri:
        formatted_results = client.format_results(results_juri, "jurisprudence")
        
        print(f"\nRésultats pour '{query}' dans la jurisprudence:")
        for i, item in enumerate(formatted_results["results"]):
            print(f"\n--- Résultat {i+1} ---")
            print(f"Titre: {item['title']}")
            print(f"Date: {item['date']}")
            print(f"Juridiction: {item.get('jurisdiction', 'Non précisée')}")
            print(f"URL: {item['url']}")
            print(f"Extrait: {item['text'][:150]}..." if len(item['text']) > 150 else f"Extrait: {item['text']}")
        
        pagination = formatted_results["pagination"]
        print(f"\nPage {pagination['page']}/{(pagination['totalResults'] // pagination['pageSize']) + 1} - "
              f"Total: {pagination['totalResults']} résultats")
    else:
        print("Aucun résultat trouvé ou erreur lors de la recherche")
        
    return 0


if __name__ == "__main__":
    sys.exit(main()) 