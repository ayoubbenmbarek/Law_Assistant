#!/usr/bin/env python3
"""
Script pour extraire l'ensemble des données juridiques de Légifrance,
les découper en chunks significatifs, les encoder en vecteurs et les
stocker dans une collection Qdrant propre.

Ce script utilise l'API Légifrance pour extraire:
- Les codes juridiques (Code civil, Code du travail, etc.)
- La jurisprudence (décisions de justice)
- La législation (lois, décrets, etc.)
- Les circulaires et instructions

Les données sont traitées, découpées en fragments pertinents,
vectorisées puis stockées dans Qdrant pour la recherche sémantique.
"""

import os
import sys
import asyncio
import time
import json
import hashlib
import uuid
import textwrap
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
from loguru import logger
import nltk
from nltk.tokenize import sent_tokenize

# Assurez-vous que le module app peut être importé
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import des modules de l'application
from app.data.legifrance_api import legifrance_api
from app.utils.vector_store import vector_store

# Téléchargement des ressources NLTK nécessaires (si pas déjà installées)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Constantes de configuration
CHUNK_SIZE = 1000  # Taille approximative des chunks en caractères
CHUNK_OVERLAP = 200  # Chevauchement entre les chunks
MAX_RESULTS_PER_QUERY = 50  # Nombre maximum de résultats par requête API
NEW_COLLECTION_NAME = "LegalTextsClean"  # Nom de la nouvelle collection
EXTRACTION_DELAY = 1  # Délai en secondes entre les requêtes API pour éviter le rate limiting

# Domaines juridiques à explorer
LEGAL_DOMAINS = {
    "codes": [
        "civil", "pénal", "travail", "commerce", "consommation", 
        "environnement", "santé", "éducation", "fiscalité", "urbanisme",
        "propriété intellectuelle", "assurance", "procédure civile", 
        "procédure pénale", "sécurité sociale", "famille"
    ],
    "jurisprudence": [
        "cassation", "conseil d'état", "tribunal", "cour d'appel", 
        "licenciement", "contrat", "responsabilité", "préjudice",
        "succession", "bail", "mariage", "divorce", "société", 
        "vente", "assurance", "crédit", "impôt", "faute"
    ],
    "legislation": [
        "loi", "décret", "arrêté", "ordonnance", "constitution",
        "droits fondamentaux", "administration", "service public",
        "entreprise", "données personnelles", "travailleur", "employeur",
        "consommateur", "environnement", "développement durable"
    ]
}

# Sous-domaines et concepts spécifiques
LEGAL_CONCEPTS = {
    "civil": ["contrat", "obligation", "responsabilité", "propriété", "servitude", "usufruit", "succession"],
    "travail": ["licenciement", "rupture conventionnelle", "congé", "salaire", "convention collective", "négociation"],
    "famille": ["mariage", "divorce", "adoption", "autorité parentale", "pension alimentaire", "succession"],
    "penal": ["infraction", "délit", "crime", "peine", "récidive", "prescription", "procédure"],
    "immobilier": ["bail", "copropriété", "servitude", "hypothèque", "crédit immobilier", "construction"],
    "affaires": ["société", "fusion", "cession", "concurrence", "distribution", "propriété intellectuelle"]
}

