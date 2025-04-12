#!/usr/bin/env python3
"""
Script d'importation d'un seul document pour tester la fonctionnalité de base du vector store
"""

import sys
import os
import uuid
from loguru import logger
from datetime import datetime

# Ajouter le répertoire parent au chemin pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

# Configuration des logs
logger.remove()
logger.add(sys.stderr, level="INFO")

# Importation conditionnelle 
try:
    from app.utils.vector_store import vector_store
    logger.info("Vector store module imported successfully")
except Exception as e:
    logger.error(f"Failed to import vector store: {str(e)}")
    sys.exit(1)

def main():
    """Fonction principale d'importation d'un seul document"""
    
    # Vérification que le vector store est fonctionnel
    if not vector_store or not vector_store.is_functional:
        logger.error("Vector store is not available or not functional")
        return False
    
    # Document de test simple
    doc_id = str(uuid.uuid4())
    title = "Test Document - Code Civil Article 1"
    content = "Les lois sont exécutoires dans tout le territoire français en vertu de la promulgation qui en est faite par le Président de la République."
    doc_type = "loi"
    date = "2023-01-01"
    url = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006419283/"
    metadata = {
        "code": "Code Civil", 
        "section": "Titre préliminaire"
    }
    
    # Tentative d'ajout du document
    logger.info(f"Attempting to add test document with ID: {doc_id}")
    try:
        success = vector_store.add_document(
            doc_id=doc_id,
            title=title,
            content=content,
            doc_type=doc_type,
            date=date,
            url=url,
            metadata=metadata
        )
        
        if success:
            logger.info("Document added successfully!")
            
            # Test de recherche simple
            logger.info("Testing search functionality...")
            results = vector_store.search("loi territoire", limit=1)
            
            if results:
                logger.info(f"Search successful! Found {len(results)} results.")
                logger.info(f"Top result: {results[0]['title']} (score: {results[0]['score']})")
            else:
                logger.warning("Search returned no results.")
        else:
            logger.error("Failed to add document.")
            
    except Exception as e:
        logger.error(f"Error during document addition: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    logger.info("Starting minimal vector store test")
    result = main()
    if result:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed") 