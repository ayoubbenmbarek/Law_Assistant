#!/usr/bin/env python3
"""
Script pour explorer les données des tables Légifrance et comprendre leur structure.
Ce script permet d'analyser les tables récupérées via l'API et de préparer
les données pour l'embedding avant ingestion dans Qdrant.
"""

import os
import json
import requests
import asyncio
from datetime import datetime
from urllib.parse import urljoin
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
import PyPDF2
import io

# Charger les variables d'environnement
load_dotenv()

# API configuration
CLIENT_ID = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
CLIENT_SECRET = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")
API_BASE_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

# Dossier pour sauvegarder les PDFs téléchargés
PDF_DIR = Path("data/legifrance/tables")
# Dossier pour les données transformées
PROCESSED_DIR = Path("data/legifrance/processed")

def get_oauth_token():
    """Obtenir un token OAuth pour l'authentification à l'API PISTE"""
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "openid"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    print(f"Demande de token avec client_id: {CLIENT_ID}")
    response = requests.post(AUTH_URL, data=auth_data, headers=headers)
    response.raise_for_status()
    
    token_data = response.json()
    token = token_data.get("access_token")
    
    return token

def get_tables(token, start_year=2012, end_year=2017):
    """Récupération des tables annuelles pour une période donnée"""
    endpoint = f"{API_BASE_URL}/consult/getTables"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Payload exactement comme Swagger
    payload = {
        "endYear": end_year,
        "startYear": start_year
    }
    
    print(f"Récupération des tables pour la période {start_year}-{end_year}")
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    tables = result.get("tables", [])
    print(f"Nombre de tables trouvées: {len(tables)}")
    
    return tables

def download_pdf(token, table_info):
    """Télécharge un PDF de table depuis l'API Légifrance"""
    # Créer les dossiers s'ils n'existent pas
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    # Construire le chemin complet pour le téléchargement
    file_path = PDF_DIR / table_info["fileName"]
    
    # Vérifier si le fichier existe déjà
    if file_path.exists():
        print(f"Fichier {table_info['fileName']} déjà téléchargé")
        return file_path
    
    # Construire l'URL pour télécharger le PDF
    # Note: à ajuster selon la documentation précise de l'API
    download_url = f"{API_BASE_URL}/consult/tableFile"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/pdf"
    }
    
    payload = {
        "path": table_info["pathToFile"]
    }
    
    print(f"Téléchargement de {table_info['fileName']}...")
    response = requests.post(download_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        # Sauvegarder le PDF
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"PDF sauvegardé: {file_path}")
        return file_path
    else:
        print(f"Échec du téléchargement: {response.status_code}")
        print(response.text)
        return None

def extract_text_from_pdf(pdf_path):
    """Extrait le texte d'un fichier PDF"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Erreur lors de l'extraction du texte de {pdf_path}: {str(e)}")
        return ""

def analyze_tables_metadata(tables):
    """Analyse les métadonnées des tables et retourne un DataFrame pour analyse"""
    # Créer un DataFrame pandas pour faciliter l'analyse
    df = pd.DataFrame(tables)
    
    # Convertir les dates de timestamp en datetime
    if 'datePubli' in df.columns:
        df['datePubli'] = pd.to_datetime(df['datePubli'], unit='ms')
    
    # Afficher des statistiques générales
    print("\n=== Analyse des métadonnées des tables ===")
    print(f"Nombre total de tables: {len(df)}")
    if 'type' in df.columns:
        print("\nTypes de tables:")
        print(df['type'].value_counts())
    
    if 'origine' in df.columns:
        print("\nOrigines des tables:")
        print(df['origine'].value_counts())
    
    if 'datePubli' in df.columns:
        print("\nRépartition par année:")
        print(df['datePubli'].dt.year.value_counts().sort_index())
    
    # Retourner le DataFrame pour analyse plus approfondie si nécessaire
    return df

def prepare_for_embedding(tables_data, token):
    """Prépare les données pour l'embedding en créant des chunks appropriés"""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    
    for table in tables_data:
        # Télécharger le PDF
        pdf_path = download_pdf(token, table)
        if not pdf_path:
            continue
        
        # Extraire le texte
        text = extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            print(f"Aucun texte extrait de {table['fileName']}")
            continue
            
        # Diviser le texte en chunks de taille appropriée pour l'embedding
        # (généralement 1000-2000 caractères pour des modèles comme BERT)
        chunk_size = 1500
        overlap = 200
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text) and end - start > overlap:
                # Chercher la fin de phrase ou de paragraphe pour une meilleure découpe
                for i in range(min(end + 50, len(text) - 1), start + chunk_size - overlap, -1):
                    if text[i] in ['.', '!', '?', '\n'] and text[i+1:i+3].isspace():
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": table['fileName'],
                        "type": table.get('type', ''),
                        "year": datetime.fromtimestamp(table['datePubli']/1000).year if 'datePubli' in table else None,
                        "chunk_id": f"{table['id']}_chunk_{len(chunks)}",
                        "origine": table.get('origine', '')
                    }
                })
            
            # Avancer avec chevauchement
            start = end - overlap if end < len(text) else end
        
        print(f"Créé {len(chunks)} chunks à partir de {table['fileName']}")
        all_chunks.extend(chunks)
    
    # Sauvegarder tous les chunks dans un fichier JSON
    output_file = PROCESSED_DIR / "tables_chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal de {len(all_chunks)} chunks créés et sauvegardés dans {output_file}")
    return all_chunks

def main():
    """Fonction principale d'exploration des données"""
    print("=== EXPLORATION DES DONNÉES LÉGIFRANCE ===")
    
    # Obtenir un token d'authentification
    token = get_oauth_token()
    if not token:
        print("Impossible d'obtenir un token d'authentification")
        return
    
    # Récupérer les données des tables
    tables = get_tables(token, start_year=2012, end_year=2017)
    
    # Sauvegarder les données brutes
    with open("data_tables_raw.json", "w", encoding="utf-8") as f:
        json.dump(tables, f, ensure_ascii=False, indent=2)
    
    # Analyser les métadonnées
    df_tables = analyze_tables_metadata(tables)
    
    # Demander à l'utilisateur s'il souhaite continuer avec le téléchargement et l'extraction
    response = input("\nVoulez-vous télécharger les PDFs et préparer les données pour l'embedding? (o/n): ")
    if response.lower() == 'o':
        # Préparer les données pour l'embedding
        chunks = prepare_for_embedding(tables, token)
        print(f"Préparation terminée. {len(chunks)} chunks prêts pour l'embedding.")
    else:
        print("Téléchargement et préparation des données annulés.")

if __name__ == "__main__":
    main() 