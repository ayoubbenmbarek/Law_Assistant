#!/usr/bin/env python3
"""
Script pour tester l'accès au modèle Hugging Face avec le token
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_access():
    """Teste l'accès au modèle Hugging Face"""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer le token
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        logger.error("Le token Hugging Face n'est pas défini dans les variables d'environnement")
        return False
    
    logger.info(f"Token récupéré: {hf_token[:5]}...{hf_token[-5:]}")
    
    # Tester l'accès au modèle
    try:
        from huggingface_hub import snapshot_download
        from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
        
        # Use a known public summarization model
        model_name = "mrm8488/camembert2camembert_shared-finetuned-french-summarization"
        logger.info(f"Tentative d'accès au modèle: {model_name}")
        
        # Télécharger le modèle avec authentification
        model_path = snapshot_download(
            repo_id=model_name,
            token=hf_token
        )
        
        logger.info(f"Modèle téléchargé avec succès dans: {model_path}")
        
        # Initialiser le tokenizer et le modèle séparément
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        
        # Initialiser le pipeline
        summarizer = pipeline(
            task="summarization", 
            model=model,
            tokenizer=tokenizer,
            device=-1
        )
        
        logger.info("Pipeline initialisé avec succès")
        
        # Test simple pour vérifier le fonctionnement
        test_text = "L'article 1382 du Code civil dispose que tout fait quelconque de l'homme, qui cause à autrui un dommage, oblige celui par la faute duquel il est arrivé à le réparer. Cette disposition fondamentale du droit français établit le principe général de responsabilité civile délictuelle."
        result = summarizer(test_text, max_length=50, min_length=10)
        
        logger.info(f"Test réussi! Résumé: {result[0]['summary_text']}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'accès au modèle: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_model_access()
    sys.exit(0 if success else 1) 