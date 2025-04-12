#!/usr/bin/env python3
"""
Script de démonstration pour l'utilisation des APIs Judilibre et Légifrance
avec des connexions directes (sans dépendances supplémentaires)

Ce script montre comment utiliser les APIs Judilibre et Légifrance avec les
informations d'authentification fournies dans les exemples curl.
"""

import os
import requests
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de l'API Judilibre
JUDILIBRE_KEY_ID = os.getenv("JUDILIBRE_KEY_ID", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
JUDILIBRE_TOKEN = os.getenv("JUDILIBRE_TOKEN", "WnU2HnkvuiQkmt0A9mxcFdcUmf6aIJwWOH9VKd4A3lP8yxFizji8D7")
JUDILIBRE_SANDBOX_URL = os.getenv("JUDILIBRE_SANDBOX_URL", "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0")

# Configuration de l'API Légifrance
LEGIFRANCE_TOKEN = os.getenv("LEGIFRANCE_TOKEN", "LHSkc7y94kZsgEr5xpoKwDRAPudaDUzMovCCuU6fmbYaZ5X4hbRTQX")
LEGIFRANCE_SANDBOX_URL = os.getenv("LEGIFRANCE_SANDBOX_URL", "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app")

async def test_judilibre():
    """Tester l'API Judilibre avec l'export d'un lot"""
    print("\n=== TEST DE L'API JUDILIBRE ===")
    
    # Exemple curl fourni:
    # curl -is -H "accept: application/json" -H "KeyId: 8687ddca-33a7-47d3-a5b7-970b71a6af92" 
    # -H "Authorization: Bearer WnU2HnkvuiQkmt0A9mxcFdcUmf6aIJwWOH9VKd4A3lP8yxFizji8D7" 
    # -X GET "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0/export?location=string&batch=11"
    
    # On reproduit la même requête:
    try:
        endpoint = f"{JUDILIBRE_SANDBOX_URL}/export"
        
        headers = {
            "KeyId": JUDILIBRE_KEY_ID,
            "Authorization": f"Bearer {JUDILIBRE_TOKEN}",
            "accept": "application/json"
        }
        
        params = {
            "location": "string",
            "batch": 11
        }
        
        print("Appel de l'API Judilibre (endpoint /export)...")
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        # Afficher les résultats
        decisions_count = len(result.get("decisions", []))
        print(f"✅ Succès! {decisions_count} décisions obtenues")
        
        # Afficher quelques détails de la première décision (s'il y en a)
        if decisions_count > 0:
            first_decision = result["decisions"][0]
            print("\nPremière décision:")
            print(f"- ID: {first_decision.get('id', 'N/A')}")
            print(f"- Juridiction: {first_decision.get('jurisdiction', 'N/A')}")
            print(f"- Chambre: {first_decision.get('chamber', 'N/A')}")
            print(f"- Numéro: {first_decision.get('number', 'N/A')}")
            print(f"- Date: {first_decision.get('decision_date', 'N/A')}")
            print(f"- Solution: {first_decision.get('solution', 'N/A')}")
            
            # Sauvegarder le résultat complet dans un fichier JSON
            with open("judilibre_export_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                print("\nRésultat complet sauvegardé dans 'judilibre_export_result.json'")
        
        # Recherche simple
        search_endpoint = f"{JUDILIBRE_SANDBOX_URL}/search"
        
        search_params = {
            "query": "propriété",
            "date_start": "2020-01-01",
            "date_end": "2023-12-31",
            "page_size": 5
        }
        
        print("\nRecherche dans Judilibre...")
        search_response = requests.get(search_endpoint, headers=headers, params=search_params)
        search_response.raise_for_status()
        
        search_result = search_response.json()
        search_count = search_result.get("total", 0)
        print(f"✅ Recherche réussie! {search_count} décisions trouvées")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API Judilibre: {str(e)}")
        return False

async def test_legifrance():
    """Tester l'API Légifrance avec la récupération d'une délibération CNIL"""
    print("\n=== TEST DE L'API LÉGIFRANCE ===")
    
    # Exemple curl fourni:
    # curl -is -H "accept: application/json" -H "Content-Type: application/json" 
    # -H "Authorization: Bearer LHSkc7y94kZsgEr5xpoKwDRAPudaDUzMovCCuU6fmbYaZ5X4hbRTQX" 
    # -d "{\"ancienId\":\"MCN97020008A\"}" 
    # -X POST "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app/consult/getCnilWithAncienId"
    
    # On reproduit la même requête:
    try:
        endpoint = f"{LEGIFRANCE_SANDBOX_URL}/consult/getCnilWithAncienId"
        
        headers = {
            "Authorization": f"Bearer {LEGIFRANCE_TOKEN}",
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
        print("\nDétails de la délibération:")
        print(f"- ID: {result.get('id', 'N/A')}")
        print(f"- Ancien ID: {result.get('ancienId', 'N/A')}")
        print(f"- Titre: {result.get('title', 'N/A')}")
        print(f"- Nature: {result.get('nature', 'N/A')}")
        print(f"- Numéro: {result.get('num', 'N/A')}")
        print(f"- Date: {result.get('date', 'N/A')}")
        
        # Sauvegarder le résultat complet dans un fichier JSON
        with open("legifrance_cnil_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            print("\nRésultat complet sauvegardé dans 'legifrance_cnil_result.json'")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API Légifrance: {str(e)}")
        return False

async def main():
    """Fonction principale pour tester les deux APIs"""
    print("=== DÉMONSTRATION DES APIS JUDILIBRE ET LÉGIFRANCE ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Ces tests utilisent les informations d'authentification fournies dans les exemples curl")
    
    # Tester l'API Judilibre
    judilibre_success = await test_judilibre()
    
    # Tester l'API Légifrance
    legifrance_success = await test_legifrance()
    
    # Résumé des tests
    print("\n=== RÉSUMÉ DES TESTS ===")
    print(f"API Judilibre: {'✅ Succès' if judilibre_success else '❌ Échec'}")
    print(f"API Légifrance: {'✅ Succès' if legifrance_success else '❌ Échec'}")
    print()
    
    if judilibre_success and legifrance_success:
        print("🎉 SUCCÈS! Les deux APIs sont fonctionnelles")
    elif judilibre_success or legifrance_success:
        print("⚠️ SUCCÈS PARTIEL: Une seule API est fonctionnelle")
    else:
        print("❌ ÉCHEC: Aucune API n'est fonctionnelle")

if __name__ == "__main__":
    asyncio.run(main()) 