import os
import asyncio
import datetime
import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from loguru import logger
from dotenv import load_dotenv

# Importer les services d'ingestion de données
from app.data.legifrance_api import legifrance_api
from app.data.eurlex_api import eurlex_api
from app.data.conseil_constitutionnel_api import conseil_constitutionnel_api
from app.data.etl_manager import etl_manager

# Try to import data_enrichment (optional)
try:
    from app.data.data_enrichment import data_enrichment
except ImportError:
    data_enrichment = None

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
            # Exécuter l'importation et obtenir le résultat
            import_result = await self._run_source_import(source_id, method, **kwargs)
            
            # Mettre à jour les statistiques avec le résultat
            if isinstance(import_result, dict) and "imported" in import_result:
                self.import_stats["total_imported"] = import_result["imported"]
                
                # Ajouter les statistiques spécifiques à la source
                if source_id not in self.import_stats["sources_stats"]:
                    self.import_stats["sources_stats"][source_id] = {
                        "name": self.sources[source_id]["name"],
                        "documents_imported": import_result["imported"],
                        "methods": {}
                    }
                
                # Ajouter les statistiques pour la méthode spécifique
                if method and "details" in import_result and method in import_result["details"]:
                    self.import_stats["sources_stats"][source_id]["methods"][method] = {
                        "documents_imported": import_result["details"][method],
                        "duration_seconds": import_result.get("time", 0)
                    }
            
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
    
    async def _run_source_import(self, source_id: str, method_name: str = None, **kwargs) -> Dict[str, Any]:
        """
        Exécute une méthode d'importation spécifique pour une source donnée
        
        Args:
            source_id: Identifiant de la source
            method_name: Nom de la méthode d'importation
            **kwargs: Options supplémentaires à passer à la méthode (limit, search_terms, etc.)
            
        Returns:
            Résultats de l'importation
        """
        start_time = time.time()
        total_imported = 0
        result = {"imported": 0, "errors": 0, "details": {}}
        
        try:
            # Obtenir la source
            source = self.sources[source_id]
            
            # Vérifier si la méthode demandée existe
            if not method_name:
                logger.error(f"Aucune méthode spécifiée pour la source {source_id}")
                return {"error": "Aucune méthode spécifiée", "imported": 0}
                
            if not hasattr(source["service"], method_name):
                logger.error(f"La méthode {method_name} n'existe pas pour la source {source_id}")
                return {"error": f"Méthode {method_name} non trouvée", "imported": 0}
            
            # Récupérer les options des kwargs
            options = kwargs.get('options', {})
            
            # Exécuter la méthode d'importation
            logger.info(f"Exécution de la méthode {method_name} pour {source_id}")
            method = getattr(source["service"], method_name)
            
            # Si des options sont spécifiées, les passer à la méthode
            if options:
                import_result = await method(**options)
            else:
                # Passer directement les kwargs (sans 'options')
                import_result = await method(**kwargs)
            
            # Vérifier le format du résultat
            if isinstance(import_result, list):
                documents = import_result
                imported_count = len(documents)
                logger.info(f"Méthode {method_name} a retourné {imported_count} documents")
            elif isinstance(import_result, dict) and 'imported_count' in import_result:
                # Si le résultat est un dictionnaire avec un compteur d'importation
                imported_count = import_result['imported_count']
                documents = []  # Pas de documents à traiter davantage
                logger.info(f"Méthode {method_name} a reporté {imported_count} documents importés")
                # Mettre à jour les statistiques et terminer
                result["imported"] = imported_count
                result["details"][method_name] = imported_count
                total_imported += imported_count
                
                elapsed_time = time.time() - start_time
                result["time"] = elapsed_time
                return result
            else:
                # Format non reconnu, essayer de convertir en liste
                logger.warning(f"Résultat non attendu de {method_name}: ce n'est pas une liste. Conversion...")
                if import_result:
                    documents = [import_result]
                    imported_count = 1
                else:
                    documents = []
                    imported_count = 0
            
            # Traiter les documents par lots
            batch_size = 10
            num_batches = (len(documents) + batch_size - 1) // batch_size if documents else 0
            
            for i in range(num_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, len(documents))
                batch = documents[start_idx:end_idx]
                
                logger.info(f"Traitement du lot {i+1}/{num_batches} ({len(batch)} documents)")
                
                # Enrichissement des documents si possible
                try:
                    if data_enrichment:
                        enriched_batch = await data_enrichment.enrich_documents(batch)
                        batch = enriched_batch
                    else:
                        logger.warning("Module d'enrichissement non disponible, utilisation des documents bruts")
                except Exception as e:
                    logger.warning(f"Échec d'enrichissement: {str(e)}")
                
                # Import dans la base vectorielle
                imported = await self._import_to_vector_store(batch)
                total_imported += imported
                
            # Résultat final
            result["imported"] = total_imported
            result["details"][method_name] = total_imported
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de {method_name} pour {source_id}: {str(e)}")
            logger.exception(e)
            result["error"] = str(e)
            result["details"][method_name] = 0
        
        elapsed_time = time.time() - start_time
        result["time"] = elapsed_time
        
        return result
    
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