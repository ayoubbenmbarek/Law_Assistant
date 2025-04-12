#!/usr/bin/env python3
"""
Script de test pour la connexion à l'API Légifrance PISTE en local
"""

import os
import requests
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
LEGIFRANCE_API_KEY = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
LEGIFRANCE_API_SECRET = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")
LEGIFRANCE_API_BASE_URL = "https://api.aife.economie.gouv.fr/dila/legifrance/lf-engine-app"

def authenticate():
    """Authentification à l'API Légifrance pour obtenir un token"""
    try:
        auth_url = "https://oauth.aife.economie.gouv.fr/api/oauth/token"
        auth_data = {
            "client_id": LEGIFRANCE_API_KEY,
            "client_secret": LEGIFRANCE_API_SECRET,
            "grant_type": "client_credentials",
            "scope": "openid"
        }
        
        print(f"Tentative d'authentification avec client_id: {LEGIFRANCE_API_KEY}")
        response = requests.post(auth_url, data=auth_data)
        response.raise_for_status()
        
        auth_result = response.json()
        token = auth_result.get("access_token")
        
        # Token expires in (default 30min)
        expires_in = auth_result.get("expires_in", 1800)
        token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        print(f"Authentification réussie! Token valide jusqu'à {token_expiry.strftime('%H:%M:%S')}")
        return token
        
    except Exception as e:
        print(f"Échec d'authentification à l'API Légifrance: {str(e)}")
        if response:
            print(f"Statut: {response.status_code}")
            print(f"Réponse: {response.text}")
        raise

def search_codes(token, query="travail", limit=3):
    """Recherche dans les codes (Code Civil, Code du Travail, etc.)"""
    try:
        endpoint = f"{LEGIFRANCE_API_BASE_URL}/consult/code"
        
        payload = {
            "recherche": {
                "champ": query,
                "pageNumber": 1,
                "pageSize": limit
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"Recherche dans les codes avec le terme: '{query}'")
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        results = response.json()
        return results
        
    except Exception as e:
        print(f"Échec de recherche dans les codes: {str(e)}")
        if 'response' in locals() and response:
            print(f"Statut: {response.status_code}")
            print(f"Réponse: {response.text}")
        raise

def format_results(results):
    """Formatte les résultats pour un affichage lisible"""
    if not results or 'results' not in results:
        print("Aucun résultat trouvé")
        return
    
    total = len(results.get('results', []))
    print(f"Nombre de résultats: {total}")
    
    for i, item in enumerate(results.get('results', [])):
        print(f"\n--- Résultat {i+1}/{total} ---")
        print(f"ID: {item.get('id')}")
        print(f"Titre: {item.get('title')}")
        
        # Afficher un extrait du contenu (limité à 200 caractères)
        content = item.get('text', '')
        if len(content) > 200:
            content = content[:197] + '...'
        print(f"Contenu: {content}")
        
        # Afficher des métadonnées
        if 'code' in item and item['code']:
            print(f"Code: {item.get('code', {}).get('title', '')}")
        if 'context' in item:
            print(f"Section: {item.get('context', '')}")

def main():
    """Fonction principale"""
    try:
        print("Test de connexion à l'API Légifrance PISTE")
        token = authenticate()
        
        if len(sys.argv) > 1:
            query = sys.argv[1]
        else:
            query = "travail"
        
        print(f"\nRecherche avec le terme: {query}")
        results = search_codes(token, query=query)
        format_results(results)
        
        print("\nTest terminé avec succès")
        return True
        
    except Exception as e:
        print(f"Erreur lors du test: {str(e)}")
        return False

if __name__ == "__main__":
    result = main()
    if not result:
        sys.exit(1) 