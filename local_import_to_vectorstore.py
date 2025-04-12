#!/usr/bin/env python3
"""
Script pour traiter les fichiers JSON téléchargés et les ajouter à la base vectorielle
"""

import os
import sys
import json
import argparse
import glob
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Chemin vers le répertoire parent pour l'import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Répertoire des données juridiques
LEGAL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legal_data")

def list_json_files():
    """Liste tous les fichiers JSON dans le répertoire des données"""
    json_pattern = os.path.join(LEGAL_DATA_DIR, "*.json")
    files = glob.glob(json_pattern)
    
    if not files:
        print(f"Aucun fichier JSON trouvé dans {LEGAL_DATA_DIR}")
        return []
    
    print(f"Trouvé {len(files)} fichiers JSON:")
    for i, file in enumerate(files):
        # Afficher le nom du fichier uniquement, pas le chemin complet
        filename = os.path.basename(file)
        print(f"{i+1}. {filename}")
        
    return files

def process_file(filepath, batch_size=1, dry_run=False):
    """Traite un fichier JSON et importe les données dans la base vectorielle"""
    try:
        filename = os.path.basename(filepath)
        print(f"Traitement du fichier: {filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'results' not in data or not data['results']:
            print(f"Aucun résultat trouvé dans le fichier {filename}")
            return 0
            
        print(f"Le fichier contient {len(data['results'])} documents")
        
        if dry_run:
            print(f"Mode simulation (dry run) - Aucun document ne sera importé")
            return 0
            
        # Charger la classe VectorStore uniquement si nécessaire (pas en mode dry_run)
        from app.utils.vector_store import vector_store
        
        if not vector_store or not vector_store.is_functional:
            print(f"La base vectorielle n'est pas disponible ou non fonctionnelle")
            return 0
            
        imported_count = 0
        
        # Détecter le type de données (codes ou jurisprudence) à partir du nom de fichier
        is_jurisprudence = "jurisprudence" in filename
        doc_type = "jurisprudence" if is_jurisprudence else "loi"
        
        # Importer les documents par lots
        for i, result in enumerate(data['results']):
            if i > 0 and i % batch_size == 0:
                print(f"Pause après le lot de {batch_size} documents...")
                import time
                time.sleep(2)  # Pause pour libérer la mémoire
                
                # Force la libération de la mémoire
                import gc
                gc.collect()
            
            try:
                # Extraire les informations pertinentes
                doc_id = str(uuid.uuid4())  # Générer un nouvel ID
                
                if is_jurisprudence:
                    # Format pour la jurisprudence
                    title = result.get('title', 'Sans titre')
                    content = result.get('text', '')
                    date = result.get('date', datetime.now().strftime("%Y-%m-%d"))
                    url = result.get('url', '')
                    metadata = {
                        "source": "legifrance",
                        "type": "jurisprudence",
                        "juridiction": result.get('jurisdiction', {}).get('label', ''),
                        "formation": result.get('formation', ''),
                        "number": result.get('number', '')
                    }
                else:
                    # Format pour les codes/lois
                    title = result.get('title', 'Sans titre')
                    content = result.get('text', '')
                    date = result.get('date', datetime.now().strftime("%Y-%m-%d"))
                    url = result.get('url', '')
                    
                    code_info = result.get('code', {})
                    metadata = {
                        "source": "legifrance",
                        "type": "code",
                        "code": code_info.get('title', '') if code_info else '',
                        "section": result.get('context', ''),
                        "number": result.get('num', '')
                    }
                
                # Ajouter le document à la base vectorielle
                print(f"Ajout du document: {title}")
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
                    imported_count += 1
                    print(f"Document {i+1}/{len(data['results'])} importé avec succès: {title}")
                else:
                    print(f"Échec de l'importation du document {i+1}/{len(data['results'])}: {title}")
                    
            except Exception as e:
                print(f"Erreur lors de l'importation du document {i+1}: {str(e)}")
        
        print(f"Importation terminée. {imported_count}/{len(data['results'])} documents importés")
        return imported_count
        
    except Exception as e:
        print(f"Erreur lors du traitement du fichier {filepath}: {str(e)}")
        return 0

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Importer des données juridiques dans la base vectorielle")
    parser.add_argument("--file", help="Chemin vers un fichier JSON spécifique à traiter")
    parser.add_argument("--batch", type=int, default=1, help="Nombre de documents à traiter par lot (défaut: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Mode simulation (ne pas importer réellement)")
    
    args = parser.parse_args()
    
    # Vérifier si le répertoire des données existe
    if not os.path.exists(LEGAL_DATA_DIR):
        print(f"Le répertoire {LEGAL_DATA_DIR} n'existe pas")
        return False
    
    # Si un fichier spécifique est fourni
    if args.file:
        filepath = args.file
        if not os.path.isabs(filepath):  # Si chemin relatif
            filepath = os.path.join(LEGAL_DATA_DIR, filepath)
            
        if not os.path.exists(filepath):
            print(f"Le fichier {filepath} n'existe pas")
            return False
            
        print(f"Traitement du fichier: {filepath}")
        imported_count = process_file(filepath, args.batch, args.dry_run)
        print(f"Total importé: {imported_count} documents")
        
    else:
        # Lister tous les fichiers JSON
        files = list_json_files()
        
        if not files:
            return False
            
        total_imported = 0
        
        # Demander à l'utilisateur quel fichier traiter
        try:
            choice = input("Entrez le numéro du fichier à traiter (ou 'all' pour tous): ")
            
            if choice.lower() == 'all':
                for file in files:
                    imported_count = process_file(file, args.batch, args.dry_run)
                    total_imported += imported_count
                    print(f"Progression: {total_imported} documents importés")
            else:
                file_index = int(choice) - 1
                if 0 <= file_index < len(files):
                    imported_count = process_file(files[file_index], args.batch, args.dry_run)
                    total_imported += imported_count
                else:
                    print(f"Choix invalide. Entrez un nombre entre 1 et {len(files)}")
                    return False
                    
            print(f"Importation terminée. Total: {total_imported} documents importés")
            
        except ValueError:
            print("Veuillez entrer un nombre valide ou 'all'")
            return False
        except KeyboardInterrupt:
            print("\nOpération annulée par l'utilisateur")
            return False
    
    return True

if __name__ == "__main__":
    load_dotenv()  # Charger les variables d'environnement
    result = main()
    if not result:
        sys.exit(1) 