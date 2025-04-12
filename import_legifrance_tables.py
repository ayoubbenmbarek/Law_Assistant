#!/usr/bin/env python3
"""
Script pour importer les tables Légifrance et extraire les PDF pour Qdrant
"""

import os
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
import PyPDF2
import tempfile
import requests

# Configurer le logging
os.makedirs("logs", exist_ok=True)
logger.add("logs/import_tables.log", rotation="10 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

# Charger les variables d'environnement
load_dotenv()

async def main():
    # Importer les classes nécessaires ici pour éviter les problèmes de dépendances circulaires
    from app.data.legifrance_api import LegifranceAPI
    from app.utils.vector_store import vector_store
    
    # Analyser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Importer les tables Légifrance en PDF")
    parser.add_argument("--start-year", type=int, help="Année de début")
    parser.add_argument("--end-year", type=int, help="Année de fin", 
                        default=datetime.now().year)
    parser.add_argument("--batch-size", type=int, default=10, 
                        help="Taille des lots pour le traitement")
    parser.add_argument("--sandbox", action="store_true", default=True,
                        help="Utiliser l'environnement sandbox de l'API")
    args = parser.parse_args()
    
    start_year = args.start_year
    end_year = args.end_year
    batch_size = args.batch_size
    use_sandbox = args.sandbox
    
    logger.info(f"Démarrage de l'import des tables Légifrance: {start_year or 'début'}-{end_year}")
    logger.info(f"Environnement API: {'sandbox' if use_sandbox else 'production'}")
    
    # Initialiser le client Légifrance
    legifrance = LegifranceAPI(use_sandbox=use_sandbox)
    
    # Récupérer les tables et extraire le contenu PDF
    tables = await get_tables_and_extract_pdf(legifrance, start_year, end_year)
    
    if not tables:
        logger.warning("Aucune table récupérée")
        return
    
    logger.info(f"{len(tables)} tables récupérées avec contenu PDF")
    
    # Ajouter les documents à la base vectorielle par lots
    imported_count = 0
    for i in range(0, len(tables), batch_size):
        batch = tables[i:i+batch_size]
        logger.info(f"Traitement du lot {i//batch_size + 1}/{(len(tables) + batch_size - 1)//batch_size}")
        
        try:
            # Ajouter à Qdrant un par un (la méthode add_documents n'existe pas)
            for doc in batch:
                success = vector_store.add_document(
                    doc_id=doc["id"],
                    title=doc["title"],
                    content=doc["content"],
                    doc_type="table",
                    date=doc.get("metadata", {}).get("date", ""),
                    url=doc["url"],
                    metadata=doc["metadata"]
                )
                if success:
                    imported_count += 1
            
            logger.info(f"{i+len(batch)}/{len(tables)} documents traités")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du lot à la base vectorielle: {str(e)}")
            # Continuer avec le lot suivant
    
    logger.info(f"Import terminé! {imported_count} documents ajoutés à la base vectorielle.")

async def get_tables_and_extract_pdf(legifrance, start_year=None, end_year=None):
    """
    Récupère les tables et extrait le contenu des PDF
    
    Args:
        legifrance: Instance du client LegifranceAPI
        start_year: Année de début (optionnelle)
        end_year: Année de fin (optionnelle)
        
    Returns:
        Liste des documents enrichis à partir des tables PDF
    """
    # Récupérer les tables
    logger.info(f"Récupération des tables de {start_year or 'début'} à {end_year or 'fin'}")
    
    try:
        response = await legifrance.get_tables(start_year, end_year)
        
        # Vérifier et transformer le format de la réponse
        tables = []
        
        # Vérifier si la réponse est au format attendu (objet JSON avec clé "tables")
        if isinstance(response, dict) and "tables" in response:
            tables = response["tables"]
            total_nb_result = response.get("totalNbResult", len(tables))
            logger.info(f"Réponse au format standard, {total_nb_result} tables trouvées")
        elif isinstance(response, list):
            tables = response
            logger.info(f"Réponse sous forme de liste, {len(tables)} tables trouvées")
        elif isinstance(response, dict):
            # Chercher les tables dans différentes structures possibles
            for key, value in response.items():
                if isinstance(value, list) and len(value) > 0:
                    logger.info(f"Utilisation de la liste trouvée sous la clé '{key}'")
                    tables = value
                    break
        
        if not tables:
            logger.warning("Aucune table trouvée dans la réponse API")
            return []
        
        logger.info(f"{len(tables)} tables trouvées à traiter")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tables: {str(e)}")
        return []
    
    # Traiter chaque table
    enriched_tables = []
    for i, table in enumerate(tables):
        logger.info(f"Traitement de la table {i+1}/{len(tables)}: {table.get('title', table.get('fileName', 'Sans titre'))}")
        
        # Récupérer les métadonnées
        table_id = table.get("id", f"table_{i}")
        year = table.get("year", table.get("number", table.get("fileName", "").split("_")[1] if "_" in table.get("fileName", "") else None))
        title = table.get("title", table.get("fileName", "Sans titre"))
        table_type = table.get("nature", table.get("type", "Inconnu"))
        
        # Vérifier si la table a une URL PDF
        pdf_url = table.get("pdfUrl", None)
        if not pdf_url and "pathToFile" in table:
            # Format alternatif observé dans certaines réponses
            path_to_file = table.get("pathToFile")
            if path_to_file:
                pdf_url = f"https://www.legifrance.gouv.fr/download/pdf/table{path_to_file}"
        
        if not pdf_url:
            logger.warning(f"Pas d'URL PDF pour la table {table_id}")
            continue
        
        # Télécharger le PDF
        try:
            logger.info(f"Téléchargement du PDF: {pdf_url}")
            pdf_data = await legifrance.download_pdf(pdf_url)
            
            # Extraire le texte du PDF
            pdf_text = extract_text_from_pdf(pdf_data)
            
            if pdf_text:
                logger.info(f"PDF extrait avec succès: {len(pdf_text)} caractères")
                
                # Segmenter le texte en chunks pour une meilleure recherche
                # Une approche simple: diviser par paragraphes non vides
                chunks = [p.strip() for p in pdf_text.split("\n\n") if len(p.strip()) > 50]
                
                # Créer un document pour chaque chunk significatif
                for j, chunk in enumerate(chunks):
                    enriched_tables.append({
                        "id": f"{table_id}_chunk_{j}",
                        "title": f"{title} - Extrait {j+1}",
                        "content": chunk,
                        "source": "legifrance_table_pdf",
                        "url": pdf_url,
                        "metadata": {
                            "origin": "legifrance",
                            "document_type": "table",
                            "year": year,
                            "table_type": table_type,
                            "full_title": title,
                            "chunk_id": j,
                            "total_chunks": len(chunks),
                            "date": table.get("date", str(year) if year else datetime.now().strftime("%Y-%m-%d")),
                            "nature": table.get("nature", "")
                        }
                    })
                
                logger.info(f"Table {table_id} segmentée en {len(chunks)} extraits")
            else:
                logger.warning(f"Aucun texte extrait du PDF pour la table {table_id}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du PDF {pdf_url}: {str(e)}")
    
    logger.info(f"Traitement terminé. {len(enriched_tables)} segments de document créés")
    return enriched_tables

def extract_text_from_pdf(pdf_data):
    """
    Extrait le texte d'un fichier PDF
    
    Args:
        pdf_data: Contenu binaire du PDF
        
    Returns:
        Texte extrait du PDF
    """
    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_data)
            temp_file_path = temp_file.name
        
        # Extraire le texte
        text = ""
        try:
            with open(temp_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"Extraction de {num_pages} pages PDF")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        return text
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte: {str(e)}")
        return ""

if __name__ == "__main__":
    asyncio.run(main())
