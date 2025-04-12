#!/usr/bin/env python3
"""
Script pour tester la connexion à l'API Légifrance avec l'authentification de base
"""

import os
import sys
import requests
import json
import base64
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Clés d'API
CLIENT_ID = "8687ddca-33a7-47d3-a5b7-970b71a6af92"
CLIENT_SECRET = "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2"

# URLs
OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_TEST_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/consult/code"

def get_oauth_token_basic_auth():
    """Obtenir un token en utilisant l'authentification basique"""
    
    logger.info("Tentative d'obtention d'un token OAuth avec authentification basique...")
    
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
    
    try:
        # Affichage des informations de debug
        logger.info(f"URL d'authentification: {OAUTH_URL}")
        logger.info(f"En-têtes: Authorization: Basic [MASQUÉ]")
        logger.info(f"Corps de la requête: {payload}")
        
        # Envoi de la requête
        response = requests.post(OAUTH_URL, headers=headers, data=payload)
        
        # Affichage de la réponse pour le débogage
        logger.info(f"Statut de la réponse: {response.status_code}")
        logger.info(f"Contenu de la réponse: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            logger.error(f"Échec de l'authentification: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la demande d'authentification: {str(e)}")
        return None

def test_legifrance_api(token):
    """Tester l'accès à l'API Légifrance avec une requête simple"""
    
    if not token:
        logger.error("Impossible de tester l'API sans token valide")
        return False
    
    logger.info("Test de l'API Légifrance...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Requête simple pour récupérer des informations sur le Code Civil
    payload = {
        "path": "/LEGI/CODE/LEGITEXT000006070721",
        "field": "CODE_DESC",
        "operator": "CONTAINS",
        "query": "propriété"
    }
    
    try:
        response = requests.post(LEGIFRANCE_TEST_URL, headers=headers, json=payload)
        
        logger.info(f"Statut de la réponse de l'API: {response.status_code}")
        logger.info(f"Taille de la réponse: {len(response.text)} caractères")
        
        if response.status_code == 200:
            data = response.json()
            articles_count = len(data.get("articles", []))
            logger.info(f"Succès! {articles_count} articles trouvés.")
            return True
        else:
            logger.error(f"Échec de l'accès à l'API: {response.status_code} - {response.text[:200]}...")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la requête à l'API: {str(e)}")
        return False

def get_oauth_token_alternative():
    """Méthode alternative d'obtention du token"""
    
    logger.info("Tentative alternative d'obtention d'un token OAuth...")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    try:
        response = requests.post(OAUTH_URL, headers=headers, data=payload)
        
        logger.info(f"Statut de la réponse: {response.status_code}")
        logger.info(f"Contenu de la réponse: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            logger.error(f"Échec de l'authentification alternative: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la demande d'authentification alternative: {str(e)}")
        return None

def main():
    """Fonction principale"""
    
    print("\n=== TEST DE CONNEXION À L'API LÉGIFRANCE ===\n")
    print(f"Date et heure du test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Client Secret: {CLIENT_SECRET[:5]}...{CLIENT_SECRET[-5:]} (masqué)")
    
    # Méthode 1: Basic Auth
    token = get_oauth_token_basic_auth()
    
    if not token:
        print("\nTentative avec méthode alternative...")
        # Méthode 2: Corps de requête
        token = get_oauth_token_alternative()
    
    if not token:
        print("\n❌ ÉCHEC: Impossible d'obtenir un token d'authentification.")
        print("\nVérifiez que:")
        print("1. Les identifiants API sont corrects")
        print("2. Votre compte PISTE a bien accès à l'API Légifrance")
        print("3. Votre application PISTE est bien configurée")
        return False
    
    print(f"\n✅ Authentification réussie. Token: {token[:10]}...{token[-10:]} (masqué)")
    
    # Test de l'API
    success = test_legifrance_api(token)
    
    if success:
        print("\n✅ Test de l'API Légifrance réussi. Votre connexion fonctionne correctement.")
        return True
    else:
        print("\n❌ ÉCHEC: La connexion à l'API Légifrance a échoué.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 