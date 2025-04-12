#!/usr/bin/env python3
"""
Script de test d'authentification à l'API PISTE
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# API configuration
PISTE_API_KEY = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
PISTE_SECRET_KEY = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")
PISTE_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

def test_auth_verbose():
    """Test l'authentification à l'API PISTE avec affichage détaillé"""
    print("=== Test d'authentification à l'API PISTE ===")
    print(f"URL d'authentification: {PISTE_AUTH_URL}")
    print(f"Clé API: {PISTE_API_KEY}")
    print(f"Secret API: {PISTE_SECRET_KEY[:4]}{'*' * (len(PISTE_SECRET_KEY) - 8)}{PISTE_SECRET_KEY[-4:]}")
    
    auth_data = {
        "client_id": PISTE_API_KEY,
        "client_secret": PISTE_SECRET_KEY,
        "grant_type": "client_credentials",
        "scope": "openid"
    }
    
    print("\nEnvoi de la requête d'authentification...")
    print(f"Données envoyées: {auth_data}")
    
    try:
        # Activer les logs de debug pour requests
        import logging
        from http.client import HTTPConnection
        HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        
        # Effectuer la requête avec vérification SSL désactivée pour le debug
        print("\nRequête HTTP en cours...")
        response = requests.post(
            PISTE_AUTH_URL, 
            data=auth_data,
            verify=False,  # Désactiver la vérification SSL pour le debugging
            timeout=10     # Timeout après 10 secondes
        )
        
        print(f"\nCode de statut: {response.status_code}")
        print(f"Headers de réponse: {dict(response.headers)}")
        
        if response.status_code == 200:
            auth_result = response.json()
            token = auth_result.get("access_token")
            expires_in = auth_result.get("expires_in", 1800)
            token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            print("\nAuthentification réussie!")
            print(f"Token: {token[:10]}...{token[-10:]}")
            print(f"Expiration: {expires_in} secondes ({token_expiry.strftime('%H:%M:%S')})")
            print(f"Réponse complète: {auth_result}")
            return True
        else:
            print(f"\nÉchec de l'authentification. Code de statut: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\nErreur de connexion: {str(e)}")
        print("Vérifiez votre connexion internet et les paramètres du serveur proxy si nécessaire.")
        return False
    except requests.exceptions.Timeout as e:
        print(f"\nTimeout de la requête: {str(e)}")
        print("Le serveur prend trop de temps pour répondre.")
        return False
    except requests.exceptions.SSLError as e:
        print(f"\nErreur SSL: {str(e)}")
        print("Problème avec la vérification du certificat SSL.")
        return False
    except Exception as e:
        print(f"\nErreur inattendue: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Désactiver les warnings de sécurité pour le debugging
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    result = test_auth_verbose()
    print("\n=== Résultat ===")
    if result:
        print("🟢 Test d'authentification réussi!")
        sys.exit(0)
    else:
        print("🔴 Test d'authentification échoué!")
        sys.exit(1) 