async def setup_qdrant_collection():
    """Configure une nouvelle collection propre dans Qdrant"""
    try:
        # Importation dynamique pour éviter les erreurs d'importation circulaire
        import qdrant_client
        from qdrant_client.http import models
        from app.utils.vector_store import EMBEDDING_DIMENSION, QDRANT_URL, QDRANT_API_KEY
        
        logger.info(f"Configuration de la collection Qdrant '{NEW_COLLECTION_NAME}'")
        
        # Initialisation du client Qdrant
        client = qdrant_client.QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
            timeout=60
        )
        
        # Vérification si la collection existe déjà
        try:
            collection_info = client.get_collection(collection_name=NEW_COLLECTION_NAME)
            logger.info(f"Collection '{NEW_COLLECTION_NAME}' existe déjà")
            
            # Option pour recréer la collection (à décommenter si nécessaire)
            # user_input = input(f"Voulez-vous supprimer et recréer la collection '{NEW_COLLECTION_NAME}'? (o/n): ").lower()
            # if user_input == 'o':
            #     client.delete_collection(collection_name=NEW_COLLECTION_NAME)
            #     logger.info(f"Collection '{NEW_COLLECTION_NAME}' supprimée")
            #     raise Exception("Collection supprimée volontairement pour recréation")
            
        except Exception as e:
            logger.info(f"Création d'une nouvelle collection '{NEW_COLLECTION_NAME}'")
            
            # Création de la collection avec les paramètres optimaux
            client.create_collection(
                collection_name=NEW_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE
                ),
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=20000  # Optimisation pour les grandes collections
                )
            )
            
            # Création d'index pour accélérer les recherches
            client.create_payload_index(
                collection_name=NEW_COLLECTION_NAME,
                field_name="type",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            client.create_payload_index(
                collection_name=NEW_COLLECTION_NAME,
                field_name="domain",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            client.create_payload_index(
                collection_name=NEW_COLLECTION_NAME,
                field_name="date",
                field_schema=models.PayloadSchemaType.DATE
            )
            
            logger.success(f"Collection '{NEW_COLLECTION_NAME}' créée avec succès")
        
        return client
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de la collection Qdrant: {str(e)}")
        raise

def chunk_text(text: str, title: str = "", id_prefix: str = "") -> List[Dict[str, Any]]:
    """
    Découpe un texte juridique en chunks de taille appropriée avec chevauchement
    
    Args:
        text: Texte à découper
        title: Titre du document
        id_prefix: Préfixe pour les IDs des chunks
        
    Returns:
        Liste de chunks avec métadonnées
    """
    if not text:
        return []
    
    # Utilisation de NLTK pour découper en phrases
    sentences = sent_tokenize(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        # Si l'ajout de cette phrase dépasse la taille maximale et qu'on a déjà du contenu
        if current_size + sentence_size > CHUNK_SIZE and current_chunk:
            # Créer un chunk avec le contenu accumulé
            chunk_text = " ".join(current_chunk)
            chunk_id = f"{id_prefix}_{len(chunks)}" if id_prefix else f"chunk_{uuid.uuid4().hex[:8]}"
            
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "title": title,
                "size": current_size
            })
            
            # Garder les dernières phrases pour le chevauchement
            overlap_size = 0
            overlap_chunks = []
            
            # Parcourir les phrases en sens inverse jusqu'à atteindre le chevauchement souhaité
            for s in reversed(current_chunk):
                if overlap_size < CHUNK_OVERLAP:
                    overlap_chunks.insert(0, s)
                    overlap_size += len(s)
                else:
                    break
            
            # Réinitialiser avec le chevauchement
            current_chunk = overlap_chunks
            current_size = overlap_size
        
        # Ajouter la phrase au chunk actuel
        current_chunk.append(sentence)
        current_size += sentence_size
    
    # Ajouter le dernier chunk s'il contient du texte
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunk_id = f"{id_prefix}_{len(chunks)}" if id_prefix else f"chunk_{uuid.uuid4().hex[:8]}"
        
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "title": title,
            "size": current_size
        })
    
    return chunks

async def extract_and_process_codes(search_terms: List[str]):
    """Extrait et traite les données des codes juridiques"""
    logger.info(f"Extraction des codes juridiques avec {len(search_terms)} termes de recherche")
    
    total_chunks = []
    total_documents = 0
    
    for term in tqdm(search_terms, desc="Extraction des codes"):
        try:
            # Extraction depuis l'API Légifrance
            response = await legifrance_api.search_codes(query=term, page=1, page_size=MAX_RESULTS_PER_QUERY)
            
            if not response or "results" not in response:
                logger.warning(f"Aucun résultat trouvé pour le terme '{term}' dans les codes")
                continue
                
            results = response.get("results", [])
            logger.info(f"Trouvé {len(results)} articles de code pour le terme '{term}'")
            
            for item in results:
                doc_id = item.get("id", "")
                title = item.get("title", "")
                content = item.get("content", "")
                doc_type = item.get("type", "code")
                date = item.get("date", datetime.now().strftime("%Y-%m-%d"))
                url = item.get("url", "")
                metadata = item.get("metadata", {})
                
                # Si le contenu est manquant, passer à l'élément suivant
                if not content:
                    continue
                
                # Découpage du texte en chunks
                document_chunks = chunk_text(
                    text=content,
                    title=title,
                    id_prefix=doc_id
                )
                
                # Enrichissement des métadonnées pour chaque chunk
                for i, chunk in enumerate(document_chunks):
                    chunk_metadata = {
                        "original_id": doc_id,
                        "chunk_index": i,
                        "total_chunks": len(document_chunks),
                        "type": doc_type,
                        "domain": "code",
                        "subdomain": metadata.get("code", "").lower() if metadata.get("code") else "",
                        "date": date,
                        "url": url,
                        "search_term": term
                    }
                    
                    # Ajouter les métadonnées spécifiques au code
                    if metadata:
                        chunk_metadata.update({
                            "code_name": metadata.get("code", ""),
                            "section": metadata.get("section", ""),
                        })
                    
                    chunk["metadata"] = chunk_metadata
                    total_chunks.append(chunk)
                
                total_documents += 1
            
            # Pause pour éviter le rate limiting
            await asyncio.sleep(EXTRACTION_DELAY)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du code pour le terme '{term}': {str(e)}")
    
    logger.success(f"Extraction des codes terminée. Total: {total_documents} documents, {len(total_chunks)} chunks")
    return total_chunks

