#!/usr/bin/env python3
"""
Script de test pour l'API Légifrance sans dépendance à la structure 'app'
Ce script est une version simplifiée qui montre comment utiliser l'API Légifrance
avec authentification OAuth en utilisant client_id et client_secret.
"""

import os
import requests
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, Union

# Charger les variables d'environnement
load_dotenv()

# API configuration
LEGIFRANCE_API_KEY = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
LEGIFRANCE_API_SECRET = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")
LEGIFRANCE_API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
LEGIFRANCE_API_SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
LEGIFRANCE_AUTH_URL = "https://oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_SANDBOX_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

class LegifranceAPI:
    """Client pour l'API Légifrance PISTE/DILA organisé selon la documentation Swagger"""
    
    def __init__(self, use_sandbox: bool = True):
        """
        Initialise le client API Légifrance
        
        Args:
            use_sandbox: Utiliser l'environnement sandbox (par défaut) ou production
        """
        self.api_key = LEGIFRANCE_API_KEY
        self.api_secret = LEGIFRANCE_API_SECRET
        self.token = ""
        self.base_url = LEGIFRANCE_API_SANDBOX_URL if use_sandbox else LEGIFRANCE_API_BASE_URL
        self.auth_url = LEGIFRANCE_SANDBOX_AUTH_URL if use_sandbox else LEGIFRANCE_AUTH_URL
        self.token_expiry = None
        self.use_sandbox = use_sandbox
        
        if not (self.api_key and self.api_secret):
            print("ATTENTION: Clés d'API Légifrance non configurées. Utilisation de données de test uniquement.")
        
    async def authenticate(self):
        """Authentification à l'API Légifrance pour obtenir un token"""
        # Si nous avons un token valide, nous l'utilisons directement
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        try:
            auth_data = {
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "grant_type": "client_credentials",
                "scope": "openid"
            }
            
            response = requests.post(self.auth_url, data=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.token = auth_result.get("access_token")
            
            # Token expires in (default 30min)
            expires_in = auth_result.get("expires_in", 1800)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"Authentification Légifrance réussie. Token expire dans {expires_in} secondes.")
            return self.token
            
        except requests.exceptions.HTTPError as e:
            print(f"Échec d'authentification à l'API Légifrance (HTTP Error): {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Détails de l'erreur: {e.response.text}")
            raise
        except Exception as e:
            print(f"Échec d'authentification à l'API Légifrance: {str(e)}")
            raise

    async def _make_api_request(self, endpoint: str, method: str = "POST", payload: Dict = None) -> Any:
        """
        Méthode interne pour effectuer des requêtes API avec gestion d'authentification
        
        Args:
            endpoint: Endpoint API à appeler
            method: Méthode HTTP (GET, POST)
            payload: Données JSON pour la requête
            
        Returns:
            Réponse JSON de l'API
        """
        await self.authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        full_url = f"{self.base_url}/{endpoint}"
        
        try:
            print(f"Appel de l'API: {endpoint}")
            if method.upper() == "GET":
                response = requests.get(full_url, headers=headers, params=payload)
            else:
                response = requests.post(full_url, headers=headers, json=payload)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            print(f"Erreur HTTP {e.response.status_code} pour {endpoint}: {str(e)}")
            raise
        except Exception as e:
            print(f"Erreur lors de l'appel à {endpoint}: {str(e)}")
            raise

    async def get_cnil_with_ancien_id(self, ancien_id: str) -> Dict[str, Any]:
        """
        Récupère un texte du fond CNIL en fonction de son Ancien ID
        
        Args:
            ancien_id: Ancien identifiant de la délibération CNIL
            
        Returns:
            Dictionnaire contenant les détails de la délibération
        """
        payload = {
            "ancienId": ancien_id
        }
        
        try:
            return await self._make_api_request("consult/getCnilWithAncienId", "POST", payload)
        except Exception as e:
            print(f"Échec de récupération de la délibération CNIL {ancien_id}: {str(e)}")
            raise

    async def get_tables(self, start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """
        Récupère l'ensemble des tables annuelles pour une période donnée
        
        Args:
            start_year: Année de début (optionnel)
            end_year: Année de fin (optionnel)
            
        Returns:
            Résultat de l'API (liste des tables ou dictionnaire contenant les tables)
        """
        # Format exact comme montré dans l'interface Swagger
        # S'assurer que les années sont bien des entiers
        payload = {}
        if start_year is not None:
            payload["startYear"] = int(start_year)
        if end_year is not None:
            payload["endYear"] = int(end_year)
            
        # Imprimer le payload exact pour vérification
        print(f"Payload de requête: {json.dumps(payload)}")
            
        try:
            # Afficher l'URL complète et les détails de la requête pour le débogage
            full_url = f"{self.base_url}/consult/getTables"
            print(f"URL de requête: {full_url}")
            
            return await self._make_api_request("consult/getTables", "POST", payload)
        except requests.exceptions.HTTPError as e:
            print(f"Erreur HTTP lors de la récupération des tables: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Détails de l'erreur: {e.response.text}")
            raise
        except Exception as e:
            print(f"Échec de récupération des tables: {str(e)}")
            raise

async def test_cnil_api():
    """Test de récupération d'une délibération CNIL"""
    print("\n=== TEST DE RÉCUPÉRATION CNIL ===")
    api = LegifranceAPI(use_sandbox=True)
    
    try:
        # ID de test pour une délibération CNIL
        ancien_id = "MCN97020008A"
        result = await api.get_cnil_with_ancien_id(ancien_id)
        
        print(f"✅ Succès! Délibération CNIL obtenue")
        
        # Sauvegarder le résultat
        with open("legifrance_cnil_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            print("Résultat complet sauvegardé dans 'legifrance_cnil_result.json'")
            
        # Afficher quelques informations
        if result.get("text"):
            text_data = result.get("text", {})
            print("\nDétails de la délibération:")
            print(f"- ID: {text_data.get('id', 'N/A')}")
            print(f"- Ancien ID: {text_data.get('ancienId', 'N/A')}")
            print(f"- Titre: {text_data.get('titre', 'N/A') or text_data.get('title', 'N/A')}")
            print(f"- Nature: {text_data.get('nature', 'N/A')}")
        else:
            print("\nDétails de la délibération:")
            print(f"- ID: {result.get('id', 'N/A')}")
            print(f"- Ancien ID: {result.get('ancienId', 'N/A')}")
            print(f"- Titre: {result.get('title', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test CNIL: {str(e)}")
        return False

async def test_tables():
    """Test de récupération des tables annuelles"""
    print("\n=== TEST DE RÉCUPÉRATION DES TABLES ===")
    api = LegifranceAPI(use_sandbox=True)
    
    try:
        # Années spécifiques mentionnées par l'utilisateur
        print("Recherche des tables pour la période 2012-2017...")
        start_year = 1900
        end_year = 2025
        print(f"Paramètres: startYear={start_year}, endYear={end_year}")
        
        # Faire la requête
        result = await api.get_tables(start_year=start_year, end_year=end_year)
        
        print(f"✅ Succès! Tables annuelles récupérées")
        print(f"Type de réponse: {type(result)}")
        
        # Sauvegarder le résultat
        with open("legifrance_tables_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            print("Résultat complet sauvegardé dans 'legifrance_tables_result.json'")
        
        # Afficher la structure exacte de la réponse pour déboguer
        print("\nStructure de la réponse:")
        for key in result:
            value = result[key]
            if isinstance(value, list):
                print(f"- {key}: Liste avec {len(value)} éléments")
            else:
                print(f"- {key}: {value}")
            
        # Afficher des informations détaillées sur les tables si elles existent
        if "tables" in result and isinstance(result["tables"], list):
            tables = result["tables"]
            print(f"\nNombre de tables: {len(tables)}")
            
            if tables:
                print(f"Tables trouvées:")
                for i, table in enumerate(tables[:5]):  # Limiter à 5 tables pour l'affichage
                    print(f"\nTable {i+1}:")
                    for key, value in table.items():
                        print(f"- {key}: {value}")
            
            print(f"Nombre total de résultats: {result.get('totalNbResult', 0)}")
        else:
            print("\nAucune table trouvée dans la période spécifiée ou format inattendu")
            print("Contenu de la réponse brute:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:500] + "...")  # Afficher le début du JSON
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test des tables: {str(e)}")
        return False

async def main():
    """Fonction principale"""
    print("=== TEST DE L'API LÉGIFRANCE ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Key: {LEGIFRANCE_API_KEY}")
    print(f"API Secret: {LEGIFRANCE_API_SECRET[:5]}...{LEGIFRANCE_API_SECRET[-5:]} (masqué)")
    
    # Tests des différentes parties de l'API
    cnil_success = await test_cnil_api()
    tables_success = await test_tables()
    
    # Récapitulatif
    print("\n=== RÉCAPITULATIF ===")
    print(f"Test CNIL: {'✅ Succès' if cnil_success else '❌ Échec'}")
    print(f"Test Tables: {'✅ Succès' if tables_success else '❌ Échec'}")
    
    if cnil_success and tables_success:
        print("\n🎉 TOUS LES TESTS ONT RÉUSSI!")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")

if __name__ == "__main__":
    asyncio.run(main()) 