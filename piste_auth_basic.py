#!/usr/bin/env python3
"""
Script simplifié d'authentification à l'API PISTE avec Basic Auth
"""

import os
import sys
import base64
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# API configuration
PISTE_API_KEY = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
PISTE_SECRET_KEY = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")
PISTE_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

def test_auth_basic():
    """Test l'authentification à l'API PISTE avec Basic Auth"""
    print("=== Test d'authentification à l'API PISTE avec Basic Auth ===")
    
    # Préparer l'en-tête Basic Auth
    credentials = f"{PISTE_API_KEY}:{PISTE_SECRET_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    # Préparer les données
    auth_data = {
        "grant_type": "client_credentials"
    }
    
    # Préparer les en-têtes
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print(f"URL d'authentification: {PISTE_AUTH_URL}")
    print(f"En-tête Authorization: Basic {encoded_credentials[:10]}...{encoded_credentials[-10:]}")
    
    try:
        # Effectuer la requête
        print("\nRequête HTTP en cours...")
        response = requests.post(
            PISTE_AUTH_URL, 
            headers=headers,
            data=auth_data,
            timeout=10
        )
        
        print(f"\nCode de statut: {response.status_code}")
        
        if response.status_code == 200:
            auth_result = response.json()
            token = auth_result.get("access_token")
            
            print("\nAuthentification réussie!")
            print(f"Token: {token[:10]}...{token[-10:]}")
            print(f"Réponse complète: {auth_result}")
            return token
        else:
            print(f"\nÉchec de l'authentification. Code de statut: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"\nErreur lors de l'authentification: {str(e)}")
        return None

if __name__ == "__main__":
    token = test_auth_basic()
    
    print("\n=== Résultat ===")
    if token:
        print("🟢 Test d'authentification réussi!")
        sys.exit(0)
    else:
        print("🔴 Test d'authentification échoué!")
        sys.exit(1) 