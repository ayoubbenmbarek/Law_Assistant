#!/usr/bin/env python3
"""
Script pour tester la connexion avec authentification HTTP Basic et les nouveaux identifiants
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

# Nouveaux identifiants OAuth
CLIENT_ID = "8687ddca-33a7-47d3-a5b7-970b71a6af92"
CLIENT_SECRET = "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2"

# URLs d'authentification et d'API
OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
JUDILIBRE_BASE_URL = "https://api.piste.gouv.fr/dila/judilibre/v1"

def get_oauth_token_basic_auth():
    """Obtenir un token en utilisant l'authentification HTTP Basic"""
    
    logger.info("Tentative d'obtention d'un token OAuth avec authentification Basic...")
    
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
        logger.info(f"URL d'authentification: {OAUTH_URL}")
        logger.info(f"En-têtes: Authorization: Basic [MASQUÉ]")
        logger.info(f"Corps de la requête: {payload}")
        
        response = requests.post(OAUTH_URL, headers=headers, data=payload)
        
        logger.info(f"Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info(f"Token obtenu avec succès. Expire dans {token_data.get('expires_in', 'N/A')} secondes")
            return token_data["access_token"]
        else:
            logger.error(f"Échec de l'authentification: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la demande d'authentification: {str(e)}")
        return None

def get_oauth_token_with_scope():
    """Obtenir un token en spécifiant un scope"""
    
    logger.info("Tentative d'obtention d'un token OAuth avec scope 'openid'...")
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "openid"  # Ajout d'un scope
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(OAUTH_URL, data=payload, headers=headers)
        
        logger.info(f"Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info(f"Token obtenu avec succès avec scope. Scope: {token_data.get('scope')}")
            return token_data["access_token"]
        else:
            logger.error(f"Échec de l'authentification avec scope: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la demande d'authentification avec scope: {str(e)}")
        return None

def test_legifrance_api(token):
    """Tester l'accès à l'API Légifrance avec une requête simple"""
    
    if not token:
        logger.error("Impossible de tester l'API sans token valide")
        return False
    
    logger.info("Test de l'API Légifrance...")
    
    # Recherche simple dans le Code Civil
    endpoint = f"{LEGIFRANCE_BASE_URL}/consult/code"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "path": "/LEGI/CODE/LEGITEXT000006070721", # Code Civil
        "field": "CODE_DESC",
        "operator": "CONTAINS",
        "query": "propriété"
    }
    
    try:
        logger.info(f"Envoi de la requête à {endpoint}")
        response = requests.post(endpoint, headers=headers, json=payload)
        
        logger.info(f"Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles_count = len(data.get("articles", []))
            logger.info(f"Accès à l'API Légifrance réussi. {articles_count} articles trouvés.")
            return True
        else:
            logger.error(f"Échec de l'accès à l'API Légifrance: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la requête à l'API Légifrance: {str(e)}")
        return False

def test_judilibre_api(token):
    """Tester l'accès à l'API JudiLibre avec une requête simple"""
    
    if not token:
        logger.error("Impossible de tester l'API sans token valide")
        return False
    
    logger.info("Test de l'API JudiLibre...")
    
    # Recherche simple de jurisprudence
    endpoint = f"{JUDILIBRE_BASE_URL}/search"
    
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
    
    try:
        logger.info(f"Envoi de la requête à {endpoint}")
        response = requests.get(endpoint, headers=headers, params=params)
        
        logger.info(f"Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results_count = data.get("total", 0)
            logger.info(f"Accès à l'API JudiLibre réussi. {results_count} décisions trouvées.")
            return True
        else:
            logger.error(f"Échec de l'accès à l'API JudiLibre: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la requête à l'API JudiLibre: {str(e)}")
        return False

def main():
    """Fonction principale pour tester les APIs"""
    
    print("\n=== TEST DE CONNEXION AUX APIS AVEC MÉTHODES ALTERNATIVES ===\n")
    print(f"Date et heure du test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Client Secret: {CLIENT_SECRET[:5]}...{CLIENT_SECRET[-5:]} (masquée)\n")
    
    # Méthode 1: Basic Auth
    print("1. Tentative avec authentification HTTP Basic...")
    token = get_oauth_token_basic_auth()
    
    if not token:
        # Méthode 2: Avec scope
        print("\n2. Tentative avec scope 'openid'...")
        token = get_oauth_token_with_scope()
    
    if not token:
        print("\n❌ ÉCHEC: Impossible d'obtenir un token d'authentification.")
        
        print("\nRecommandations:")
        print("1. Vérifiez que les identifiants sont correctement activés dans votre compte PISTE")
        print("2. Vérifiez que vous avez souscrit aux APIs Légifrance et JudiLibre")
        print("3. Vérifiez que vous avez une demande approuvée dans DataPass")
        print("4. Contactez le support PISTE à support.api@dila.gouv.fr")
        
        return False
    
    print(f"\n✅ Authentification réussie. Token: {token[:10]}...{token[-10:]} (masqué)")
    
    # Tester l'API Légifrance
    legifrance_success = test_legifrance_api(token)
    
    if legifrance_success:
        print("\n✅ Test de l'API Légifrance réussi!")
    else:
        print("\n❌ ÉCHEC: Impossible d'accéder à l'API Légifrance.")
    
    # Tester l'API JudiLibre
    judilibre_success = test_judilibre_api(token)
    
    if judilibre_success:
        print("\n✅ Test de l'API JudiLibre réussi!")
    else:
        print("\n❌ ÉCHEC: Impossible d'accéder à l'API JudiLibre.")
    
    # Résultat global
    if legifrance_success and judilibre_success:
        print("\n===== SUCCÈS: Les deux APIs sont accessibles =====")
        return True
    elif legifrance_success:
        print("\n===== SUCCÈS PARTIEL: Uniquement l'API Légifrance est accessible =====")
        return True
    elif judilibre_success:
        print("\n===== SUCCÈS PARTIEL: Uniquement l'API JudiLibre est accessible =====")
        return True
    else:
        print("\n===== ÉCHEC: Aucune API n'est accessible =====")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 