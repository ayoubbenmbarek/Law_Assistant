#!/usr/bin/env python3
"""
Script de test de connexion aux APIs Légifrance et JudiLibre
"""

import os
import sys
import requests
import base64
import json
from datetime import datetime, timedelta

# Identifiants OAuth (à remplacer par vos propres identifiants)
CLIENT_ID = os.getenv("PISTE_CLIENT_ID", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
CLIENT_SECRET = os.getenv("PISTE_CLIENT_SECRET", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")

# URLs
OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
JUDILIBRE_BASE_URL = "https://api.piste.gouv.fr/dila/judilibre/v1"

def get_oauth_token():
    """Obtenir un token OAuth en utilisant les identifiants"""
    print("\n=== Authentification à l'API PISTE ===")
    
    # Méthode 1: Basic Auth
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # Corps de la requête
    payload = "grant_type=client_credentials"
    
    try:
        print("Envoi de la requête d'authentification...")
        response = requests.post(OAUTH_URL, headers=headers, data=payload)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 1800)
            token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            print("\n✅ Authentification réussie!")
            print(f"Token: {token[:10]}...{token[-10:]} (masqué)")
            print(f"Expiration: {expires_in} secondes ({token_expiry.strftime('%H:%M:%S')})")
            return token
        else:
            print(f"\n❌ Échec de l'authentification: {response.status_code}")
            print(f"Réponse: {response.text}")
            
            # Tenter la méthode 2 si la méthode 1 échoue
            return get_oauth_token_with_scope()
    except Exception as e:
        print(f"\n❌ Erreur lors de l'authentification: {str(e)}")
        return None

def get_oauth_token_with_scope():
    """Obtenir un token OAuth en spécifiant un scope"""
    print("\nTentative avec scope 'openid'...")
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "openid"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(OAUTH_URL, data=payload, headers=headers)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            
            print("✅ Authentification avec scope réussie!")
            print(f"Token: {token[:10]}...{token[-10:]} (masqué)")
            return token
        else:
            print(f"❌ Échec de l'authentification avec scope: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de l'authentification avec scope: {str(e)}")
        return None

def test_legifrance_api(token):
    """Tester l'API Légifrance avec une requête de recherche"""
    print("\n=== Test de l'API Légifrance ===")
    
    if not token:
        print("❌ Impossible de tester l'API sans token valide")
        return False
    
    # Point d'entrée pour rechercher dans les codes
    endpoint = f"{LEGIFRANCE_BASE_URL}/consult/code"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Recherche dans le Code Civil
    payload = {
        "recherche": {
            "champ": "propriété",
            "pageNumber": 1,
            "pageSize": 5
        },
        "filtres": [
            {
                "name": "CODE",
                "value": "LEGITEXT000006070721"  # Code Civil
            }
        ]
    }
    
    try:
        print(f"Envoi de la requête à {endpoint}")
        response = requests.post(endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            results_count = len(data.get("results", []))
            print(f"✅ Accès à l'API Légifrance réussi!")
            print(f"Nombre de résultats: {results_count}")
            return True
        else:
            print(f"❌ Échec de l'accès à l'API Légifrance: {response.status_code}")
            print(f"Réponse: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la requête à l'API Légifrance: {str(e)}")
        return False

def test_judilibre_api(token):
    """Tester l'API JudiLibre avec une requête de recherche"""
    print("\n=== Test de l'API JudiLibre ===")
    
    if not token:
        print("❌ Impossible de tester l'API sans token valide")
        return False
    
    # Point d'entrée pour rechercher dans la jurisprudence
    endpoint = f"{JUDILIBRE_BASE_URL}/search"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    # Paramètres de recherche
    params = {
        "query": "propriété",
        "date_start": "2020-01-01",
        "date_end": "2023-12-31",
        "page_size": 5
    }
    
    try:
        print(f"Envoi de la requête à {endpoint}")
        response = requests.get(endpoint, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results_count = data.get("total", 0)
            print(f"✅ Accès à l'API JudiLibre réussi!")
            print(f"Nombre de décisions trouvées: {results_count}")
            return True
        else:
            print(f"❌ Échec de l'accès à l'API JudiLibre: {response.status_code}")
            print(f"Réponse: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la requête à l'API JudiLibre: {str(e)}")
        return False

def main():
    """Fonction principale pour tester les APIs"""
    print("=== TEST DE CONNEXION AUX APIS LÉGIFRANCE ET JUDILIBRE ===")
    print(f"Date et heure du test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier les identifiants
    if CLIENT_ID == "votre_client_id" or CLIENT_SECRET == "votre_client_secret":
        print("\n⚠️ Veuillez configurer vos identifiants avant d'exécuter le script:")
        print("1. Définissez les variables d'environnement PISTE_CLIENT_ID et PISTE_CLIENT_SECRET")
        print("2. Ou modifiez directement les variables CLIENT_ID et CLIENT_SECRET dans le script")
        return False
    
    # Obtenir un token d'authentification
    token = get_oauth_token()
    
    if not token:
        print("\n❌ ÉCHEC: Impossible d'obtenir un token d'authentification.")
        return False
    
    # Tester les deux APIs
    legifrance_success = test_legifrance_api(token)
    judilibre_success = test_judilibre_api(token)
    
    # Afficher le résultat global
    print("\n=== RÉSULTAT DU TEST ===")
    if legifrance_success and judilibre_success:
        print("✅ SUCCÈS: Les deux APIs sont accessibles")
        return True
    elif legifrance_success:
        print("⚠️ SUCCÈS PARTIEL: Uniquement l'API Légifrance est accessible")
        return True
    elif judilibre_success:
        print("⚠️ SUCCÈS PARTIEL: Uniquement l'API JudiLibre est accessible") 
        return True
    else:
        print("❌ ÉCHEC: Aucune API n'est accessible")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
