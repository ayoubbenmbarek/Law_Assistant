#!/usr/bin/env python3
"""
Script d'exploration des APIs disponibles sur la plateforme PISTE
"""

import os
import sys
import json
import requests
import argparse
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Charger les variables d'environnement
load_dotenv()

# API configuration - méthode API Key
PISTE_API_KEY = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
PISTE_SECRET_KEY = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")

# API configuration - méthode OAuth
PISTE_OAUTH_CLIENT_ID = os.getenv("PISTE_OAUTH_CLIENT_ID", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
PISTE_OAUTH_SECRET_KEY = os.getenv("PISTE_OAUTH_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")

# URLs
PISTE_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
PISTE_BASE_URL = "https://api.piste.gouv.fr"

# Liste des APIs disponibles
API_PROVIDERS = {
    "legifrance": {
        "base_url": "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app",
        "endpoints": [
            {"path": "/consult/code", "method": "POST", "description": "Recherche dans les codes"},
            {"path": "/consult/juri", "method": "POST", "description": "Recherche dans la jurisprudence"},
            {"path": "/consult/legi", "method": "POST", "description": "Recherche dans la législation"}
        ]
    },
    "entreprise": {
        "base_url": "https://api.piste.gouv.fr/entreprise/v3",
        "endpoints": [
            {"path": "/insee/sirene/etablissements", "method": "GET", "description": "Données SIRENE des établissements"},
            {"path": "/insee/sirene/unites_legales", "method": "GET", "description": "Données SIRENE des unités légales"}
        ]
    },
    "api-particulier": {
        "base_url": "https://api.piste.gouv.fr/api-particulier/v2",
        "endpoints": [
            {"path": "/composition-familiale", "method": "GET", "description": "Données de composition familiale"},
            {"path": "/certificat-scolarite", "method": "GET", "description": "Certificats de scolarité"}
        ]
    },
    "api-entreprise": {
        "base_url": "https://api.piste.gouv.fr/entreprise/v3",
        "endpoints": [
            {"path": "/insee/sirene/unites_legales/{siren}", "method": "GET", "description": "Données d'une unité légale"},
            {"path": "/urssaf/attestation-vigilance", "method": "GET", "description": "Attestation de vigilance URSSAF"}
        ]
    },
    "api-geo": {
        "base_url": "https://api.piste.gouv.fr/geo/v1",
        "endpoints": [
            {"path": "/communes", "method": "GET", "description": "Liste des communes"},
            {"path": "/departements", "method": "GET", "description": "Liste des départements"}
        ]
    }
}

def get_token(auth_type="apikey", verbose=False):
    """Authentification à l'API PISTE pour obtenir un token"""
    response = None
    try:
        if verbose:
            print("=== Authentification à l'API PISTE ===")
            print(f"URL d'authentification: {PISTE_AUTH_URL}")
            print(f"Méthode d'authentification: {auth_type.upper()}")
        
        if auth_type.lower() == "oauth":
            # Authentification avec les identifiants OAuth
            if not PISTE_OAUTH_SECRET_KEY:
                print("⚠️ La clé secrète OAuth n'est pas configurée. Passage à l'authentification par APIKey.")
                return get_token("apikey", verbose)
                
            auth_data = {
                "client_id": PISTE_OAUTH_CLIENT_ID,
                "client_secret": PISTE_OAUTH_SECRET_KEY,
                "grant_type": "client_credentials",
                "scope": "openid"
            }
            
            if verbose:
                print(f"Client ID: {PISTE_OAUTH_CLIENT_ID}")
                print(f"Secret Key: {PISTE_OAUTH_SECRET_KEY[:4]}{'*' * (len(PISTE_OAUTH_SECRET_KEY) - 8)}{PISTE_OAUTH_SECRET_KEY[-4:] if len(PISTE_OAUTH_SECRET_KEY) > 8 else ''}")
        else:
            # Authentification avec API Key (par défaut)
            auth_data = {
                "client_id": PISTE_API_KEY,
                "client_secret": PISTE_SECRET_KEY,
                "grant_type": "client_credentials",
                "scope": "openid"
            }
            
            if verbose:
                print(f"API Key: {PISTE_API_KEY}")
                print(f"Secret Key: {PISTE_SECRET_KEY[:4]}{'*' * (len(PISTE_SECRET_KEY) - 8)}{PISTE_SECRET_KEY[-4:]}")
        
        if verbose:
            print("\nEnvoi de la requête d'authentification...")
            
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
            
        response = requests.post(PISTE_AUTH_URL, data=auth_data, headers=headers, timeout=10)
        response.raise_for_status()
        
        auth_result = response.json()
        token = auth_result.get("access_token")
        
        # Token expiration (default 30min)
        expires_in = auth_result.get("expires_in", 1800)
        token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        if verbose:
            print("\nAuthentification réussie!")
            print(f"Token: {token[:10]}...{token[-10:] if len(token) > 20 else ''}")
            print(f"Expiration: {expires_in} secondes ({token_expiry.strftime('%H:%M:%S')})")
        
        return {"token": token, "expiry": token_expiry}
        
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP lors de l'authentification: {e}")
        if response:
            print(f"Statut: {response.status_code}")
            print(f"Réponse: {response.text}")
        return None
    except Exception as e:
        print(f"Erreur lors de l'authentification: {e}")
        return None

def explore_api(api_name, token, test_endpoint=None, verbose=False):
    """Explorer une API spécifique et tester les endpoints"""
    if api_name not in API_PROVIDERS:
        print(f"API inconnue: {api_name}")
        print(f"APIs disponibles: {', '.join(API_PROVIDERS.keys())}")
        return False
    
    api_config = API_PROVIDERS[api_name]
    print(f"\n=== Exploration de l'API {api_name.upper()} ===")
    print(f"URL de base: {api_config['base_url']}")
    print(f"Endpoints disponibles:")
    
    for i, endpoint in enumerate(api_config['endpoints']):
        print(f"  {i+1}. {endpoint['method']} {endpoint['path']}")
        print(f"     {endpoint['description']}")
    
    # Test d'un endpoint spécifique
    if test_endpoint is not None:
        try:
            endpoint_index = int(test_endpoint) - 1
            if 0 <= endpoint_index < len(api_config['endpoints']):
                endpoint = api_config['endpoints'][endpoint_index]
                test_api_endpoint(api_config['base_url'], endpoint, token, verbose)
            else:
                print(f"Numéro d'endpoint invalide. Doit être entre 1 et {len(api_config['endpoints'])}")
        except ValueError:
            print(f"Erreur: '{test_endpoint}' n'est pas un numéro d'endpoint valide")
    
    return True

def test_api_endpoint(base_url, endpoint, token, verbose=False):
    """Tester un endpoint d'API spécifique"""
    print(f"\n=== Test de l'endpoint {endpoint['method']} {endpoint['path']} ===")
    
    url = f"{base_url}{endpoint['path']}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        if endpoint['method'] == 'GET':
            if verbose:
                print(f"Requête GET vers {url}")
                print(f"Headers: {headers}")
            
            response = requests.get(url, headers=headers)
        else:  # POST
            # Données de test basiques pour les endpoints POST
            test_payload = {}
            if "code" in endpoint['path']:
                test_payload = {
                    "recherche": {
                        "champ": "travail",
                        "pageNumber": 1,
                        "pageSize": 1
                    }
                }
            elif "juri" in endpoint['path']:
                test_payload = {
                    "recherche": {
                        "champ": "contrat",
                        "pageNumber": 1,
                        "pageSize": 1
                    }
                }
            elif "legi" in endpoint['path']:
                test_payload = {
                    "recherche": {
                        "champ": "environnement",
                        "pageNumber": 1,
                        "pageSize": 1
                    }
                }
            
            if verbose:
                print(f"Requête POST vers {url}")
                print(f"Headers: {headers}")
                print(f"Payload: {json.dumps(test_payload, indent=2)}")
            
            response = requests.post(url, headers=headers, json=test_payload)
        
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Succès! Statut: {response.status_code}")
        
        # Afficher un aperçu de la réponse
        result_preview = json.dumps(result, indent=2, ensure_ascii=False)
        if len(result_preview) > 500:
            result_preview = result_preview[:500] + "..."
        print(f"Aperçu de la réponse:\n{result_preview}")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP: {e}")
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test de l'endpoint: {e}")
        return False

def list_all_apis():
    """Lister toutes les APIs disponibles"""
    print("\n=== APIs disponibles sur la plateforme PISTE ===")
    for api_name, api_config in API_PROVIDERS.items():
        print(f"- {api_name.upper()}: {len(api_config['endpoints'])} endpoints")
        for endpoint in api_config['endpoints']:
            print(f"  • {endpoint['method']} {endpoint['path']}")
            print(f"    {endpoint['description']}")
    
    print("\nNote: Cette liste n'est pas exhaustive et peut être incomplète.")
    print("Pour une liste complète, consultez la documentation officielle de PISTE.")

def main():
    parser = argparse.ArgumentParser(description="Explorateur d'APIs PISTE")
    parser.add_argument("--api", help="Nom de l'API à explorer (ex: legifrance, entreprise)")
    parser.add_argument("--endpoint", help="Numéro de l'endpoint à tester (1, 2, etc.)")
    parser.add_argument("--list", action="store_true", help="Lister toutes les APIs disponibles")
    parser.add_argument("--verbose", action="store_true", help="Mode verbeux avec plus de détails")
    parser.add_argument("--auth", choices=["apikey", "oauth"], default="apikey",
                        help="Méthode d'authentification (apikey ou oauth)")
    
    args = parser.parse_args()
    
    if args.list:
        list_all_apis()
        return 0
    
    # Vérifier les identifiants selon la méthode choisie
    if args.auth.lower() == "oauth":
        if not PISTE_OAUTH_CLIENT_ID:
            print("⚠️ Erreur: L'identifiant OAuth n'est pas configuré.")
            print("Veuillez définir la variable d'environnement PISTE_OAUTH_CLIENT_ID.")
            return 1
    else:  # apikey
        if not PISTE_API_KEY or not PISTE_SECRET_KEY:
            print("⚠️ Erreur: Les clés d'API PISTE ne sont pas configurées.")
            print("Veuillez définir les variables d'environnement PISTE_API_KEY et PISTE_SECRET_KEY.")
            return 1
    
    # Obtenir un token avec la méthode d'authentification spécifiée
    auth_result = get_token(args.auth, args.verbose)
    if not auth_result:
        print("❌ Erreur: Impossible d'obtenir un token d'authentification.")
        return 1
    
    token = auth_result['token']
    
    if args.api:
        explore_api(args.api, token, args.endpoint, args.verbose)
    else:
        print("Veuillez spécifier une API à explorer avec --api ou lister toutes les APIs avec --list")
        print("Exemple: python explore_piste_apis.py --api legifrance")
        print("Pour lister toutes les APIs: python explore_piste_apis.py --list")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 