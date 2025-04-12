#!/usr/bin/env python3
"""
Script de test de l'API Légifrance (endpoint getTables)
"""
import requests
import base64
import json
from datetime import datetime

# Identifiants
CLIENT_ID = "8687ddca-33a7-47d3-a5b7-970b71a6af92"
CLIENT_SECRET = "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2"

# URLs
OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_BASE_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"

def get_oauth_token():
    """Obtenir un token OAuth pour l'API Légifrance"""
    print("\n=== Obtention du token OAuth ===")
    
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
            print(f"✅ Token OAuth obtenu: {token[:10]}...{token[-5:]}")
            return token
        else:
            print(f"❌ Échec d'obtention du token: {response.status_code}")
            print(f"Message: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None

def test_get_tables(token):
    """Tester le point d'entrée /consult/getTables de l'API Légifrance"""
    print("\n=== Test du point d'entrée /consult/getTables ===")
    endpoint = f"{LEGIFRANCE_BASE_URL}/consult/getTables"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Même payload que dans l'exemple curl
    payload = {
        "endYear": 2017,
        "startYear": 2012
    }
    
    try:
        print(f"Requête POST vers {endpoint}")
        print(f"Payload: {json.dumps(payload)}")
        response = requests.post(endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès! Tables obtenues:")
            
            # Afficher un résumé des résultats
            if isinstance(data, list):
                print(f"Nombre de tables: {len(data)}")
                
                # Afficher le détail des 3 premières tables (s'il y en a)
                for i, table in enumerate(data[:3]):
                    print(f"\nTable {i+1}:")
                    print(f"- Année: {table.get('year', 'N/A')}")
                    print(f"- Type: {table.get('type', 'N/A')}")
                    print(f"- ID: {table.get('id', 'N/A')}")
                    print(f"- Titre: {table.get('title', 'N/A')}")
            else:
                print(f"Format de réponse: {type(data)}")
            
            return True
        else:
            print(f"❌ Échec (code {response.status_code}): {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def main():
    """Fonction principale pour tester l'API Légifrance"""
    print("=== TEST DE L'API LÉGIFRANCE (ENDPOINT getTables) ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL de base: {LEGIFRANCE_BASE_URL}")
    
    # Obtenir un token
    token = get_oauth_token()
    
    if not token:
        print("\n❌ Impossible de poursuivre sans token valide")
        return
    
    # Tester le point d'entrée getTables
    success = test_get_tables(token)
    
    # Résumé
    print("\n=== RÉSUMÉ DU TEST ===")
    print(f"GetTables endpoint: {'✅ Réussi' if success else '❌ Échec'}")
    print(f"\n{'✅ SUCCÈS' if success else '❌ ÉCHEC'}: Test de l'API Légifrance")

if __name__ == "__main__":
    main()
