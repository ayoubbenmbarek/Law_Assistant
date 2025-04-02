import os
import asyncio
import datetime
from typing import Dict, List, Any, Optional, Union
from loguru import logger
from dotenv import load_dotenv

# Importer les services d'ingestion de données
from app.data.legifrance_api import legifrance_api
from app.data.eurlex_api import eurlex_api
from app.data.conseil_constitutionnel_api import conseil_constitutionnel_api
from app.data.etl_manager import etl_manager
from app.data.data_enrichment import data_enrichment

# Importer les services de base de données
from app.utils.vector_store import vector_store
from app.utils.database import get_db, SessionLocal

# Charger les variables d'environnement
load_dotenv()

# Configuration
PIPELINE_BATCH_SIZE = int(os.getenv("PIPELINE_BATCH_SIZE", "100"))
IMPORT_STATS_PATH = os.getenv("IMPORT_STATS_PATH", "./data/stats")

class PipelineManager:
    """
    Gestionnaire de pipeline pour coordonner les processus d'ingestion,
    d'enrichissement et de stockage des données juridiques
    """
    
    def __init__(self):
        """Initialiser le gestionnaire de pipeline"""
        self.sources = {
            "legifrance": {
                "name": "Légifrance API",
                "service": legifrance_api,
                "methods": ["import_codes", "import_jurisprudence"]
            },
            "eurlex": {
                "name": "EUR-Lex API",
                "service": eurlex_api,
                "methods": ["import_regulations"]
            },
            "conseil_constitutionnel": {
                "name": "Conseil Constitutionnel API",
                "service": conseil_constitutionnel_api,
                "methods": ["import_decisions"]
            },
            "web_sources": {
                "name": "Sources Web (ETL)",
                "service": etl_manager,
                "methods": ["run_extraction"]
            }
        }
        
        # Statistiques d'importation
        self.import_stats = {
            "total_imported": 0,
            "start_time": None,
            "end_time": None,
            "sources_stats": {},
            "error_count": 0
        }
    
    async def run_full_pipeline(self):
        """
        Exécuter le pipeline complet d'ingestion et d'enrichissement
        pour toutes les sources configurées
        """
        logger.info("Démarrage du pipeline complet d'ingestion des données juridiques")
        
        # Initialiser les statistiques
        self.import_stats = {
            "total_imported": 0,
            "start_time": datetime.datetime.now().isoformat(),
            "sources_stats": {},
            "error_count": 0
        }
        
        try:
            # 1. Légifrance API
            if "legifrance" in self.sources:
                logger.info("Importation des données depuis Légifrance")
                await self._run_source_import("legifrance")
            
            # 2. EUR-Lex API
            if "eurlex" in self.sources:
                logger.info("Importation des données depuis EUR-Lex")
                await self._run_source_import("eurlex")
            
            # 3. Conseil Constitutionnel API
            if "conseil_constitutionnel" in self.sources:
                logger.info("Importation des données depuis le Conseil Constitutionnel")
                await self._run_source_import("conseil_constitutionnel")
            
            # 4. Sources Web (ETL)
            if "web_sources" in self.sources:
                logger.info("Importation des données depuis les sources web par ETL")
                await self._run_source_import("web_sources")
            
            # Finaliser les statistiques
            self.import_stats["end_time"] = datetime.datetime.now().isoformat()
            
            # Calculer la durée totale
            start = datetime.datetime.fromisoformat(self.import_stats["start_time"])
            end = datetime.datetime.fromisoformat(self.import_stats["end_time"])
            duration = (end - start).total_seconds()
            self.import_stats["duration_seconds"] = duration
            
            # Sauvegarder les statistiques
            self._save_import_stats()
            
            logger.info(f"Pipeline d'ingestion terminé. {self.import_stats['total_imported']} documents importés en {duration} secondes.")
            return self.import_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du pipeline complet: {str(e)}")
            self.import_stats["error"] = str(e)
            self.import_stats["end_time"] = datetime.datetime.now().isoformat()
            self._save_import_stats()
            raise
    
    async def run_specific_source(self, source_id: str, method: Optional[str] = None, **kwargs):
        """
        Exécuter le pipeline pour une source spécifique
        
        Args:
            source_id: Identifiant de la source (legifrance, eurlex, etc.)
            method: Méthode spécifique à appeler (optionnel)
            **kwargs: Paramètres supplémentaires à passer à la méthode
        """
        if source_id not in self.sources:
            raise ValueError(f"Source inconnue: {source_id}")
        
        logger.info(f"Démarrage du pipeline pour {self.sources[source_id]['name']}")
        
        # Initialiser les statistiques
        self.import_stats = {
            "total_imported": 0,
            "start_time": datetime.datetime.now().isoformat(),
            "sources_stats": {},
            "error_count": 0
        }
        
        try:
            await self._run_source_import(source_id, method, **kwargs)
            
            # Finaliser les statistiques
            self.import_stats["end_time"] = datetime.datetime.now().isoformat()
            
            # Calculer la durée totale
            start = datetime.datetime.fromisoformat(self.import_stats["start_time"])
            end = datetime.datetime.fromisoformat(self.import_stats["end_time"])
            duration = (end - start).total_seconds()
            self.import_stats["duration_seconds"] = duration
            
            # Sauvegarder les statistiques
            self._save_import_stats()
            
            logger.info(f"Pipeline pour {self.sources[source_id]['name']} terminé. {self.import_stats['total_imported']} documents importés en {duration} secondes.")
            return self.import_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du pipeline pour {source_id}: {str(e)}")
            self.import_stats["error"] = str(e)
            self.import_stats["end_time"] = datetime.datetime.now().isoformat()
            self._save_import_stats()
            raise
    
    async def _run_source_import(self, source_id: str, specific_method: Optional[str] = None, **kwargs):
        """
        Exécuter l'importation à partir d'une source spécifique
        
        Args:
            source_id: Identifiant de la source
            specific_method: Méthode spécifique à appeler (optionnel)
            **kwargs: Paramètres supplémentaires à passer à la méthode
        """
        source = self.sources[source_id]
        service = source["service"]
        
        # Initialiser les statistiques pour cette source
        self.import_stats["sources_stats"][source_id] = {
            "name": source["name"],
            "documents_imported": 0,
            "methods": {}
        }
        
        try:
            # Déterminer les méthodes à appeler
            methods_to_call = [specific_method] if specific_method else source["methods"]
            
            for method_name in methods_to_call:
                if not hasattr(service, method_name):
                    logger.warning(f"Méthode {method_name} non trouvée dans le service {source_id}")
                    continue
                
                # Initialiser les statistiques pour cette méthode
                self.import_stats["sources_stats"][source_id]["methods"][method_name] = {
                    "documents_imported": 0,
                    "start_time": datetime.datetime.now().isoformat()
                }
                
                # Appeler la méthode
                method = getattr(service, method_name)
                
                try:
                    # Appel de la méthode avec les paramètres supplémentaires
                    documents = await method(**kwargs) if kwargs else await method()
                    
                    # S'assurer que le résultat est une liste
                    if not isinstance(documents, list):
                        logger.warning(f"Résultat non attendu de {method_name}: ce n'est pas une liste. Conversion...")
                        documents = [documents] if documents else []
                    
                    # Traiter les documents par lots
                    total_docs = len(documents)
                    batch_size = PIPELINE_BATCH_SIZE
                    
                    for i in range(0, total_docs, batch_size):
                        batch = documents[i:i+batch_size]
                        logger.info(f"Traitement du lot {i//batch_size + 1}/{(total_docs+batch_size-1)//batch_size} ({len(batch)} documents)")
                        
                        # Enrichir les documents
                        enriched_batch = await data_enrichment.enrich_documents(batch)
                        
                        # Importer dans la base vectorielle
                        imported_count = await self._import_to_vector_store(enriched_batch)
                        
                        # Mettre à jour les statistiques
                        self.import_stats["sources_stats"][source_id]["methods"][method_name]["documents_imported"] += imported_count
                        self.import_stats["sources_stats"][source_id]["documents_imported"] += imported_count
                        self.import_stats["total_imported"] += imported_count
                    
                    # Finaliser les statistiques de la méthode
                    self.import_stats["sources_stats"][source_id]["methods"][method_name]["end_time"] = datetime.datetime.now().isoformat()
                    start = datetime.datetime.fromisoformat(self.import_stats["sources_stats"][source_id]["methods"][method_name]["start_time"])
                    end = datetime.datetime.fromisoformat(self.import_stats["sources_stats"][source_id]["methods"][method_name]["end_time"])
                    duration = (end - start).total_seconds()
                    self.import_stats["sources_stats"][source_id]["methods"][method_name]["duration_seconds"] = duration
                    
                    logger.info(f"Méthode {method_name} terminée: {self.import_stats['sources_stats'][source_id]['methods'][method_name]['documents_imported']} documents importés")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'appel de la méthode {method_name}: {str(e)}")
                    self.import_stats["sources_stats"][source_id]["methods"][method_name]["error"] = str(e)
                    self.import_stats["error_count"] += 1
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation depuis {source_id}: {str(e)}")
            self.import_stats["sources_stats"][source_id]["error"] = str(e)
            self.import_stats["error_count"] += 1
    
    async def _import_to_vector_store(self, documents: List[Dict[str, Any]]) -> int:
        """
        Importer les documents dans la base vectorielle
        
        Args:
            documents: Liste des documents à importer
            
        Returns:
            Nombre de documents importés avec succès
        """
        if not documents:
            return 0
            
        imported_count = 0
        
        for doc in documents:
            try:
                # S'assurer que tous les champs requis sont présents
                if not all(field in doc for field in ["id", "title", "content"]):
                    logger.warning(f"Document incomplet, champs manquants: {doc.get('id', 'ID inconnu')}")
                    continue
                
                # Déterminer le type du document
                doc_type = doc.get("type", "autre")
                if isinstance(doc_type, str):
                    doc_type_str = doc_type
                else:
                    # Si c'est un objet Enum, récupérer la valeur
                    doc_type_str = getattr(doc_type, "value", str(doc_type))
                
                # Ajouter le document à la base vectorielle
                vector_store.add_document(
                    doc_id=doc["id"],
                    title=doc["title"],
                    content=doc["content"],
                    doc_type=doc_type_str,
                    date=doc.get("date", datetime.datetime.now().strftime("%Y-%m-%d")),
                    url=doc.get("url", ""),
                    metadata=doc.get("metadata", {})
                )
                
                # Enregistrer également dans la base de données relationnelle si nécessaire
                # self._save_to_database(doc)
                
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Erreur lors de l'importation du document {doc.get('id', 'ID inconnu')}: {str(e)}")
                self.import_stats["error_count"] += 1
        
        return imported_count
    
    def _save_to_database(self, document: Dict[str, Any]):
        """
        Sauvegarder le document dans la base de données relationnelle
        
        Args:
            document: Document à sauvegarder
        """
        # Obtenir une session de base de données
        db = SessionLocal()
        
        try:
            # TODO: Implémentation de la sauvegarde en base de données
            # Cette méthode peut être implémentée plus tard pour sauvegarder
            # les documents dans la base de données relationnelle
            pass
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde en base de données: {str(e)}")
            
        finally:
            db.close()
    
    def _save_import_stats(self):
        """Sauvegarder les statistiques d'importation"""
        try:
            import json
            from pathlib import Path
            
            # Créer le répertoire s'il n'existe pas
            stats_dir = Path(IMPORT_STATS_PATH)
            stats_dir.mkdir(parents=True, exist_ok=True)
            
            # Nom de fichier avec horodatage
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = stats_dir / f"import_stats_{timestamp}.json"
            
            # Sauvegarder en JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.import_stats, f, ensure_ascii=False, indent=4)
                
            logger.info(f"Statistiques d'importation sauvegardées: {filename}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des statistiques: {str(e)}")

# Créer l'instance du gestionnaire de pipeline
pipeline_manager = PipelineManager() 