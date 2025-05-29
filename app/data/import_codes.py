#!/usr/bin/env python
"""
Script pour importer les codes depuis l'API Legifrance dans Qdrant
"""

import asyncio
import argparse
import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import des modules nécessaires
from app.data.legifrance_api import LegifranceAPI
from app.utils.vector_store import vector_store
from app.data.etl_manager import chunk_text
from app.data.data_enrichment import DataEnrichment

# Codes à importer (ID et noms)
CODE_IDS = {
    "LEGITEXT000006070721": "Code civil",
    "LEGITEXT000006072050": "Code du travail",
    "LEGITEXT000005634379": "Code de commerce",
    "LEGITEXT000006070716": "Code de procédure civile",
    "LEGITEXT000006071154": "Code de procédure pénale",
    "LEGITEXT000006070719": "Code pénal",
    "LEGITEXT000006069414": "Code de la propriété intellectuelle",
    "LEGITEXT000006074075": "Code de l'urbanisme",
    "LEGITEXT000006074220": "Code de l'environnement",
    "LEGITEXT000006069577": "Code général des impôts",
    "LEGITEXT000006070933": "Code de justice administrative",
    "LEGITEXT000006075116": "Code constitutionnel",
    "LEGITEXT000006073189": "Code de la sécurité sociale",
    "LEGITEXT000031366350": "Code des relations entre le public et l'administration",
    "LEGITEXT000006074228": "Code de la route"
}

# Initialisation des modules
legifrance_api = LegifranceAPI()
data_enrichment = DataEnrichment()

async def fetch_code_content(code_id: str, code_name: str) -> Optional[Dict[str, Any]]:
    """
    Récupère le contenu d'un code via l'API Legifrance
    
    Args:
        code_id: ID du code
        code_name: Nom du code
        
    Returns:
        Dictionnaire contenant les données du code ou None si erreur
    """
    try:
        # Payload pour l'API
        payload = {
            "textId": code_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "abrogated": True
        }
        
        # Appel à l'API
        logger.info(f"Récupération du code: {code_name} (ID: {code_id})")
        result = await legifrance_api._make_api_request("consult/code", "POST", payload)
        
        # Vérifier si la structure attendue est présente
        if not result or "title" not in result:
            logger.warning(f"Structure incorrecte pour le code {code_name}")
            return None
            
        # Préparation des données
        return {
            "id": code_id,
            "title": result.get("title", code_name),
            "type": "code",
            "date": result.get("date", datetime.now().strftime("%Y-%m-%d")),
            "content": extract_code_text(result),
            "url": f"https://www.legifrance.gouv.fr/codes/id/{code_id}",
            "metadata": {
                "source": "Legifrance",
                "code_name": code_name,
                "version_date": result.get("date"),
                "structure": json.dumps(result.get("structure", {}))[:1000],  # Limiter la taille
            }
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du code {code_name}: {str(e)}")
        return None
        
def extract_code_text(code_data: Dict[str, Any]) -> str:
    """
    Extrait le texte du code à partir des données structurées
    
    Args:
        code_data: Données du code depuis l'API
        
    Returns:
        Texte extrait du code
    """
    # Récupérer le titre
    text_parts = [code_data.get("title", "")]
    
    # Extraire le texte de manière récursive depuis la structure
    structure = code_data.get("structure", {})
    if structure:
        extract_text_from_structure(structure, text_parts)
        
    # Ajouter les articles qui seraient à la racine
    articles = code_data.get("articles", [])
    for article in articles:
        if "content" in article:
            text_parts.append(f"Article {article.get('num', '')}: {article.get('content', '')}")
    
    return "\n\n".join(text_parts)
    
def extract_text_from_structure(structure: Dict[str, Any], text_parts: List[str], depth: int = 0):
    """
    Extrait récursivement le texte depuis la structure du code
    
    Args:
        structure: Structure du code
        text_parts: Liste pour stocker les parties de texte
        depth: Profondeur dans la structure
    """
    # Ajouter le titre de la section
    if "title" in structure:
        prefix = "  " * depth
        text_parts.append(f"{prefix}{structure.get('title', '')}")
    
    # Ajouter les articles de cette section
    articles = structure.get("articles", [])
    for article in articles:
        if "content" in article:
            text_parts.append(f"Article {article.get('num', '')}: {article.get('content', '')}")
    
    # Parcourir les sections enfants
    children = structure.get("children", [])
    for child in children:
        extract_text_from_structure(child, text_parts, depth + 1)

async def process_code(code_id: str, code_name: str) -> int:
    """
    Traite un code: télécharge, chunke, enrichit et stocke dans Qdrant
    
    Args:
        code_id: ID du code
        code_name: Nom du code
        
    Returns:
        Nombre de chunks stockés
    """
    # Récupérer le contenu du code
    code_data = await fetch_code_content(code_id, code_name)
    if not code_data:
        return 0
        
    # Découper le contenu en chunks
    logger.info(f"Découpage du code {code_name} en chunks")
    chunks = chunk_text(
        text=code_data["content"],
        title=code_data["title"],
        id_prefix=f"code_{code_id}"
    )
    
    if not chunks:
        logger.warning(f"Aucun chunk généré pour le code {code_name}")
        return 0
    
    # Enrichir les chunks avec NLP
    logger.info(f"Enrichissement des {len(chunks)} chunks pour le code {code_name}")
    enriched_chunks = []
    
    for chunk in tqdm(chunks, desc=f"Enrichissement {code_name}"):
        # Copier les métadonnées du code
        chunk["type"] = "code"
        chunk["date"] = code_data["date"]
        chunk["url"] = code_data["url"]
        
        if "metadata" not in chunk:
            chunk["metadata"] = {}
            
        # Ajouter/fusionner les métadonnées
        for key, value in code_data["metadata"].items():
            chunk["metadata"][key] = value
            
        # Enrichir le chunk
        enriched_chunk = data_enrichment.enrich_document(chunk)
        enriched_chunks.append(enriched_chunk)
    
    # Stocker dans Qdrant
    logger.info(f"Stockage de {len(enriched_chunks)} chunks dans Qdrant pour le code {code_name}")
    vector_store.add_documents(enriched_chunks)
    
    return len(enriched_chunks)

async def main(code_ids=None, skip_authentication=False):
    """
    Fonction principale d'import
    
    Args:
        code_ids: Liste des IDs de codes à importer (None pour tous)
        skip_authentication: Ignorer l'authentification (utile pour les tests)
    """
    # S'authentifier auprès de l'API si nécessaire
    if not skip_authentication:
        await legifrance_api.authenticate()
    
    total_chunks = 0
    selected_codes = CODE_IDS
    
    # Filtrer les codes si nécessaire
    if code_ids:
        selected_codes = {k: v for k, v in CODE_IDS.items() if k in code_ids}
    
    # Récupérer et stocker chaque code
    for code_id, code_name in selected_codes.items():
        chunks_count = await process_code(code_id, code_name)
        total_chunks += chunks_count
        logger.info(f"Code {code_name} traité: {chunks_count} chunks générés")
    
    logger.info(f"Import terminé. Total: {total_chunks} chunks dans {len(selected_codes)} codes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import des codes Legifrance dans Qdrant")
    parser.add_argument("--codes", nargs="+", help="IDs des codes à importer (par défaut: tous)")
    parser.add_argument("--skip-auth", action="store_true", help="Ignorer l'authentification (pour tests)")
    
    args = parser.parse_args()
    
    asyncio.run(main(args.codes, args.skip_auth)) 