async def extract_and_process_jurisprudence(search_terms: List[str]):
    """Extrait et traite les données de jurisprudence"""
    logger.info(f"Extraction de la jurisprudence avec {len(search_terms)} termes de recherche")
    
    total_chunks = []
    total_documents = 0
    
    for term in tqdm(search_terms, desc="Extraction de la jurisprudence"):
        try:
            # Extraction depuis l'API Légifrance
            response = await legifrance_api.search_jurisprudence(
                query=term, 
                page=1, 
                page_size=MAX_RESULTS_PER_QUERY, 
                sort="date desc"
            )
            
            if not response or "results" not in response:
                logger.warning(f"Aucun résultat trouvé pour le terme '{term}' dans la jurisprudence")
                continue
                
            results = response.get("results", [])
            logger.info(f"Trouvé {len(results)} décisions de jurisprudence pour le terme '{term}'")
            
            for item in results:
                doc_id = item.get("id", "")
                title = item.get("title", "")
                content = item.get("content", "")
                doc_type = item.get("type", "jurisprudence")
                date = item.get("date", datetime.now().strftime("%Y-%m-%d"))
                url = item.get("url", "")
                metadata = item.get("metadata", {})
                
                # Si le contenu est manquant, passer à l'élément suivant
                if not content:
                    continue
                
                # Découpage du texte en chunks
                document_chunks = chunk_text(
                    text=content,
                    title=title,
                    id_prefix=doc_id
                )
                
                # Enrichissement des métadonnées pour chaque chunk
                for i, chunk in enumerate(document_chunks):
                    chunk_metadata = {
                        "original_id": doc_id,
                        "chunk_index": i,
                        "total_chunks": len(document_chunks),
                        "type": doc_type,
                        "domain": "jurisprudence",
                        "subdomain": metadata.get("juridiction", "").lower() if metadata.get("juridiction") else "",
                        "date": date,
                        "url": url,
                        "search_term": term
                    }
                    
                    # Ajouter les métadonnées spécifiques à la jurisprudence
                    if metadata:
                        chunk_metadata.update({
                            "juridiction": metadata.get("juridiction", ""),
                            "formation": metadata.get("formation", ""),
                            "solution": metadata.get("solution", "")
                        })
                    
                    chunk["metadata"] = chunk_metadata
                    total_chunks.append(chunk)
                
                total_documents += 1
            
            # Pause pour éviter le rate limiting
            await asyncio.sleep(EXTRACTION_DELAY)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de la jurisprudence pour le terme '{term}': {str(e)}")
    
    logger.success(f"Extraction de la jurisprudence terminée. Total: {total_documents} documents, {len(total_chunks)} chunks")
    return total_chunks

