import os
import argparse
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger
from dotenv import load_dotenv

# Importer les gestionnaires de données
from app.data.pipeline_manager import pipeline_manager
from app.data.etl_manager import etl_manager
from app.data.data_enrichment import data_enrichment
from app.utils.vector_store import vector_store

# Charger les variables d'environnement
load_dotenv()

class DataAdministrationCLI:
    """
    Interface en ligne de commande pour l'administration des données juridiques
    """
    
    def __init__(self):
        """Initialiser l'interface d'administration"""
        pass
    
    async def run_command(self, args):
        """
        Exécuter une commande basée sur les arguments passés
        
        Args:
            args: Arguments de la ligne de commande
        """
        command = args.command
        
        if command == "import":
            await self._handle_import(args)
        elif command == "enrich":
            await self._handle_enrichment(args)
        elif command == "search":
            await self._handle_search(args)
        elif command == "stats":
            await self._handle_stats(args)
        elif command == "export":
            await self._handle_export(args)
        elif command == "validate":
            await self._handle_validation(args)
        else:
            logger.error(f"Commande inconnue: {command}")
    
    async def _handle_import(self, args):
        """
        Gérer la commande d'importation de données
        
        Args:
            args: Arguments de la ligne de commande
        """
        if args.source == "all":
            # Exécuter le pipeline complet d'importation
            logger.info("Lancement de l'importation complète de toutes les sources")
            stats = await pipeline_manager.run_full_pipeline()
            self._display_import_stats(stats)
        else:
            # Exécuter l'importation pour une source spécifique
            logger.info(f"Lancement de l'importation depuis {args.source}")
            
            # Construire les paramètres supplémentaires
            kwargs = {}
            if args.options:
                try:
                    for option in args.options:
                        key, value = option.split("=")
                        # Convertir les types si nécessaire
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        kwargs[key] = value
                except Exception as e:
                    logger.error(f"Erreur lors du parsing des options: {str(e)}")
            
            stats = await pipeline_manager.run_specific_source(
                args.source, 
                args.method,
                **kwargs
            )
            self._display_import_stats(stats)
    
    async def _handle_enrichment(self, args):
        """
        Gérer la commande d'enrichissement de données
        
        Args:
            args: Arguments de la ligne de commande
        """
        if args.file:
            # Charger les documents depuis un fichier JSON
            logger.info(f"Chargement des documents depuis {args.file}")
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                
                if not isinstance(documents, list):
                    logger.error(f"Format invalide dans {args.file}: ce n'est pas une liste de documents")
                    return
                
                # Enrichir les documents
                logger.info(f"Enrichissement de {len(documents)} documents")
                enriched_docs = await data_enrichment.enrich_documents(documents)
                
                # Sauvegarder les documents enrichis
                output_file = args.output or f"{args.file.rsplit('.', 1)[0]}_enriched.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(enriched_docs, f, ensure_ascii=False, indent=4)
                
                logger.info(f"Documents enrichis sauvegardés dans {output_file}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'enrichissement des documents: {str(e)}")
        else:
            logger.error("Aucun fichier spécifié pour l'enrichissement")
    
    async def _handle_search(self, args):
        """
        Gérer la commande de recherche dans la base vectorielle
        
        Args:
            args: Arguments de la ligne de commande
        """
        if not args.query:
            logger.error("Requête de recherche manquante")
            return
        
        # Construire les filtres
        filters = {}
        if args.type:
            filters["type"] = args.type.split(",")
        if args.domain:
            filters["domain"] = args.domain.split(",")
        if args.date_from or args.date_to:
            date_filter = {}
            if args.date_from:
                date_filter["gte"] = args.date_from
            if args.date_to:
                date_filter["lte"] = args.date_to
            filters["date"] = date_filter
        
        try:
            # Effectuer la recherche
            logger.info(f"Recherche: '{args.query}' (limite: {args.limit})")
            results = vector_store.search(
                query=args.query,
                limit=args.limit,
                filters=filters
            )
            
            # Afficher les résultats
            logger.info(f"{len(results)} résultats trouvés")
            
            for i, result in enumerate(results):
                print(f"\n--- Résultat {i+1} ---")
                print(f"ID: {result.get('id', 'N/A')}")
                print(f"Titre: {result.get('title', 'N/A')}")
                print(f"Type: {result.get('doc_type', 'N/A')}")
                print(f"Date: {result.get('date', 'N/A')}")
                print(f"Score: {result.get('score', 'N/A')}")
                
                # Afficher un extrait du contenu
                content = result.get('content', '')
                print(f"Contenu: {content[:200]}..." if len(content) > 200 else f"Contenu: {content}")
                
                # Afficher les métadonnées pertinentes
                if 'metadata' in result and result['metadata']:
                    summary = result['metadata'].get('summary', '')
                    if summary:
                        print(f"Résumé: {summary[:200]}..." if len(summary) > 200 else f"Résumé: {summary}")
                    
                    domains = result['metadata'].get('domains', [])
                    if domains:
                        print(f"Domaines: {', '.join(domains)}")
            
            # Sauvegarder les résultats si demandé
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                logger.info(f"Résultats sauvegardés dans {args.output}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
    
    async def _handle_stats(self, args):
        """
        Gérer la commande d'affichage des statistiques
        
        Args:
            args: Arguments de la ligne de commande
        """
        try:
            # Récupérer les statistiques de la base vectorielle
            vector_stats = vector_store.get_stats()
            
            # Afficher les statistiques
            print("\n--- Statistiques de la base de données vectorielle ---")
            print(f"Nombre total de documents: {vector_stats.get('total_documents', 'N/A')}")
            print(f"Taille de l'index: {vector_stats.get('index_size', 'N/A')}")
            
            # Statistiques par type de document
            type_stats = vector_stats.get('document_types', {})
            if type_stats:
                print("\nDistribution par type de document:")
                for doc_type, count in type_stats.items():
                    print(f"  - {doc_type}: {count} documents")
            
            # Statistiques par domaine juridique
            domain_stats = vector_stats.get('domains', {})
            if domain_stats:
                print("\nDistribution par domaine juridique:")
                for domain, count in domain_stats.items():
                    print(f"  - {domain}: {count} documents")
            
            # Statistiques temporelles
            time_stats = vector_stats.get('time_periods', {})
            if time_stats:
                print("\nDistribution temporelle:")
                for period, count in time_stats.items():
                    print(f"  - {period}: {count} documents")
            
            # Statistiques supplémentaires
            if args.detailed:
                # Récupérer des statistiques plus détaillées
                # Cette partie peut être étendue avec des statistiques plus avancées
                pass
            
            # Sauvegarder les statistiques si demandé
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(vector_stats, f, ensure_ascii=False, indent=4)
                logger.info(f"Statistiques sauvegardées dans {args.output}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
    
    async def _handle_export(self, args):
        """
        Gérer la commande d'exportation de données
        
        Args:
            args: Arguments de la ligne de commande
        """
        try:
            # Déterminer le format d'exportation
            export_format = args.format.lower()
            if export_format not in ["json", "csv", "xml"]:
                logger.error(f"Format d'exportation non supporté: {export_format}")
                return
            
            # Construire les filtres
            filters = {}
            if args.type:
                filters["type"] = args.type.split(",")
            if args.domain:
                filters["domain"] = args.domain.split(",")
            if args.date_from or args.date_to:
                date_filter = {}
                if args.date_from:
                    date_filter["gte"] = args.date_from
                if args.date_to:
                    date_filter["lte"] = args.date_to
                filters["date"] = date_filter
            
            # Récupérer les documents à exporter
            logger.info(f"Exportation des données au format {export_format}")
            
            # Si une requête est spécifiée, effectuer une recherche
            if args.query:
                logger.info(f"Recherche des documents correspondant à '{args.query}'")
                documents = vector_store.search(
                    query=args.query,
                    limit=args.limit,
                    filters=filters
                )
            else:
                # Sinon, récupérer tous les documents correspondant aux filtres
                logger.info("Récupération de tous les documents correspondant aux filtres")
                documents = vector_store.get_documents(
                    limit=args.limit,
                    filters=filters
                )
            
            logger.info(f"{len(documents)} documents à exporter")
            
            # Déterminer le fichier de sortie
            output_file = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
            
            # Exporter les documents
            if export_format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(documents, f, ensure_ascii=False, indent=4)
            elif export_format == "csv":
                import csv
                
                # Déterminer les champs à exporter
                fields = ["id", "title", "content", "doc_type", "date", "url"]
                
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    
                    for doc in documents:
                        # Extraire les champs nécessaires
                        row = {field: doc.get(field, "") for field in fields}
                        writer.writerow(row)
            elif export_format == "xml":
                from xml.dom.minidom import getDOMImplementation
                
                # Créer un document XML
                impl = getDOMImplementation()
                xml_doc = impl.createDocument(None, "documents", None)
                root = xml_doc.documentElement
                
                for doc in documents:
                    # Créer un élément pour chaque document
                    doc_elem = xml_doc.createElement("document")
                    
                    # Ajouter les attributs
                    for key, value in doc.items():
                        if key == "metadata":
                            # Traiter les métadonnées séparément
                            continue
                        
                        # Créer un élément pour chaque champ
                        field_elem = xml_doc.createElement(key)
                        text = xml_doc.createTextNode(str(value))
                        field_elem.appendChild(text)
                        doc_elem.appendChild(field_elem)
                    
                    # Ajouter le document à la racine
                    root.appendChild(doc_elem)
                
                # Sauvegarder le document XML
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(xml_doc.toprettyxml(indent="  "))
            
            logger.info(f"Données exportées dans {output_file}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des données: {str(e)}")
    
    async def _handle_validation(self, args):
        """
        Gérer la commande de validation des données
        
        Args:
            args: Arguments de la ligne de commande
        """
        try:
            # Déterminer le type de validation
            validation_type = args.type.lower()
            
            if validation_type == "consistency":
                # Vérifier la cohérence des données
                logger.info("Vérification de la cohérence des données")
                
                # TODO: Implémenter des vérifications de cohérence spécifiques
                # Par exemple, vérifier que les champs obligatoires sont présents,
                # que les valeurs sont cohérentes, etc.
                
                print("Validation de cohérence non implémentée")
                
            elif validation_type == "duplicates":
                # Rechercher les doublons
                logger.info("Recherche de doublons")
                
                # Récupérer tous les documents
                documents = vector_store.get_documents(limit=10000)
                
                # Rechercher les doublons par ID
                ids = [doc.get("id") for doc in documents]
                duplicate_ids = set([id for id in ids if ids.count(id) > 1])
                
                if duplicate_ids:
                    print(f"Doublons trouvés: {len(duplicate_ids)} IDs dupliqués")
                    print(f"IDs en double: {list(duplicate_ids)[:10]}...")
                else:
                    print("Aucun doublon trouvé")
                
            elif validation_type == "schema":
                # Valider le schéma des documents
                logger.info("Validation du schéma des documents")
                
                # TODO: Implémenter la validation de schéma
                # Par exemple, vérifier que les documents respectent un schéma JSON
                
                print("Validation de schéma non implémentée")
                
            else:
                logger.error(f"Type de validation non supporté: {validation_type}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la validation des données: {str(e)}")
    
    def _display_import_stats(self, stats):
        """
        Afficher les statistiques d'importation
        
        Args:
            stats: Statistiques d'importation
        """
        if not stats:
            logger.warning("Aucune statistique d'importation disponible")
            return
        
        print("\n--- Statistiques d'importation ---")
        print(f"Total importé: {stats.get('total_imported', 0)} documents")
        print(f"Erreurs: {stats.get('error_count', 0)}")
        
        if 'duration_seconds' in stats:
            duration = stats['duration_seconds']
            print(f"Durée totale: {duration:.2f} secondes")
            
            if stats.get('total_imported', 0) > 0:
                print(f"Vitesse moyenne: {stats['total_imported'] / duration:.2f} documents/seconde")
        
        # Statistiques par source
        sources_stats = stats.get('sources_stats', {})
        if sources_stats:
            print("\nStatistiques par source:")
            
            for source_id, source_stats in sources_stats.items():
                print(f"  - {source_stats.get('name', source_id)}: {source_stats.get('documents_imported', 0)} documents")
                
                # Statistiques par méthode
                methods_stats = source_stats.get('methods', {})
                if methods_stats:
                    for method_name, method_stats in methods_stats.items():
                        print(f"    - {method_name}: {method_stats.get('documents_imported', 0)} documents")
                        
                        if 'error' in method_stats:
                            print(f"      Erreur: {method_stats['error']}")

def main():
    """Point d'entrée principal du script d'administration"""
    # Configurer le logger
    logger.add("logs/data_admin.log", rotation="10 MB", level="INFO")
    
    # Créer le parseur d'arguments
    parser = argparse.ArgumentParser(description="Administration des données juridiques")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Commande d'importation
    import_parser = subparsers.add_parser("import", help="Importer des données juridiques")
    import_parser.add_argument("--source", default="all", help="Source à importer (all, legifrance, eurlex, ...)")
    import_parser.add_argument("--method", help="Méthode spécifique à appeler")
    import_parser.add_argument("--options", nargs="*", help="Options supplémentaires (clé=valeur)")
    
    # Commande d'enrichissement
    enrich_parser = subparsers.add_parser("enrich", help="Enrichir des documents juridiques")
    enrich_parser.add_argument("--file", required=True, help="Fichier JSON contenant les documents à enrichir")
    enrich_parser.add_argument("--output", help="Fichier de sortie pour les documents enrichis")
    
    # Commande de recherche
    search_parser = subparsers.add_parser("search", help="Rechercher dans la base vectorielle")
    search_parser.add_argument("--query", required=True, help="Requête de recherche")
    search_parser.add_argument("--limit", type=int, default=10, help="Nombre maximum de résultats")
    search_parser.add_argument("--type", help="Filtrer par type de document (loi,jurisprudence,doctrine,...)")
    search_parser.add_argument("--domain", help="Filtrer par domaine juridique (fiscal,travail,affaires,...)")
    search_parser.add_argument("--date-from", help="Date de début (format YYYY-MM-DD)")
    search_parser.add_argument("--date-to", help="Date de fin (format YYYY-MM-DD)")
    search_parser.add_argument("--output", help="Fichier de sortie pour les résultats")
    
    # Commande de statistiques
    stats_parser = subparsers.add_parser("stats", help="Afficher les statistiques de la base de données")
    stats_parser.add_argument("--detailed", action="store_true", help="Afficher des statistiques détaillées")
    stats_parser.add_argument("--output", help="Fichier de sortie pour les statistiques")
    
    # Commande d'exportation
    export_parser = subparsers.add_parser("export", help="Exporter des données juridiques")
    export_parser.add_argument("--format", default="json", choices=["json", "csv", "xml"], help="Format d'exportation")
    export_parser.add_argument("--query", help="Requête de recherche (optionnel)")
    export_parser.add_argument("--limit", type=int, default=1000, help="Nombre maximum de documents à exporter")
    export_parser.add_argument("--type", help="Filtrer par type de document (loi,jurisprudence,doctrine,...)")
    export_parser.add_argument("--domain", help="Filtrer par domaine juridique (fiscal,travail,affaires,...)")
    export_parser.add_argument("--date-from", help="Date de début (format YYYY-MM-DD)")
    export_parser.add_argument("--date-to", help="Date de fin (format YYYY-MM-DD)")
    export_parser.add_argument("--output", help="Fichier de sortie pour les données exportées")
    
    # Commande de validation
    validate_parser = subparsers.add_parser("validate", help="Valider les données juridiques")
    validate_parser.add_argument("--type", default="consistency", choices=["consistency", "duplicates", "schema"], help="Type de validation")
    
    # Créer l'interface d'administration
    admin = DataAdministrationCLI()
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Exécuter la commande
    if args.command:
        # Exécuter dans une boucle d'événements asyncio
        asyncio.run(admin.run_command(args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 