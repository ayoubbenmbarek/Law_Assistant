#!/usr/bin/env python3
"""
Script d'importation des données juridiques dans la base vectorielle
Ce script peut être exécuté directement ou via Docker Compose
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv
from loguru import logger

# Ajouter le répertoire parent au chemin pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importer les modules après l'ajout du chemin
from app.data.legifrance_api import legifrance_api
from app.utils.vector_store import vector_store

# Charger les variables d'environnement
load_dotenv()

def setup_logger():
    """Configure le logger"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("logs/import_legal_data.log", rotation="500 MB", level="DEBUG")

async def import_codes(limit_per_term=5, specific_terms=None):
    """Importe des articles de code juridique"""
    if specific_terms:
        terms = specific_terms.split(',')
    else:
        terms = None  # Utilise la liste par défaut dans legifrance_api
    
    result = await legifrance_api.import_codes(limit=limit_per_term, search_terms=terms)
    return result

async def import_jurisprudence(limit_per_term=5, specific_terms=None):
    """Importe des décisions de jurisprudence"""
    if specific_terms:
        terms = specific_terms.split(',')
    else:
        terms = None  # Utilise la liste par défaut dans legifrance_api
    
    result = await legifrance_api.import_jurisprudence(limit=limit_per_term, search_terms=terms)
    return result

async def verify_vector_store():
    """Vérifie que la base vectorielle est fonctionnelle"""
    if not vector_store or not vector_store.is_functional:
        logger.error("Base vectorielle non disponible ou non fonctionnelle")
        return False
    
    try:
        # Test simple
        logger.info("Test de la base vectorielle...")
        test_result = vector_store.search("test", limit=1)
        logger.info(f"Test de recherche dans la base vectorielle: {len(test_result)} résultat(s)")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du test de la base vectorielle: {str(e)}")
        return False

async def main():
    """Fonction principale"""
    setup_logger()
    
    parser = argparse.ArgumentParser(description="Script d'importation des données juridiques")
    parser.add_argument("--type", choices=["codes", "jurisprudence", "all"], default="all",
                        help="Type de données à importer (default: all)")
    parser.add_argument("--limit", type=int, default=5, 
                        help="Nombre maximum de documents par terme de recherche (default: 5)")
    parser.add_argument("--terms", type=str, 
                        help="Termes de recherche spécifiques (séparés par des virgules)")
    
    args = parser.parse_args()
    
    logger.info(f"Démarrage de l'importation des données juridiques (type: {args.type}, limite: {args.limit})")
    
    # Vérifier la base vectorielle
    if not await verify_vector_store():
        logger.error("La base vectorielle n'est pas disponible. Abandon de l'importation.")
        return
    
    try:
        if args.type in ["codes", "all"]:
            logger.info("Importation des codes...")
            codes_result = await import_codes(limit_per_term=args.limit, specific_terms=args.terms)
            logger.info(f"Importation des codes terminée: {codes_result}")
        
        if args.type in ["jurisprudence", "all"]:
            logger.info("Importation de la jurisprudence...")
            jurisprudence_result = await import_jurisprudence(limit_per_term=args.limit, specific_terms=args.terms)
            logger.info(f"Importation de la jurisprudence terminée: {jurisprudence_result}")
        
        logger.info("Importation des données juridiques terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'importation des données: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 