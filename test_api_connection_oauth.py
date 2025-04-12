#!/usr/bin/env python3
"""
Script de démonstration pour l'utilisation des APIs Judilibre et Légifrance
avec des connexions directes (sans dépendances supplémentaires)

Ce script montre comment utiliser les APIs Judilibre et Légifrance avec
authentification OAuth en utilisant client_id et client_secret.
"""

import os
import requests
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlencode
import base64

# Charger les variables d'environnement
load_dotenv()

# Informations d'authentification
CLIENT_ID = "8687ddca-33a7-47d3-a5b7-970b71a6af92"
CLIENT_SECRET = "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2"
OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
CALLBACK_URL = "https://piste.gouv.fr/cb"

# URLs des APIs
JUDILIBRE_SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"
LEGIFRANCE_SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"

def get_oauth_token():
    """Obtenir un token OAuth pour l'authentification aux APIs PISTE"""
    # Utilisation du client_credentials flow
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
        print("Obtention d'un token OAuth...")
        response = requests.post(OAUTH_URL, data=payload, headers=headers)
        
        print(f"Code de statut: {response.status_code}")
        print(f"Réponse: {response.text[:200]}")
        
        response.raise_for_status()
        
        token_data = response.json()
        token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", "N/A")
        
        print(f"✅ Token OAuth obtenu avec succès (expire dans {expires_in} secondes)")
        if token:
            print(f"   Token: {token[:10]}...{token[-5:]}")
        
        return token
    except Exception as e:
        print(f"❌ Échec d'obtention du token OAuth: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails de l'erreur: {e.response.text}")
        return None

async def test_judilibre(token):
    """Tester l'API Judilibre avec recherche de décisions"""
    print("\n=== TEST DE L'API JUDILIBRE ===")
    
    try:
        endpoint = f"{JUDILIBRE_SANDBOX_URL}/search"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        params = {
            "query": "propriété",
            "date_start": "2020-01-01",
            "date_end": "2023-12-31",
            "page_size": 5
        }
        
        print("Appel de l'API Judilibre (endpoint /search)...")
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        # Afficher les résultats
        decisions_count = result.get("total", 0)
        print(f"✅ Succès! {decisions_count} décisions trouvées")
        
        # Afficher quelques détails de la première décision (s'il y en a)
        if result.get("results") and len(result.get("results", [])) > 0:
            first_decision = result["results"][0]
            print("\nPremière décision:")
            print(f"- ID: {first_decision.get('id', 'N/A')}")
            print(f"- Juridiction: {first_decision.get('jurisdiction', 'N/A')}")
            print(f"- Chambre: {first_decision.get('chamber', 'N/A')}")
            print(f"- Numéro: {first_decision.get('number', 'N/A')}")
            print(f"- Date: {first_decision.get('decision_date', 'N/A')}")
            
            # Sauvegarder le résultat complet dans un fichier JSON
            with open("judilibre_search_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                print("\nRésultat complet sauvegardé dans 'judilibre_search_result.json'")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API Judilibre: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails de l'erreur: {e.response.text}")
        return False

async def test_legifrance(token):
    """Tester l'API Légifrance avec la récupération d'une délibération CNIL"""
    print("\n=== TEST DE L'API LÉGIFRANCE ===")
    
    try:
        endpoint = f"{LEGIFRANCE_SANDBOX_URL}/consult/getCnilWithAncienId"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "ancienId": "MCN97020008A"
        }
        
        print("Appel de l'API Légifrance (endpoint /consult/getCnilWithAncienId)...")
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Afficher les résultats
        print(f"✅ Succès! Délibération CNIL obtenue")
        
        if result.get("text"):
            text_data = result.get("text", {})
            print("\nDétails de la délibération:")
            print(f"- ID: {text_data.get('id', 'N/A')}")
            print(f"- Ancien ID: {text_data.get('ancienId', 'N/A')}")
            print(f"- Titre: {text_data.get('titre', 'N/A') or text_data.get('title', 'N/A')}")
            print(f"- Nature: {text_data.get('nature', 'N/A')}")
            print(f"- Numéro: {text_data.get('num', 'N/A')}")
        else:
            print("\nDétails de la délibération:")
            print(f"- ID: {result.get('id', 'N/A')}")
            print(f"- Ancien ID: {result.get('ancienId', 'N/A')}")
            print(f"- Titre: {result.get('title', 'N/A')}")
            print(f"- Nature: {result.get('nature', 'N/A')}")
            print(f"- Numéro: {result.get('num', 'N/A')}")
        
        # Sauvegarder le résultat
        with open("legifrance_cnil_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            print("\nRésultat complet sauvegardé dans 'legifrance_cnil_result.json'")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API Légifrance: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails de l'erreur: {e.response.text}")
        return False

async def main():
    """Fonction principale pour tester les deux APIs"""
    print("=== DÉMONSTRATION DES APIS JUDILIBRE ET LÉGIFRANCE ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Client Secret: {CLIENT_SECRET[:5]}...{CLIENT_SECRET[-5:]} (masqué)")
    
    # Obtenir un token OAuth
    token = get_oauth_token()
    
    if not token:
        print("\n❌ Impossible de continuer sans token d'authentification valide.")
        return
    
    # Tester l'API Légifrance
    legifrance_success = await test_legifrance(token)
    
    # Tester l'API Judilibre
    judilibre_success = await test_judilibre(token)
    
    # Résumé des tests
    print("\n=== RÉSUMÉ DES TESTS ===")
    print(f"API Légifrance: {'✅ Succès' if legifrance_success else '❌ Échec'}")
    print(f"API Judilibre: {'✅ Succès' if judilibre_success else '❌ Échec'}")
    print()
    
    if legifrance_success and judilibre_success:
        print("🎉 SUCCÈS! Les deux APIs sont fonctionnelles")
    elif legifrance_success or judilibre_success:
        print("⚠️ SUCCÈS PARTIEL: Une seule API est fonctionnelle")
    else:
        print("❌ ÉCHEC: Aucune API n'est fonctionnelle")

if __name__ == "__main__":
    asyncio.run(main())