async def store_chunks_in_qdrant(chunks: List[Dict[str, Any]], qdrant_client):
    """Stocke les chunks dans la collection Qdrant"""
    from sentence_transformers import SentenceTransformer
    from qdrant_client.http import models
    import hashlib
    
    # Récupération du modèle d'embedding
    model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2"))
    
    total_chunks = len(chunks)
    logger.info(f"Vectorisation et stockage de {total_chunks} chunks dans Qdrant")
    
    batch_size = 50  # Traitement par lots pour optimiser les performances
    success_count = 0
    
    for i in tqdm(range(0, total_chunks, batch_size), desc="Stockage dans Qdrant"):
        batch = chunks[i:i+batch_size]
        points = []
        
        for chunk in batch:
            try:
                # Générer un ID numérique pour Qdrant
                chunk_id = chunk["id"]
                hash_obj = hashlib.md5(chunk_id.encode())
                numeric_id = abs(int(hash_obj.hexdigest(), 16) % (2**31 - 1))
                
                # Générer l'embedding du texte
                embedding = model.encode(chunk["text"]).tolist()
                
                # Préparer les données pour Qdrant
                points.append(
                    models.PointStruct(
                        id=numeric_id,
                        vector=embedding,
                        payload={
                            "original_id": chunk["id"],
                            "title": chunk["title"],
                            "content": chunk["text"],
                            "type": chunk["metadata"].get("type", "unknown"),
                            "domain": chunk["metadata"].get("domain", "unknown"),
                            "subdomain": chunk["metadata"].get("subdomain", ""),
                            "date": chunk["metadata"].get("date", ""),
                            "url": chunk["metadata"].get("url", ""),
                            "metadata": chunk["metadata"]
                        }
                    )
                )
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Erreur lors de la préparation du chunk {chunk['id']}: {str(e)}")
        
        # Stocker le lot dans Qdrant
        if points:
            try:
                qdrant_client.upsert(
                    collection_name=NEW_COLLECTION_NAME,
                    points=points
                )
            except Exception as e:
                logger.error(f"Erreur lors du stockage du lot dans Qdrant: {str(e)}")
        
        # Pause pour éviter de surcharger le système
        await asyncio.sleep(0.1)
    
    logger.success(f"Stockage dans Qdrant terminé. {success_count}/{total_chunks} chunks stockés avec succès.")
    return success_count

async def main():
    """Fonction principale d'extraction et de traitement"""
    try:
        # Vérification des variables d'environnement
        if not os.getenv("PISTE_API_KEY") or not os.getenv("PISTE_SECRET_KEY"):
            logger.warning("Clés API Légifrance non configurées. Utilisation des données de test.")
            use_mock = input("Continuer avec les données de test? (o/n): ").lower()
            if use_mock != 'o':
                logger.info("Extraction annulée. Configurez les clés API dans le fichier .env")
                return
        
        # Configuration de la collection Qdrant
        qdrant_client = await setup_qdrant_collection()
        
        # Extraction et traitement des codes
        logger.info("=== Extraction des Codes Juridiques ===")
        code_terms = LEGAL_DOMAINS["codes"] + list(LEGAL_CONCEPTS.keys())
        code_chunks = await extract_and_process_codes(code_terms)
        
        # Stockage des chunks de codes dans Qdrant
        if code_chunks:
            logger.info(f"Stockage de {len(code_chunks)} chunks de codes dans Qdrant")
            await store_chunks_in_qdrant(code_chunks, qdrant_client)
        
        # Extraction et traitement de la jurisprudence
        logger.info("=== Extraction de la Jurisprudence ===")
        jurisprudence_terms = LEGAL_DOMAINS["jurisprudence"]
        for domain, concepts in LEGAL_CONCEPTS.items():
            jurisprudence_terms.extend(concepts)
        
        jurisprudence_chunks = await extract_and_process_jurisprudence(jurisprudence_terms)
        
        # Stockage des chunks de jurisprudence dans Qdrant
        if jurisprudence_chunks:
            logger.info(f"Stockage de {len(jurisprudence_chunks)} chunks de jurisprudence dans Qdrant")
            await store_chunks_in_qdrant(jurisprudence_chunks, qdrant_client)
        
        # Statistiques finales
        total_chunks = len(code_chunks) + len(jurisprudence_chunks)
        logger.success(f"Extraction et traitement terminés. Total: {total_chunks} chunks stockés.")
        
        # Sauvegarde des informations dans un fichier JSON
        extraction_info = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "collection": NEW_COLLECTION_NAME,
            "total_chunks": total_chunks,
            "code_chunks": len(code_chunks),
            "jurisprudence_chunks": len(jurisprudence_chunks),
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP
        }
        
        with open("extraction_stats.json", "w", encoding="utf-8") as f:
            json.dump(extraction_info, f, indent=2, ensure_ascii=False)
        
        logger.info("Informations d'extraction sauvegardées dans extraction_stats.json")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction: {str(e)}")

if __name__ == "__main__":
    # Configuration du logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("legifrance_extraction.log", rotation="100 MB", level="DEBUG")
    
    # Exécution de la fonction principale
    asyncio.run(main()) 