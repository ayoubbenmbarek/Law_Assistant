#!/usr/bin/env python3
"""
Script de test complet pour l'API Légifrance
"""

import asyncio
import json
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration directe pour éviter les dépendances
CLIENT_ID = "8687ddca-33a7-47d3-a5b7-970b71a6af92"
CLIENT_SECRET = "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2"
OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"

def get_oauth_token():
    """Obtenir directement un token OAuth sans passer par la classe LegifranceAPI"""
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
    
    print(f"Requesting OAuth token from {OAUTH_URL}")
    print(f"Using client_id: {CLIENT_ID}")
    print(f"Using client_secret: {CLIENT_SECRET[:5]}...{CLIENT_SECRET[-5:]}")
    
    try:
        response = requests.post(OAUTH_URL, data=payload, headers=headers)
        print(f"OAuth response status: {response.status_code}")
        print(f"OAuth response content: {response.text[:200]}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", "N/A")
            
            print(f"✅ Token obtained successfully (expires in {expires_in} seconds)")
            print(f"Token: {token[:10]}...{token[-5:]}")
            
            return token
        else:
            print(f"❌ Failed to get token: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception during OAuth request: {str(e)}")
        return None

def test_get_tables(token, start_year=2022, end_year=2022):
    """Tester la récupération des tables avec le token obtenu"""
    endpoint = f"{LEGIFRANCE_SANDBOX_URL}/consult/getTables"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "startYear": start_year,
        "endYear": end_year
    }
    
    print(f"\nTesting API endpoint: {endpoint}")
    print(f"With payload: {json.dumps(payload)}")
    print(f"Using Authorization: Bearer {token[:10]}...{token[-5:]}")
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✅ Success! Received {len(data)} tables")
                
                # Afficher les détails des 2 premières tables
                for i, table in enumerate(data[:2]):
                    print(f"\nTable {i+1}:")
                    print(f"- ID: {table.get('id', 'N/A')}")
                    print(f"- Title: {table.get('title', 'N/A')}")
                    print(f"- Year: {table.get('year', 'N/A')}")
                    print(f"- Type: {table.get('type', 'N/A')}")
                    print(f"- PDF URL: {table.get('pdfUrl', 'N/A')}")
            else:
                print(f"Unexpected response format: {type(data)}")
                print(f"Content: {json.dumps(data)[:200]}")
            
            return True
        else:
            print(f"❌ Error: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Exception during API request: {str(e)}")
        return False

def main():
    """Fonction principale pour tester l'API Légifrance"""
    print("=== LÉGIFRANCE API TEST ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Obtenir un token directement
    token = get_oauth_token()
    
    if not token:
        print("\n❌ Cannot proceed without a valid token")
        return
    
    # Tester la récupération des tables
    success = test_get_tables(token)
    
    # Résumé
    print("\n=== TEST SUMMARY ===")
    print(f"API test result: {'✅ Success' if success else '❌ Failure'}")

if __name__ == "__main__":
    main()
