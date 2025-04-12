#!/usr/bin/env python3
"""
Test d'authentification à la plateforme PISTE suivant strictement la documentation officielle
"""

import os
import sys
import requests
import json
import logging
import urllib.parse
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Clés d'API
CLIENT_ID = "8687ddca-33a7-47d3-a5b7-970b71a6af92"
CLIENT_SECRET = "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2"

# URLs
OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

def test_auth_official():
    """
    Test d'authentification suivant exactement l'exemple de la documentation officielle
    """
    print("\n=== TEST D'AUTHENTIFICATION OFFICIEL PISTE ===\n")
    print(f"Date et heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Client Secret: {CLIENT_SECRET[:5]}...{CLIENT_SECRET[-5:]} (masqué)")
    print(f"URL d'authentification: {OAUTH_URL}")
    
    # Construction du payload en x-www-form-urlencoded
    payload = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    })
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    print("\nDétails de la requête:")
    print(f"Headers: {headers}")
    print(f"Payload: grant_type=client_credentials&client_id={CLIENT_ID}&client_secret=XXXXX")
    
    try:
        response = requests.post(OAUTH_URL, data=payload, headers=headers)
        
        print(f"\nCode de statut de la réponse: {response.status_code}")
        print(f"En-têtes de la réponse: {response.headers}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("\n✅ Authentification réussie!")
            print(f"Access Token: {token_data.get('access_token')[:10]}...{token_data.get('access_token')[-10:]} (masqué)")
            print(f"Token Type: {token_data.get('token_type')}")
            print(f"Expires In: {token_data.get('expires_in')} secondes")
            print(f"Scope: {token_data.get('scope')}")
            return True
        else:
            print(f"\n❌ Échec de l'authentification: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
    except Exception as e:
        print(f"\n❌ Erreur lors de la requête: {str(e)}")
        return False

def test_auth_with_scope():
    """
    Test d'authentification avec un scope spécifique
    """
    print("\n=== TEST AVEC SCOPE SPÉCIFIQUE ===\n")
    
    # Construction du payload en x-www-form-urlencoded
    payload = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "openid"  # Scope spécifique
    })
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    print("Requête avec scope 'openid'...")
    
    try:
        response = requests.post(OAUTH_URL, data=payload, headers=headers)
        
        print(f"Code de statut: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authentification avec scope réussie!")
            print(f"Scope reçu: {token_data.get('scope')}")
            return True
        else:
            print(f"❌ Échec: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_auth_with_basic():
    """
    Test d'authentification avec HTTP Basic Auth
    """
    print("\n=== TEST AVEC AUTHENTIFICATION HTTP BASIC ===\n")
    
    import base64
    
    # Préparation des en-têtes Basic Auth
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # Corps de la requête
    payload = "grant_type=client_credentials"
    
    print("Requête avec authentication HTTP Basic...")
    
    try:
        response = requests.post(OAUTH_URL, headers=headers, data=payload)
        
        print(f"Code de statut: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authentification Basic réussie!")
            return True
        else:
            print(f"❌ Échec: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def main():
    """Fonction principale"""
    
    # Méthode officielle
    official_success = test_auth_official()
    
    # Si la méthode officielle échoue, essayons avec un scope
    if not official_success:
        scope_success = test_auth_with_scope()
        
        # Si ça échoue encore, essayons avec Basic Auth
        if not scope_success:
            basic_success = test_auth_with_basic()
            
            if not basic_success:
                print("\n❌ ÉCHEC: Toutes les méthodes d'authentification ont échoué.")
                print("\nVérifiez que:")
                print("1. Les identifiants API sont corrects et actifs")
                print("2. Votre compte PISTE a bien accès à l'API")
                print("3. Votre application est bien configurée sur PISTE")
                return False
    
    print("\n✅ Test d'authentification réussi avec au moins une méthode.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 