#!/usr/bin/env python3
"""
Script pour générer des embeddings à partir des données textuelles de Légifrance
et les ingérer dans une base de données vectorielle Qdrant.
"""

import os
import json
import time
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# Pour l'embedding
from sentence_transformers import SentenceTransformer
import torch

# Client Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Chargement des variables d'environnement
load_dotenv()

# Configuration
PROCESSED_DIR = Path("data/legifrance/processed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2")

# Configuration Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6339))
COLLECTION_NAME = "legifrance"
VECTOR_SIZE = 768  # Dépend du modèle d'embedding

# Nombre maximum de documents à traiter (None pour tous)
MAX_DOCS = None

def generate_numeric_id(text_id):
    """
    Génère un ID numérique à partir d'un ID textuel.
    
    Args:
        text_id (str): Identifiant textuel
        
    Returns:
        int: Identifiant numérique positif
    """
    # Utiliser MD5 pour créer un hash consistant
    hash_obj = hashlib.md5(text_id.encode('utf-8'))
    # Convertir en entier et prendre modulo pour assurer un entier positif
    return abs(int(hash_obj.hexdigest(), 16) % (2**31 - 1))

def load_chunks_data(file_path=None):
    """
    Charge les données de chunks prétraitées depuis un fichier JSON.
    
    Args:
        file_path (str, optional): Chemin du fichier JSON. Si None, utilise le chemin par défaut.
        
    Returns:
        list: Liste de dictionnaires contenant les chunks avec leur texte et métadonnées
    """
    if file_path is None:
        file_path = PROCESSED_DIR / "tables_chunks.json"
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier {file_path} introuvable. Exécutez d'abord explore_legifrance_data.py")
    
    print(f"Chargement des chunks depuis {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"Nombre total de chunks chargés: {len(chunks)}")
    
    # Limiter le nombre de documents si MAX_DOCS est défini
    if MAX_DOCS and len(chunks) > MAX_DOCS:
        print(f"Limitation à {MAX_DOCS} chunks pour test")
        chunks = chunks[:MAX_DOCS]
    
    return chunks

def generate_embeddings(chunks, batch_size=32):
    """
    Génère des embeddings pour les chunks textuels.
    
    Args:
        chunks (list): Liste de dictionnaires contenant les chunks
        batch_size (int): Taille des lots pour l'embedding
        
    Returns:
        tuple: Liste de chunks avec embeddings et embeddings séparés
    """
    print(f"Chargement du modèle d'embedding: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Utiliser GPU si disponible
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Utilisation de {device} pour l'embedding")
    model = model.to(device)
    
    texts = [chunk["text"] for chunk in chunks]
    
    # Générer les embeddings par lots
    print("Génération des embeddings...")
    all_embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size)):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = model.encode(batch_texts, show_progress_bar=False)
        all_embeddings.extend(batch_embeddings)
    
    # Ajouter les embeddings aux chunks
    for i, embedding in enumerate(all_embeddings):
        # Convertir si nécessaire avant de sérialiser
        if isinstance(embedding, np.ndarray):
            embedding_list = embedding.tolist()
        else:
            embedding_list = embedding
        chunks[i]["embedding"] = embedding_list
    
    print(f"Embeddings générés pour {len(all_embeddings)} chunks")
    return chunks, all_embeddings

