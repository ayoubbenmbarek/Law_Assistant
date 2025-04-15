#!/usr/bin/env python3
"""
Script pour tester l'initialisation de DataEnrichment
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enrichment():
    """Teste l'initialisation du service d'enrichissement"""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Importer après le chargement des variables d'environnement
    from app.data.data_enrichment import DataEnrichment
    
    logger.info("Initialisation du service d'enrichissement...")
    
    # Initialiser le service
    service = DataEnrichment()
    
    # Vérifier l'initialisation du résumeur
    if service.summarizer is not None:
        logger.info("Le résumeur a été correctement initialisé")
        
        # Tester le résumeur avec un texte simple
        test_text = "L'article 1382 du Code civil dispose que tout fait quelconque de l'homme, qui cause à autrui un dommage, oblige celui par la faute duquel il est arrivé à le réparer. Cette disposition fondamentale du droit français établit le principe général de responsabilité civile délictuelle."
        
        try:
            # Exécuter une inférence de test
            summary = service.summarizer(test_text, max_length=50, min_length=10)
            logger.info(f"Test de résumé réussi: {summary[0]['summary_text']}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du test du résumeur: {str(e)}")
            return False
    else:
        logger.error("Le résumeur n'a pas été correctement initialisé")
        return False

if __name__ == "__main__":
    success = test_enrichment()
    sys.exit(0 if success else 1) 