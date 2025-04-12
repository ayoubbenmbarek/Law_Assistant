#!/usr/bin/env python3
"""
Script pour importer des données de l'API Légifrance PISTE localement
et les sauvegarder dans des fichiers JSON
"""

import os
import json
import argparse
import sys
import time
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# API configuration
LEGIFRANCE_API_KEY = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
LEGIFRANCE_API_SECRET = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")
LEGIFRANCE_API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
LEGIFRANCE_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

# Répertoire de sortie pour les fichiers JSON
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legal_data")

def ensure_output_dir():
    """Créer le répertoire de sortie s'il n'existe pas"""
    if not os.path.exists(OUTPUT_DIR):
        print(f"Création du répertoire de sortie: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

def authenticate():
    """Authentification à l'API Légifrance pour obtenir un token"""
    response = None
    try:
        print(f"Tentative d'authentification avec client_id: {LEGIFRANCE_API_KEY}")
        auth_data = {
            "client_id": LEGIFRANCE_API_KEY,
            "client_secret": LEGIFRANCE_API_SECRET,
            "grant_type": "client_credentials",
            "scope": "openid"
        }
        
        response = requests.post(LEGIFRANCE_AUTH_URL, data=auth_data)
        response.raise_for_status()
        
        auth_result = response.json()
        token = auth_result.get("access_token")
        
        # Token expires in (default 30min)
        expires_in = auth_result.get("expires_in", 1800)
        token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        print(f"Authentification réussie! Token valide jusqu'à {token_expiry.strftime('%H:%M:%S')}")
        return token
        
    except requests.exceptions.ConnectionError as e:
        print(f"Erreur de connexion à l'API Légifrance: {str(e)}")
        print("Vérifiez votre connexion internet et les paramètres du serveur proxy si nécessaire.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP lors de l'authentification à l'API Légifrance: {str(e)}")
        if response:
            print(f"Statut: {response.status_code}")
            print(f"Réponse: {response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Échec d'authentification à l'API Légifrance: {str(e)}")
        if response:
            print(f"Statut: {response.status_code}")
            print(f"Réponse: {response.text}")
        sys.exit(1)

def search_codes(token, query="travail", limit=10, page=1):
    """Recherche dans les codes (Code Civil, Code du Travail, etc.)"""
    response = None
    try:
        endpoint = f"{LEGIFRANCE_API_BASE_URL}/consult/code"
        
        payload = {
            "recherche": {
                "champ": query,
                "pageNumber": page,
                "pageSize": limit
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"Recherche dans les codes avec le terme: '{query}' (page {page}, limite {limit})")
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        results = response.json()
        return results
        
    except Exception as e:
        print(f"Échec de recherche dans les codes: {str(e)}")
        if response:
            print(f"Statut: {response.status_code}")
            print(f"Réponse: {response.text}")
        return None

def search_jurisprudence(token, query="travail", limit=10, page=1):
    """Recherche dans la jurisprudence"""
    response = None
    try:
        endpoint = f"{LEGIFRANCE_API_BASE_URL}/consult/juri"
        
        payload = {
            "recherche": {
                "champ": query,
                "pageNumber": page,
                "pageSize": limit
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"Recherche dans la jurisprudence avec le terme: '{query}' (page {page}, limite {limit})")
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        results = response.json()
        return results
        
    except Exception as e:
        print(f"Échec de recherche dans la jurisprudence: {str(e)}")
        if response:
            print(f"Statut: {response.status_code}")
            print(f"Réponse: {response.text}")
        return None

def save_results(results, file_prefix, query, page):
    """Sauvegarder les résultats dans un fichier JSON"""
    if not results or 'results' not in results:
        print("Aucun résultat à sauvegarder")
        return 0
    
    # Créer un nom de fichier avec le timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{file_prefix}_{query.replace(' ', '_')}_{page}_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Sauvegarder les résultats
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    count = len(results.get('results', []))
    print(f"Sauvegardé {count} résultats dans {filepath}")
    return count

def import_data(data_type, query, limit_per_page, max_pages):
    """Importer des données juridiques depuis l'API PISTE"""
    token = authenticate()
    
    total_imported = 0
    
    for page in range(1, max_pages + 1):
        # Pause entre les requêtes pour éviter de saturer l'API
        if page > 1:
            print(f"Pause de 2 secondes entre les requêtes...")
            time.sleep(2)
        
        if data_type == "codes":
            results = search_codes(token, query, limit_per_page, page)
            if results:
                count = save_results(results, "codes", query, page)
                total_imported += count
            else:
                print(f"Pas de résultats pour la page {page}")
                break
                
        elif data_type == "jurisprudence":
            results = search_jurisprudence(token, query, limit_per_page, page)
            if results:
                count = save_results(results, "jurisprudence", query, page)
                total_imported += count
            else:
                print(f"Pas de résultats pour la page {page}")
                break
    
    print(f"Total importé: {total_imported} documents")
    return total_imported

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Importer des données juridiques de l'API PISTE")
    parser.add_argument("--type", choices=["codes", "jurisprudence"], default="codes",
                      help="Type de données à importer (par défaut: codes)")
    parser.add_argument("--query", default="travail", 
                      help="Terme de recherche (par défaut: travail)")
    parser.add_argument("--limit", type=int, default=10,
                      help="Nombre de résultats par page (par défaut: 10)")
    parser.add_argument("--pages", type=int, default=1,
                      help="Nombre de pages à récupérer (par défaut: 1)")
    
    args = parser.parse_args()
    
    print(f"Importation de données juridiques depuis l'API PISTE")
    print(f"Type: {args.type}")
    print(f"Requête: {args.query}")
    print(f"Limite par page: {args.limit}")
    print(f"Nombre de pages: {args.pages}")
    
    # Créer le répertoire de sortie
    ensure_output_dir()
    
    # Importer les données
    import_data(args.type, args.query, args.limit, args.pages)
    
    print("Importation terminée avec succès")

if __name__ == "__main__":
    main() 