def setup_qdrant_collection():
    """
    Configure la collection Qdrant pour les données Légifrance.
    
    Returns:
        QdrantClient: Client Qdrant configuré
    """
    print(f"Connexion à Qdrant sur {QDRANT_URL}:{QDRANT_PORT}")
    
    try:
        client = QdrantClient(url=QDRANT_URL, port=QDRANT_PORT)
        
        # Vérifier si la collection existe
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if COLLECTION_NAME in collection_names:
            print(f"Collection '{COLLECTION_NAME}' existe déjà")
            # Récupérer les informations sur la collection
            collection_info = client.get_collection(COLLECTION_NAME)
            print(f"Taille actuelle de la collection: {collection_info.vectors_count} vecteurs")
            
            # Option pour recréer la collection
            recreate = input("Voulez-vous recréer la collection (tous les documents existants seront supprimés)? (o/n): ")
            if recreate.lower() == 'o':
                print(f"Suppression de la collection '{COLLECTION_NAME}'")
                client.delete_collection(COLLECTION_NAME)
                create_collection = True
            else:
                create_collection = False
        else:
            create_collection = True
        
        if create_collection:
            print(f"Création de la collection '{COLLECTION_NAME}'")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE
                )
            )
            
            # Ajouter des index pour les métadonnées pour des recherches plus rapides
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="metadata.year",
                field_schema=models.PayloadSchemaType.INTEGER
            )
            
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="metadata.type",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="metadata.origine",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
        return client
    
    except Exception as e:
        print(f"Erreur lors de la configuration de Qdrant: {str(e)}")
        raise

def ingest_embeddings_to_qdrant(client, chunks_with_embeddings):
    """
    Ingère les embeddings dans Qdrant.
    
    Args:
        client (QdrantClient): Client Qdrant
        chunks_with_embeddings (list): Chunks avec les embeddings générés
        
    Returns:
        int: Nombre de points ingérés
    """
    print(f"Préparation des données pour ingestion dans Qdrant")
    
    # Créer les points Qdrant
    qdrant_points = []
    
    for chunk in chunks_with_embeddings:
        # Créer un ID numérique unique pour chaque chunk
        point_id = generate_numeric_id(chunk["metadata"]["chunk_id"])
        
        # Préparer le point
        qdrant_points.append(
            models.PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload={
                    "text": chunk["text"],
                    "metadata": chunk["metadata"]
                }
            )
        )
    
    # Ingérer les points par lots
    batch_size = 100
    total_ingested = 0
    
    print(f"Ingestion de {len(qdrant_points)} points dans Qdrant...")
    
    for i in tqdm(range(0, len(qdrant_points), batch_size)):
        batch = qdrant_points[i:i+batch_size]
        
        operation_info = client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        
        total_ingested += len(batch)
    
    print(f"Ingestion terminée: {total_ingested} points ajoutés à la collection '{COLLECTION_NAME}'")
    return total_ingested

def test_qdrant_search(client, query_text, top_k=5):
    """
    Teste la recherche dans Qdrant avec une requête texte.
    
    Args:
        client (QdrantClient): Client Qdrant
        query_text (str): Texte de la requête
        top_k (int): Nombre de résultats à retourner
        
    Returns:
        list: Résultats de la recherche
    """
    print(f"Test de recherche pour: '{query_text}'")
    
    # Générer l'embedding pour la requête
    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode(query_text)
    
    # Effectuer la recherche
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k
    )
    
    print(f"Résultats de recherche:")
    for i, result in enumerate(search_results):
        print(f"\n--- Résultat {i+1} (score: {result.score:.4f}) ---")
        print(f"Source: {result.payload['metadata']['source']}")
        print(f"Type: {result.payload['metadata']['type']}")
        print(f"Année: {result.payload['metadata']['year']}")
        print(f"Extrait: {result.payload['text'][:200]}...")
    
    return search_results

def main():
    """
    Fonction principale pour générer des embeddings et les ingérer dans Qdrant.
    """
    print("=== GÉNÉRATION D'EMBEDDINGS ET INGESTION DANS QDRANT ===")
    
    # Charger les données prétraitées
    chunks = load_chunks_data()
    
    # Générer les embeddings
    chunks_with_embeddings, embeddings = generate_embeddings(chunks)
    
    # Configurer Qdrant
    client = setup_qdrant_collection()
    
    # Ingérer les embeddings dans Qdrant
    total_ingested = ingest_embeddings_to_qdrant(client, chunks_with_embeddings)
    
    # Tester la recherche
    if total_ingested > 0:
        test_query = input("\nEntrez une requête de test (ou appuyez sur Entrée pour sauter): ")
        if test_query:
            test_qdrant_search(client, test_query)
    
    print("\nProcessus d'ingestion terminé avec succès!")

if __name__ == "__main__":
    main() 