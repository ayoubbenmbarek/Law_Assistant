#!/usr/bin/env python3
"""
Script pour tester la fonctionnalité de recherche avec les documents déjà importés
"""

import sys
import os
import argparse
from loguru import logger

# Ajouter le répertoire parent au chemin pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

def setup_logger():
    """Configure le logger"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")

def main():
    """Fonction principale"""
    setup_logger()
    
    # Configurer les arguments
    parser = argparse.ArgumentParser(description="Tester la recherche dans la base vectorielle")
    parser.add_argument("query", help="Requête de recherche")
    parser.add_argument("--limit", type=int, default=5, help="Nombre maximum de résultats (défaut: 5)")
    parser.add_argument("--type", choices=["loi", "jurisprudence"], help="Filtrer par type de document")
    args = parser.parse_args()
    
    # Importation conditionnelle du vector_store pour éviter les problèmes de mémoire
    try:
        from app.utils.vector_store import vector_store
        logger.info("Vector store module imported successfully")
    except Exception as e:
        logger.error(f"Failed to import vector store: {str(e)}")
        return False
    
    # Vérification que le vector store est fonctionnel
    if not vector_store or not vector_store.is_functional:
        logger.error("Vector store is not available or not functional")
        return False
    
    # Exécuter la recherche
    logger.info(f"Recherche: '{args.query}' (limit: {args.limit}, type: {args.type or 'all'})")
    try:
        results = vector_store.search(
            query=args.query,
            limit=args.limit,
            doc_type=args.type
        )
        
        if not results:
            logger.warning("Aucun résultat trouvé.")
            return True
            
        logger.info(f"Trouvé {len(results)} résultats:")
        
        for i, result in enumerate(results):
            logger.info(f"\n--- Résultat {i+1} (score: {result.get('score', 'N/A')}) ---")
            logger.info(f"ID: {result.get('id')}")
            logger.info(f"Titre: {result.get('title')}")
            logger.info(f"Type: {result.get('type')}")
            logger.info(f"Date: {result.get('date')}")
            
            # Afficher un extrait du contenu (limité à 200 caractères)
            content = result.get('content', '')
            if len(content) > 200:
                content = content[:197] + '...'
            logger.info(f"Contenu: {content}")
            
            # Afficher les métadonnées
            metadata = result.get('metadata', {})
            if metadata:
                logger.info("Métadonnées:")
                for key, value in metadata.items():
                    logger.info(f"  - {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        return False

if __name__ == "__main__":
    result = main()
    if not result:
        sys.exit(1) 