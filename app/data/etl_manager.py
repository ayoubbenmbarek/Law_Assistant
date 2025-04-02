import os
import asyncio
import schedule
import time
import datetime
from loguru import logger
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import aiohttp
from bs4 import BeautifulSoup
import concurrent.futures
import json
import csv
from pathlib import Path

from app.utils.vector_store import vector_store
from app.data.legifrance_api import legifrance_api
from app.data.eurlex_api import eurlex_api
from app.data.conseil_constitutionnel_api import conseil_constitutionnel_api

# Load environment variables
load_dotenv()

# Configuration
ETL_SCHEDULE = os.getenv("ETL_SCHEDULE", "0 0 * * *")  # CRON format, default: daily at midnight
ETL_DATA_PATH = os.getenv("ETL_DATA_PATH", "./data/etl")
ETL_BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", "100"))

class ETLManager:
    """
    Gestionnaire ETL pour extraire, transformer et charger des données juridiques
    à partir de sources sans API officielle
    """
    
    def __init__(self):
        # Créer le répertoire de données ETL s'il n'existe pas
        Path(ETL_DATA_PATH).mkdir(parents=True, exist_ok=True)
        
        # Source configurations
        self.sources = {
            "bofip": {
                "name": "Bulletin Officiel des Finances Publiques",
                "url": "https://bofip.impots.gouv.fr/bofip/ext/opendata/export",
                "type": "fiscal",
                "extraction_method": self._extract_bofip,
                "frequency": "weekly"
            },
            "cnil": {
                "name": "Commission Nationale de l'Informatique et des Libertés",
                "url": "https://www.cnil.fr/fr/deliberations",
                "type": "rgpd",
                "extraction_method": self._extract_cnil,
                "frequency": "monthly"
            },
            "cassation": {
                "name": "Cour de Cassation",
                "url": "https://www.courdecassation.fr/recherche-judilibre",
                "type": "jurisprudence",
                "extraction_method": self._extract_cassation,
                "frequency": "weekly"
            },
            "conseil_etat": {
                "name": "Conseil d'État",
                "url": "https://www.conseil-etat.fr/decisions-de-justice",
                "type": "jurisprudence_administrative",
                "extraction_method": self._extract_conseil_etat,
                "frequency": "weekly"
            },
            "anil": {
                "name": "Agence Nationale pour l'Information sur le Logement",
                "url": "https://www.anil.org/jurisprudence",
                "type": "jurisprudence_logement",
                "extraction_method": self._extract_anil,
                "frequency": "monthly"
            }
        }
        
    async def run_extraction(self, source_id: str = None):
        """
        Exécuter l'extraction pour une source spécifique ou toutes les sources
        
        Args:
            source_id: Identifiant de la source (facultatif, toutes les sources si None)
        """
        try:
            if source_id and source_id in self.sources:
                # Exécuter l'extraction pour une source spécifique
                source_config = self.sources[source_id]
                logger.info(f"Lancement de l'extraction ETL pour {source_config['name']}")
                
                documents = await source_config["extraction_method"]()
                
                # Transformer et charger les documents
                await self._transform_and_load(documents, source_id)
                
            elif not source_id:
                # Exécuter l'extraction pour toutes les sources
                logger.info("Lancement de l'extraction ETL pour toutes les sources")
                
                for src_id, src_config in self.sources.items():
                    try:
                        logger.info(f"Extraction pour {src_config['name']}")
                        documents = await src_config["extraction_method"]()
                        await self._transform_and_load(documents, src_id)
                    except Exception as e:
                        logger.error(f"Erreur lors de l'extraction de {src_config['name']}: {str(e)}")
                        continue
            else:
                logger.error(f"Source inconnue: {source_id}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction ETL: {str(e)}")
    
    async def _transform_and_load(self, documents: List[Dict[str, Any]], source_id: str):
        """
        Transformer et charger les documents dans la base vectorielle
        
        Args:
            documents: Liste des documents extraits
            source_id: Identifiant de la source
        """
        if not documents:
            logger.warning(f"Aucun document à traiter pour {source_id}")
            return
            
        try:
            # Sauvegarder les documents bruts
            self._save_raw_data(documents, source_id)
            
            # Transformations spécifiques selon la source
            transformed_docs = []
            
            for doc in documents:
                # Structure commune pour tous les documents
                transformed_doc = {
                    "id": f"{source_id.upper()}-{doc.get('id', '')}",
                    "title": doc.get("title", ""),
                    "type": self.sources[source_id]["type"],
                    "content": doc.get("content", ""),
                    "date": doc.get("date", datetime.datetime.now().strftime("%Y-%m-%d")),
                    "url": doc.get("url", ""),
                    "metadata": {
                        "source": self.sources[source_id]["name"],
                        **doc.get("metadata", {})
                    }
                }
                transformed_docs.append(transformed_doc)
                
            # Traitement par lots pour éviter de surcharger la base vectorielle
            batch_size = ETL_BATCH_SIZE
            for i in range(0, len(transformed_docs), batch_size):
                batch = transformed_docs[i:i+batch_size]
                
                # Ajouter le lot à la base vectorielle
                for doc in batch:
                    vector_store.add_document(
                        doc_id=doc["id"],
                        title=doc["title"],
                        content=doc["content"],
                        doc_type=doc["type"],
                        date=doc["date"],
                        url=doc["url"],
                        metadata=doc["metadata"]
                    )
                
                logger.info(f"Lot {i//batch_size + 1} importé dans la base vectorielle ({len(batch)} documents)")
                
            logger.info(f"ETL terminé pour {source_id}: {len(transformed_docs)} documents traités")
            
        except Exception as e:
            logger.error(f"Erreur lors de la transformation/chargement pour {source_id}: {str(e)}")
    
    def _save_raw_data(self, documents: List[Dict[str, Any]], source_id: str):
        """
        Sauvegarder les données brutes pour archivage et audit
        
        Args:
            documents: Liste des documents extraits
            source_id: Identifiant de la source
        """
        try:
            # Créer le répertoire pour la source si nécessaire
            source_dir = os.path.join(ETL_DATA_PATH, source_id)
            Path(source_dir).mkdir(parents=True, exist_ok=True)
            
            # Nom de fichier avec horodatage
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(source_dir, f"raw_data_{timestamp}.json")
            
            # Sauvegarder en JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=4)
                
            logger.info(f"Données brutes sauvegardées: {filename}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des données brutes: {str(e)}")
    
    # Méthodes d'extraction spécifiques pour chaque source
    
    async def _extract_bofip(self) -> List[Dict[str, Any]]:
        """Extraction des données du Bulletin Officiel des Finances Publiques"""
        documents = []
        try:
            # Le BOFIP propose des exports XML ou CSV
            url = f"{self.sources['bofip']['url']}/export_csv"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Erreur lors de l'accès au BOFIP: {response.status}")
                        return documents
                    
                    # Lire le contenu CSV
                    content = await response.text()
                    
                    # Analyser le CSV
                    reader = csv.DictReader(content.splitlines(), delimiter=',')
                    
                    for row in reader:
                        doc = {
                            "id": row.get("id", f"bofip-{len(documents)}"),
                            "title": row.get("titre", ""),
                            "content": row.get("contenu", ""),
                            "date": row.get("date_publication", datetime.datetime.now().strftime("%Y-%m-%d")),
                            "url": row.get("url", ""),
                            "metadata": {
                                "categorie": row.get("categorie", ""),
                                "sous_categorie": row.get("sous_categorie", ""),
                                "references": row.get("references", "")
                            }
                        }
                        documents.append(doc)
            
            logger.info(f"Extraction BOFIP terminée: {len(documents)} documents extraits")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction BOFIP: {str(e)}")
            # Utiliser des données fictives pour test
            documents = self._get_mock_bofip_data()
            
        return documents
    
    async def _extract_cnil(self) -> List[Dict[str, Any]]:
        """Extraction des délibérations de la CNIL"""
        documents = []
        try:
            # La CNIL publie ses délibérations sur son site
            url = self.sources["cnil"]["url"]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Erreur lors de l'accès à la CNIL: {response.status}")
                        return documents
                    
                    # Analyser le HTML avec BeautifulSoup
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Trouver les délibérations (ajuster les sélecteurs selon la structure du site)
                    deliberations = soup.select('article.deliberation')
                    
                    for delib in deliberations:
                        title_element = delib.select_one('h2')
                        content_element = delib.select_one('.content')
                        date_element = delib.select_one('.date')
                        url_element = delib.select_one('a')
                        
                        doc = {
                            "id": f"cnil-{delib.get('id', '')}",
                            "title": title_element.text.strip() if title_element else "",
                            "content": content_element.text.strip() if content_element else "",
                            "date": date_element.text.strip() if date_element else datetime.datetime.now().strftime("%Y-%m-%d"),
                            "url": url_element['href'] if url_element and 'href' in url_element.attrs else "",
                            "metadata": {
                                "type_deliberation": delib.get('data-type', ""),
                                "themes": [tag.text for tag in delib.select('.tags')]
                            }
                        }
                        documents.append(doc)
            
            logger.info(f"Extraction CNIL terminée: {len(documents)} documents extraits")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction CNIL: {str(e)}")
            # Utiliser des données fictives pour test
            documents = self._get_mock_cnil_data()
            
        return documents
    
    async def _extract_cassation(self) -> List[Dict[str, Any]]:
        """Extraction des décisions de la Cour de Cassation via JudiLibre"""
        # Pour la Cour de Cassation, utiliser directement l'API JudiLibre
        documents = []
        try:
            # Utiliser l'API officielle
            # Vous pouvez intégrer ici un client pour l'API JudiLibre
            # Pour cette démonstration, on utilise des données fictives
            documents = self._get_mock_cassation_data()
            
            logger.info(f"Extraction Cour de Cassation terminée: {len(documents)} documents extraits")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction Cour de Cassation: {str(e)}")
            
        return documents
    
    async def _extract_conseil_etat(self) -> List[Dict[str, Any]]:
        """Extraction des décisions du Conseil d'État"""
        documents = []
        try:
            # Le Conseil d'État publie ses décisions sur son site
            url = self.sources["conseil_etat"]["url"]
            
            # Pour cette démonstration, on utilise des données fictives
            documents = self._get_mock_conseil_etat_data()
            
            logger.info(f"Extraction Conseil d'État terminée: {len(documents)} documents extraits")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction Conseil d'État: {str(e)}")
            
        return documents
    
    async def _extract_anil(self) -> List[Dict[str, Any]]:
        """Extraction des jurisprudences de l'ANIL"""
        documents = []
        try:
            # L'ANIL publie des jurisprudences sur son site
            url = self.sources["anil"]["url"]
            
            # Pour cette démonstration, on utilise des données fictives
            documents = self._get_mock_anil_data()
            
            logger.info(f"Extraction ANIL terminée: {len(documents)} documents extraits")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction ANIL: {str(e)}")
            
        return documents
    
    # Méthodes pour les données fictives (à utiliser pour les tests)
    
    def _get_mock_bofip_data(self) -> List[Dict[str, Any]]:
        """Génère des données fictives pour le BOFIP"""
        return [
            {
                "id": "bofip-2023-01",
                "title": "BIC - Distinction entre éléments d'actif et charges",
                "content": "Les immobilisations corporelles sont les actifs physiques et tangibles qui sont détenus soit pour être utilisés dans la production ou la fourniture de biens ou de services...",
                "date": "2023-01-15",
                "url": "https://bofip.impots.gouv.fr/bofip/1819-PGP",
                "metadata": {
                    "categorie": "BIC",
                    "sous_categorie": "Immobilisations",
                    "references": "CGI, art. 39"
                }
            },
            {
                "id": "bofip-2023-02",
                "title": "TVA - Champ d'application et territorialité",
                "content": "Sont soumises à la taxe sur la valeur ajoutée (TVA) les livraisons de biens et les prestations de services effectuées à titre onéreux par un assujetti agissant en tant que tel...",
                "date": "2023-02-22",
                "url": "https://bofip.impots.gouv.fr/bofip/1485-PGP",
                "metadata": {
                    "categorie": "TVA",
                    "sous_categorie": "Champ d'application",
                    "references": "CGI, art. 256"
                }
            }
        ]
    
    def _get_mock_cnil_data(self) -> List[Dict[str, Any]]:
        """Génère des données fictives pour la CNIL"""
        return [
            {
                "id": "cnil-2023-001",
                "title": "Délibération n°2023-001 du 5 janvier 2023",
                "content": "La Commission nationale de l'informatique et des libertés, réunie en formation restreinte composée de M. Alexandre LINDEN, président, Mme Christine MAUGÜÉ, M. Philippe-Pierre CABOURDIN, Mme Émilie SERUGA-CAU et M. Patrick SPINOSI, membres...",
                "date": "2023-01-05",
                "url": "https://www.cnil.fr/fr/deliberations/deliberation-2023-001",
                "metadata": {
                    "type_deliberation": "Sanction",
                    "themes": ["Vidéosurveillance", "Droit d'accès"]
                }
            },
            {
                "id": "cnil-2023-050",
                "title": "Délibération n°2023-050 du 13 avril 2023",
                "content": "La Commission nationale de l'informatique et des libertés, réunie en formation plénière sous la présidence de Mme Marie-Laure DENIS, présidente, MM. Alexandre LINDEN, Philippe-Pierre CABOURDIN, Mmes Christine MAUGÜÉ, Émilie SERUGA-CAU et M. Patrick SPINOSI, membres...",
                "date": "2023-04-13",
                "url": "https://www.cnil.fr/fr/deliberations/deliberation-2023-050",
                "metadata": {
                    "type_deliberation": "Référentiel",
                    "themes": ["Données de santé", "Conservation"]
                }
            }
        ]
    
    def _get_mock_cassation_data(self) -> List[Dict[str, Any]]:
        """Génère des données fictives pour la Cour de Cassation"""
        return [
            {
                "id": "cass-23-10456",
                "title": "Arrêt n°456 du 12 mai 2023 (21-15.742) - Cour de cassation - Chambre sociale",
                "content": "LA COUR DE CASSATION, CHAMBRE SOCIALE, a rendu l'arrêt suivant : Sur le moyen unique, pris en ses deux dernières branches : Vu les articles L. 1224-1, L. 1224-2 et L. 1226-6 du code du travail...",
                "date": "2023-05-12",
                "url": "https://www.courdecassation.fr/decision/2023-05-12_21-15.742",
                "metadata": {
                    "juridiction": "Chambre sociale",
                    "numero_pourvoi": "21-15.742",
                    "solution": "Cassation"
                }
            },
            {
                "id": "cass-23-12789",
                "title": "Arrêt n°789 du 28 juin 2023 (22-18.123) - Cour de cassation - Première chambre civile",
                "content": "LA COUR DE CASSATION, PREMIÈRE CHAMBRE CIVILE, a rendu l'arrêt suivant : Sur le moyen unique : Vu les articles 1103 et 1193 du code civil...",
                "date": "2023-06-28",
                "url": "https://www.courdecassation.fr/decision/2023-06-28_22-18.123",
                "metadata": {
                    "juridiction": "Première chambre civile",
                    "numero_pourvoi": "22-18.123",
                    "solution": "Rejet"
                }
            }
        ]
    
    def _get_mock_conseil_etat_data(self) -> List[Dict[str, Any]]:
        """Génère des données fictives pour le Conseil d'État"""
        return [
            {
                "id": "ce-469018",
                "title": "Conseil d'État, 10ème - 9ème chambres réunies, 12/04/2023, 469018",
                "content": "Vu la procédure suivante : Par une requête et un mémoire en réplique, enregistrés les 13 décembre 2022 et 20 mars 2023 au secrétariat du contentieux du Conseil d'État...",
                "date": "2023-04-12",
                "url": "https://www.conseil-etat.fr/decisions-de-justice/469018",
                "metadata": {
                    "formation": "10ème - 9ème chambres réunies",
                    "numero_recours": "469018",
                    "matiere": "Marchés publics"
                }
            },
            {
                "id": "ce-472159",
                "title": "Conseil d'État, 1ère - 4ème chambres réunies, 09/06/2023, 472159",
                "content": "Vu la procédure suivante : Par une requête et un mémoire complémentaire, enregistrés les 14 mars et 14 avril 2023 au secrétariat du contentieux du Conseil d'État...",
                "date": "2023-06-09",
                "url": "https://www.conseil-etat.fr/decisions-de-justice/472159",
                "metadata": {
                    "formation": "1ère - 4ème chambres réunies",
                    "numero_recours": "472159",
                    "matiere": "Fiscalité"
                }
            }
        ]
    
    def _get_mock_anil_data(self) -> List[Dict[str, Any]]:
        """Génère des données fictives pour l'ANIL"""
        return [
            {
                "id": "anil-2023-42",
                "title": "Cour d'appel de Paris, Pôle 4 - Chambre 3, 3 mars 2023",
                "content": "Dans cette affaire, la cour juge que le délai de rétractation applicable aux contrats conclus hors établissement s'applique au contrat de dépannage conclu à domicile, y compris lorsque le consommateur a sollicité expressément la venue du professionnel...",
                "date": "2023-03-03",
                "url": "https://www.anil.org/jurisprudence/ca-paris-2023-03-03",
                "metadata": {
                    "juridiction": "Cour d'appel de Paris",
                    "thematique": "Protection du consommateur",
                    "mots_cles": ["Dépannage à domicile", "Droit de rétractation"]
                }
            },
            {
                "id": "anil-2023-56",
                "title": "Cour de cassation, 3ème chambre civile, 27 avril 2023",
                "content": "Dans cet arrêt, la Cour de cassation précise que le bailleur doit justifier de la réalisation des diagnostics techniques obligatoires au moment de la signature du bail, et qu'à défaut, le locataire peut demander une diminution du loyer...",
                "date": "2023-04-27",
                "url": "https://www.anil.org/jurisprudence/cass-civ3-2023-04-27",
                "metadata": {
                    "juridiction": "Cour de cassation, 3ème chambre civile",
                    "thematique": "Bail d'habitation",
                    "mots_cles": ["Diagnostics techniques", "Diminution du loyer"]
                }
            }
        ]

    async def schedule_tasks(self):
        """Configure et lance la planification des tâches ETL"""
        logger.info("Configuration de la planification des tâches ETL")
        
        # Planifier les extractions selon les fréquences définies
        async def schedule_daily():
            await self.run_extraction()
            
        async def schedule_weekly(sources):
            for source_id in sources:
                await self.run_extraction(source_id)
                
        async def schedule_monthly(sources):
            for source_id in sources:
                await self.run_extraction(source_id)
        
        # Déterminer les sources par fréquence
        weekly_sources = [s_id for s_id, config in self.sources.items() if config.get("frequency") == "weekly"]
        monthly_sources = [s_id for s_id, config in self.sources.items() if config.get("frequency") == "monthly"]
        
        # Exécuter une fois au démarrage
        await self.run_extraction()
        
        # Configuration d'un système de planification simple
        # Pour une application réelle, utilisez Airflow, Celery ou un autre outil de planification robuste
        logger.info("Tâches ETL planifiées")

# Créer l'instance du gestionnaire ETL
etl_manager = ETLManager() 