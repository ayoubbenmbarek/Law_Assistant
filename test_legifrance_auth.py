#!/usr/bin/env python3
"""
Script de test d'authentification à l'API Légifrance
"""

import asyncio
from dotenv import load_dotenv
from loguru import logger

# Charger les variables d'environnement
load_dotenv()

async def main():
    # Importer la classe LegifranceAPI
    from app.data.legifrance_api import LegifranceAPI
    
    # Afficher la version du module
    print(f"Testing authentication for LegifranceAPI")
    
    # Initialiser le client Légifrance
    legifrance = LegifranceAPI(use_sandbox=True)  # Assurez-vous d'utiliser le bon environnement
    
    # Afficher les paramètres de configuration
    print(f"API Key: {legifrance.api_key[:5]}...{legifrance.api_key[-5:] if legifrance.api_key else 'None'}")
    print(f"API Secret: {legifrance.api_secret[:5]}...{legifrance.api_secret[-5:] if legifrance.api_secret else 'None'}")
    print(f"Base URL: {legifrance.base_url}")
    
    # Tester l'authentification
    print("Attempting authentication...")
    try:
        token = await legifrance.authenticate()
        print(f"✅ Authentication successful!")
        print(f"Token: {token[:10]}...{token[-5:]}")
        
        # Tester une requête simple
        print("\nTesting a simple API request...")
        endpoint = f"{legifrance.base_url}/consult/getTables"
        import requests
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "startYear": 2022,
            "endYear": 2022
        }
        
        response = requests.post(endpoint, headers=headers, json=payload)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Received {len(data) if isinstance(data, list) else 'non-list'} response")
        else:
            print(f"Error: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
