#!/usr/bin/env python
"""
Script pour importer des documents enrichis dans la base vectorielle
"""

import json
import asyncio
from app.utils.vector_store import vector_store

async def import_data():
    """Importe les documents depuis un fichier JSON dans la base vectorielle"""
    try:
        # Charger les documents depuis le fichier JSON
        file_path = 'legal_data/codes_enriched.json'
        print(f"Chargement des documents depuis {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        # Ajouter les documents dans la base vectorielle
        print(f"Importation de {len(documents)} documents dans la base vectorielle")
        
        # Importer chaque document individuellement
        count = 0
        for doc in documents:
            # Préparer les paramètres pour l'ajout du document
            doc_id = doc.get('titles', [{}])[0].get('cid', f"unknown_{count}")
            title = doc.get('titles', [{}])[0].get('title', 'Titre inconnu')
            content = doc.get('text', '')
            doc_type = 'code'
            date = doc.get('date', '').split('T')[0] if 'T' in doc.get('date', '') else doc.get('date', '')
            url = f"https://www.legifrance.gouv.fr/codes/id/{doc_id}"
            metadata = {
                'nature': doc.get('nature', ''),
                'origin': doc.get('origin', ''),
                'etat': doc.get('etat', ''),
                'themes': doc.get('themes', []),
                'mots_cles': doc.get('motsCles', [])
            }
            
            # Vérifier que les champs obligatoires sont présents
            if content:
                try:
                    # Note: vector_store.add_document n'est pas une coroutine async
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
                        count += 1
                        print(f"Document {count} ajouté: {title}")
                    else:
                        print(f"Échec de l'ajout du document: {title}")
                except Exception as e:
                    print(f"Erreur lors de l'ajout du document {title}: {str(e)}")
            else:
                print(f"Document ignoré (contenu vide): {title}")
        
        print(f"Importation terminée: {count} documents importés avec succès")
        
    except Exception as e:
        print(f"Erreur lors de l'importation: {str(e)}")

if __name__ == "__main__":
    asyncio.run(import_data()) 