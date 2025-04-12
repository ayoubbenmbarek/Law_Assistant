#!/usr/bin/env python3
"""
Script pour tester directement l'endpoint des tables annuelles de Légifrance
en utilisant exactement le format montré dans l'interface Swagger
"""

import os
import asyncio
import json
import requests
from dotenv import load_dotenv
from loguru import logger
import sys
from pathlib import Path

# Configuration du logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(log_dir / "test_tables_api.log", rotation="10 MB", level="DEBUG")

# Charger les variables d'environnement
load_dotenv()

# Récupération des clés API depuis les variables d'environnement
PISTE_API_KEY = os.getenv("PISTE_API_KEY")
PISTE_SECRET_KEY = os.getenv("PISTE_SECRET_KEY")

# Base URL pour les PDFs de Légifrance
LEGIFRANCE_PDF_BASE_URL = "https://www.legifrance.gouv.fr/download/pdf/table"

async def get_token():
    """Obtenir un token d'authentification depuis l'API PISTE"""
    auth_url = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
    auth_data = {
        "client_id": PISTE_API_KEY,
        "client_secret": PISTE_SECRET_KEY,
        "grant_type": "client_credentials",
        "scope": "openid"
    }
    
    try:
        response = requests.post(auth_url, data=auth_data)
        response.raise_for_status()
        token_data = response.json()
        token = token_data.get("access_token")
        logger.info("Token obtenu avec succès")
        return token
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du token: {str(e)}")
        raise

def construct_pdf_url(table):
    """Construire l'URL de téléchargement du PDF à partir des données de la table"""
    # Vérifier d'abord si une URL directe existe
    if "pdfUrl" in table and table["pdfUrl"]:
        return table["pdfUrl"]
    
    # Sinon, utiliser le champ pathToFile pour construire l'URL
    if "pathToFile" in table and table["pathToFile"]:
        return f"{LEGIFRANCE_PDF_BASE_URL}{table['pathToFile']}"
    
    return None

async def get_tables(token, start_year=2012, end_year=2022):
    """
    Récupérer les tables annuelles directement avec le format exact de l'API
    """
    url = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app/consult/getTables"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Exactement comme montré dans le screenshot Swagger
    payload = {
        "startYear": start_year,
        "endYear": end_year
    }
    
    try:
        logger.info(f"Envoi de la requête avec payload: {json.dumps(payload)}")
        response = requests.post(url, headers=headers, json=payload)
        
        # Afficher le code de statut HTTP même en cas d'erreur
        logger.info(f"Code de statut HTTP: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Erreur HTTP {response.status_code}: {response.text}")
            return None
            
        result = response.json()
        logger.info(f"Réponse reçue de type: {type(result)}")
        
        # Afficher les premières clés du résultat s'il s'agit d'un dictionnaire
        if isinstance(result, dict):
            logger.info(f"Clés dans la réponse: {list(result.keys())}")
            
            # Si la réponse contient une liste de tables, compter le nombre de tables
            if "tables" in result and isinstance(result["tables"], list):
                logger.info(f"Nombre de tables trouvées: {len(result['tables'])}")
                first_table = result["tables"][0]
                logger.info(f"Première table: {first_table.get('title', 'Sans titre')} ({first_table.get('id', 'Sans ID')})")
                
                # Print PDF URLs for the first few tables
                for i, table in enumerate(result["tables"][:3]):
                    logger.info(f"Table {i+1}: {table.get('title')} - ID: {table.get('id')}")
                    logger.info(f"Table data: {json.dumps(table, indent=2)}")
                    
                    # Construire et afficher l'URL de téléchargement du PDF
                    pdf_url = construct_pdf_url(table)
                    if pdf_url:
                        logger.info(f"PDF URL: {pdf_url}")
                    else:
                        logger.warning(f"Impossible de construire l'URL du PDF pour la table {table.get('id')}")
            else:
                logger.info("Aucune table trouvée")
        elif isinstance(result, list):
            logger.info(f"Nombre d'éléments dans la liste: {len(result)}")
            
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tables: {str(e)}")
        return None
    
async def main():
    """Fonction principale"""
    print("Test de l'API des tables annuelles Légifrance")
    print("---------------------------------------------")
    
    try:
        # Obtenir un token
        token = await get_token()
        if not token:
            print("❌ Échec: Impossible d'obtenir un token")
            return
            
        print("✅ Token obtenu avec succès")
        
        # Tester avec différentes plages d'années
        years_to_test = [
            (2012, 2022),  # Plage large
            (2020, 2020),  # Année unique récente
            (2015, 2015),  # Année unique plus ancienne
            (None, 2022),  # Jusqu'à 2022
            (2020, None),  # Depuis 2020
        ]
        
        for start_year, end_year in years_to_test:
            print(f"\nTest avec startYear={start_year}, endYear={end_year}")
            result = await get_tables(token, start_year, end_year)
            
            if result:
                print(f"✅ Succès: Réponse reçue")
                # Afficher un aperçu de la première table si présente
                if isinstance(result, dict) and "tables" in result and result["tables"]:
                    first_table = result["tables"][0]
                    print(f"   Première table: {first_table.get('title', 'Sans titre')} ({first_table.get('id', 'Sans ID')})")
                    
                    # Afficher l'URL de téléchargement du PDF
                    pdf_url = construct_pdf_url(first_table)
                    if pdf_url:
                        print(f"   URL du PDF: {pdf_url}")
                    else:
                        print("   Pas d'URL de PDF disponible")
                        
                elif isinstance(result, list) and result:
                    first_item = result[0]
                    print(f"   Premier élément: {first_item.get('title', 'Sans titre')} ({first_item.get('id', 'Sans ID')})")
                else:
                    print("   Aucune table trouvée")
            else:
                print("❌ Échec: Impossible de récupérer les tables")
        
    except Exception as e:
        print(f"❌ Erreur non gérée: {str(e)}")
        logger.exception("Erreur non gérée")

if __name__ == "__main__":
    asyncio.run(main()) 