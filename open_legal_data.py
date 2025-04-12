#!/usr/bin/env python3
"""
Script d'accès aux données juridiques open source
Ce script permet d'accéder à différentes sources de données juridiques
ouvertes en attendant l'accès à l'API Légifrance.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import argparse
from datetime import datetime
import requests
from tqdm import tqdm
import pandas as pd
import zipfile
import io

# Configuration des sources de données
SOURCES = {
    "codes": {
        "name": "Codes",
        "url": "https://www.data.gouv.fr/fr/datasets/r/b0da0f5c-6e55-4112-a3aa-bc64ba0b98a9",
        "description": "LEGI - Codes en vigueur en XML",
        "format": "zip"
    },
    "lois": {
        "name": "Lois",
        "url": "https://www.data.gouv.fr/fr/datasets/r/3b422e9b-c574-43b3-a538-4a1ca73e3bcf",
        "description": "LEGI - Textes législatifs et réglementaires en XML",
        "format": "zip"
    },
    "jurisprudence": {
        "name": "Jurisprudence",
        "url": "https://www.data.gouv.fr/fr/datasets/r/f0eeb6a2-6dce-4ad0-b2dd-28c8bc5be1e0",
        "description": "JADE - Jurisprudence administrative en XML",
        "format": "zip"
    },
    "cassation": {
        "name": "Cassation",
        "url": "https://www.data.gouv.fr/fr/datasets/r/f8e65f48-5f9a-45c2-a482-01e82c0c0e66",
        "description": "CASS - Jurisprudence judiciaire en XML",
        "format": "zip"
    },
    "kali": {
        "name": "Conventions collectives",
        "url": "https://www.data.gouv.fr/fr/datasets/r/76f2bce3-4c83-422e-94b3-e290f93fb239",
        "description": "KALI - Conventions collectives en XML",
        "format": "zip"
    }
}

# URLs pour recherche
LEGIFRANCE_SEARCH_URL = "https://www.legifrance.gouv.fr/search/all?tab_selection=all&searchField=ALL&query="
ETALAB_LEGILIBRE_URL = "https://github.com/etalab/legilibre-data/releases"
DATA_GOUV_LEGIFRANCE_URL = "https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/"

def print_header(title):
    """Affiche un en-tête formaté"""
    width = 80
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width + "\n")

def download_file(url, dest_folder, verbose=True):
    """
    Télécharge un fichier avec une barre de progression
    """
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        if verbose:
            print(f"✅ Dossier créé: {dest_folder}")
            
    filename = url.split('/')[-1]
    if "?" in filename:
        filename = filename.split('?')[0]
        
    # Si le nom de fichier n'est pas explicite, utiliser un nom basé sur la date
    if len(filename) < 5 or "." not in filename:
        ext = "zip" if url.endswith(".zip") else "xml"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"legal_data_{timestamp}.{ext}"
    
    file_path = os.path.join(dest_folder, filename)
    
    # Vérifier si le fichier existe déjà
    if os.path.exists(file_path):
        if verbose:
            print(f"⚠️ Le fichier existe déjà: {file_path}")
            choice = input("Voulez-vous le télécharger à nouveau? (o/n): ").lower()
            if choice != 'o':
                return file_path
    
    if verbose:
        print(f"📥 Téléchargement de {url}...")
        print(f"   Vers: {file_path}")
    
    try:
        # Obtenir la taille du fichier
        response = requests.head(url)
        file_size = int(response.headers.get('content-length', 0))
        
        # Télécharger avec barre de progression
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            
            with open(file_path, 'wb') as f:
                chunk_size = 8192
                with tqdm(total=file_size, unit='B', unit_scale=True, 
                          desc=filename) as pbar:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        
        if verbose:
            print(f"✅ Téléchargement terminé: {file_path}")
        return file_path
    
    except Exception as e:
        if verbose:
            print(f"❌ Erreur lors du téléchargement: {str(e)}")
        return None

def extract_zip(zip_path, extract_folder=None, verbose=True):
    """
    Extrait une archive ZIP
    """
    if extract_folder is None:
        extract_folder = os.path.splitext(zip_path)[0]
    
    if not os.path.exists(extract_folder):
        os.makedirs(extract_folder)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if verbose:
                print(f"📂 Extraction vers {extract_folder}...")
                total_files = len(zip_ref.namelist())
                
                for i, file in enumerate(zip_ref.namelist()):
                    if verbose and i % 100 == 0:
                        print(f"   Progression: {i}/{total_files} fichiers...")
                    zip_ref.extract(file, extract_folder)
            else:
                zip_ref.extractall(extract_folder)
                
        if verbose:
            print(f"✅ Extraction terminée: {total_files} fichiers")
        return extract_folder
    
    except Exception as e:
        if verbose:
            print(f"❌ Erreur lors de l'extraction: {str(e)}")
        return None

def search_legifrance(query):
    """
    Ouvre le site Legifrance avec une recherche
    """
    search_url = LEGIFRANCE_SEARCH_URL + urllib.parse.quote(query)
    print(f"🔍 Recherche sur Legifrance: {query}")
    print(f"   URL: {search_url}")
    
    try:
        import webbrowser
        webbrowser.open(search_url)
        print("✅ Navigateur ouvert avec la recherche")
    except Exception as e:
        print(f"❌ Erreur lors de l'ouverture du navigateur: {str(e)}")
        print(f"   Veuillez ouvrir manuellement: {search_url}")

def list_data_sources():
    """
    Liste les sources de données disponibles
    """
    print_header("Sources de données juridiques libres disponibles")
    
    for key, source in SOURCES.items():
        print(f"\n{source['name']} ({key}):")
        print(f"  Description: {source['description']}")
        print(f"  Format: {source['format'].upper()}")
        print(f"  URL: {source['url']}")
    
    print("\nAutres ressources utiles:")
    print(f"- Legilibre (Etalab): {ETALAB_LEGILIBRE_URL}")
    print(f"- data.gouv.fr Légifrance: {DATA_GOUV_LEGIFRANCE_URL}")

def download_source(source_key, output_dir="legal_data"):
    """
    Télécharge une source de données spécifique
    """
    if source_key not in SOURCES:
        print(f"❌ Source inconnue: {source_key}")
        print(f"   Sources disponibles: {', '.join(SOURCES.keys())}")
        return False
    
    source = SOURCES[source_key]
    print_header(f"Téléchargement des données {source['name']}")
    print(f"Source: {source['description']}")
    
    # Créer le dossier de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ Dossier créé: {output_dir}")
    
    # Créer un sous-dossier pour cette source
    source_dir = os.path.join(output_dir, source_key)
    
    # Télécharger le fichier
    file_path = download_file(source['url'], source_dir)
    
    if file_path and source['format'] == 'zip':
        extract = input("\nVoulez-vous extraire l'archive ZIP? (o/n): ").lower()
        if extract == 'o':
            extract_dir = os.path.join(source_dir, "extracted")
            extract_zip(file_path, extract_dir)
    
    return file_path is not None

def main():
    """
    Fonction principale
    """
    parser = argparse.ArgumentParser(description="Accès aux données juridiques open source")
    
    # Commandes principales
    commands = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Commande: list
    list_cmd = commands.add_parser("list", help="Lister les sources de données disponibles")
    
    # Commande: download
    download_cmd = commands.add_parser("download", help="Télécharger une source de données")
    download_cmd.add_argument("source", choices=list(SOURCES.keys()) + ["all"], 
                             help="Source à télécharger (ou 'all' pour toutes)")
    download_cmd.add_argument("--output", "-o", default="legal_data",
                             help="Dossier de sortie (par défaut: legal_data)")
    
    # Commande: search
    search_cmd = commands.add_parser("search", help="Rechercher sur Legifrance")
    search_cmd.add_argument("query", help="Terme de recherche")
    
    # Analyse des arguments
    args = parser.parse_args()
    
    # Si aucune commande n'est spécifiée, afficher l'aide
    if args.command is None:
        parser.print_help()
        return 0
    
    # Exécuter la commande appropriée
    if args.command == "list":
        list_data_sources()
    
    elif args.command == "download":
        if args.source == "all":
            success = True
            for source_key in SOURCES.keys():
                source_success = download_source(source_key, args.output)
                success = success and source_success
            return 0 if success else 1
        else:
            success = download_source(args.source, args.output)
            return 0 if success else 1
    
    elif args.command == "search":
        search_legifrance(args.query)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 