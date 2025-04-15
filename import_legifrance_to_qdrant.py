#!/usr/bin/env python3
"""
Script pour importer les données de Legifrance depuis les fichiers JSON
vers la base vectorielle Qdrant
"""

import os
import json
import asyncio
import glob
import uuid
import hashlib
from typing import List, Dict, Any
from loguru import logger
from dotenv import load_dotenv

# Import the Legifrance API client
from app.data.legifrance_api import legifrance_api

# Load environment variables
load_dotenv()

# Directory with JSON files
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legal_data")

def generate_numeric_id(text_id: str) -> int:
    """
    Generate a numeric ID from a text ID using a hash function
    
    Args:
        text_id: Original text ID
        
    Returns:
        A numeric ID suitable for Qdrant as an integer
    """
    # Create a hash of the original ID to ensure uniqueness
    hash_obj = hashlib.md5(text_id.encode())
    # Convert to a positive integer by taking only part of the hash
    # and removing the negative sign possibility
    numeric_id = abs(int(hash_obj.hexdigest(), 16) % (2**31 - 1))
    return numeric_id

async def process_code_file(file_path: str) -> int:
    """
    Traite un fichier JSON contenant des données de codes et les importe dans Qdrant
    
    Args:
        file_path: Chemin vers le fichier JSON
        
    Returns:
        Nombre de sources importées
    """
    try:
        logger.info(f"Traitement du fichier: {file_path}")
        
        # Charger le fichier JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Extraire les résultats
        results = data.get("results", [])
        if not results:
            logger.warning(f"Aucun résultat trouvé dans {file_path}")
            return 0
            
        # Transformer en format attendu par import_to_vector_store
        sources = []
        for result in results:
            # Obtenir le titre et l'ID du code s'ils sont disponibles
            title = result.get("titles", [{}])[0].get("title", "Titre inconnu")
            code_id = result.get("titles", [{}])[0].get("cid", "ID inconnu")
            
            # Générer un ID numérique pour Qdrant
            numeric_id = generate_numeric_id(code_id)
            
            # Construire l'URL vers Legifrance
            url = f"https://www.legifrance.gouv.fr/codes/id/{code_id}"
            
            # Date de publication au format YYYY-MM-DD
            date_str = result.get("date", "")
            if date_str and "T" in date_str:
                date = date_str.split("T")[0]
            else:
                date = "1977-01-01"  # Date par défaut
            
            # Contenu du texte (s'il est disponible, sinon utiliser un placeholder)
            content = result.get("text")
            if not content:
                content = f"Code juridique: {title}. Référence légale en droit français."
            
            # Créer l'objet source
            source = {
                "id": numeric_id,
                "title": title,
                "content": content,
                "type": "code",
                "date": date,
                "url": url,
                "metadata": {
                    "original_id": code_id,
                    "nature": result.get("nature"),
                    "origin": result.get("origin"),
                    "etat": result.get("etat"),
                    "source_file": os.path.basename(file_path)
                }
            }
            sources.append(source)
        
        # Importer dans la base vectorielle
        logger.info(f"Importation de {len(sources)} entrées dans la base vectorielle")
        await legifrance_api.import_to_vector_store(sources)
        
        logger.success(f"Importation réussie de {len(sources)} entrées depuis {file_path}")
        return len(sources)
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du fichier {file_path}: {str(e)}")
        return 0

async def process_jurisprudence_file(file_path: str) -> int:
    """
    Traite un fichier JSON contenant des données de jurisprudence et les importe dans Qdrant
    
    Args:
        file_path: Chemin vers le fichier JSON
        
    Returns:
        Nombre de sources importées
    """
    try:
        logger.info(f"Traitement du fichier de jurisprudence: {file_path}")
        
        # Charger le fichier JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Extraire les résultats
        results = data.get("results", [])
        if not results:
            logger.warning(f"Aucun résultat trouvé dans {file_path}")
            return 0
            
        # Transformer en format attendu par import_to_vector_store
        sources = []
        for result in results:
            # Générer un ID unique si non disponible
            result_id = result.get("id") or f"JURI-{hash(str(result))}"
            
            # Générer un ID numérique pour Qdrant
            numeric_id = generate_numeric_id(result_id)
            
            # Obtenir le titre
            title = result.get("title", "Décision de justice")
            
            # Date de publication au format YYYY-MM-DD
            date_str = result.get("date", "")
            if date_str and "T" in date_str:
                date = date_str.split("T")[0]
            else:
                date = "2000-01-01"  # Date par défaut
            
            # Contenu du texte
            content = result.get("text")
            if not content:
                content = f"Jurisprudence: {title}. Décision de justice française."
            
            # Construire l'URL vers Legifrance (si possible)
            url = f"https://www.legifrance.gouv.fr/juri/id/{result_id}" if "JURI" in result_id else ""
            
            # Créer l'objet source
            source = {
                "id": numeric_id,
                "title": title,
                "content": content,
                "type": "jurisprudence",
                "date": date,
                "url": url,
                "metadata": {
                    "original_id": result_id,
                    "nature": result.get("nature"),
                    "origin": result.get("origin"),
                    "juridiction": result.get("juridiction"),
                    "solution": result.get("solution"),
                    "source_file": os.path.basename(file_path)
                }
            }
            sources.append(source)
        
        # Importer dans la base vectorielle
        logger.info(f"Importation de {len(sources)} entrées de jurisprudence dans la base vectorielle")
        await legifrance_api.import_to_vector_store(sources)
        
        logger.success(f"Importation réussie de {len(sources)} entrées depuis {file_path}")
        return len(sources)
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du fichier {file_path}: {str(e)}")
        return 0

async def import_all_files():
    """Importe tous les fichiers JSON dans la base vectorielle"""
    # Importation des codes
    codes_files = glob.glob(os.path.join(DATA_DIR, "codes_*.json"))
    
    total_codes = 0
    for file_path in codes_files:
        count = await process_code_file(file_path)
        total_codes += count
    
    # Importation de la jurisprudence
    jurisprudence_files = glob.glob(os.path.join(DATA_DIR, "jurisprudence_*.json"))
    
    total_jurisprudence = 0
    for file_path in jurisprudence_files:
        count = await process_jurisprudence_file(file_path)
        total_jurisprudence += count
    
    logger.info(f"Importation terminée. Total: {total_codes} codes, {total_jurisprudence} décisions de jurisprudence")

if __name__ == "__main__":
    logger.info("Démarrage de l'importation des données Legifrance vers Qdrant")
    asyncio.run(import_all_files())
    logger.info("Script terminé") 