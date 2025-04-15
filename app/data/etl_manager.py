import os
import asyncio
import schedule
import time
import datetime
import uuid
import hashlib
from loguru import logger
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import aiohttp
from bs4 import BeautifulSoup
import concurrent.futures
import json
import csv
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize
from tqdm import tqdm

from app.utils.vector_store import vector_store
from app.data.legifrance_api import legifrance_api, LegifranceAPI
from app.data.eurlex_api import eurlex_api
from app.data.conseil_constitutionnel_api import conseil_constitutionnel_api

# Téléchargement des ressources NLTK nécessaires (si pas déjà installées)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Load environment variables
load_dotenv()

# Configuration
ETL_SCHEDULE = os.getenv("ETL_SCHEDULE", "0 0 * * *")  # CRON format, default: daily at midnight
ETL_DATA_PATH = os.getenv("ETL_DATA_PATH", "./data/etl")
ETL_BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", "100"))
CHUNK_SIZE = 1000  # Taille approximative des chunks en caractères
CHUNK_OVERLAP = 200  # Chevauchement entre les chunks
MAX_RESULTS_PER_QUERY = 50  # Nombre maximum de résultats par requête API
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
            "legifrance_codes": {
                "name": "Légifrance Codes",
                "type": "code",
                "extraction_method": self._extract_legifrance_codes,
                "frequency": "monthly"
            },
            "legifrance_jurisprudence": {
                "name": "Légifrance Jurisprudence",
                "type": "jurisprudence",
                "extraction_method": self._extract_legifrance_jurisprudence,
                "frequency": "weekly"
            },
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
            },
            "legifrance_tables": {
                "extraction_method": self._extract_legifrance_tables,
                "enabled": True,
                "params": {
                    "start_year": 2020,
                    "end_year": 2023
                }
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
            documents: Liste des documents extraits (ou chunks pour les sources Légifrance)
            source_id: Identifiant de la source
        """
        if not documents:
            logger.warning(f"Aucun document à traiter pour {source_id}")
            return
            
        try:
            # Sauvegarder les documents bruts
            self._save_raw_data(documents, source_id)
            
            # Vérifier si nous traitons déjà des chunks (sources Légifrance)
            is_chunked_source = source_id in ["legifrance_codes", "legifrance_jurisprudence"]
            
            if is_chunked_source:
                # Les documents sont déjà des chunks optimisés pour la vectorisation
                chunks = documents
                logger.info(f"Source {source_id} : Utilisation de {len(chunks)} chunks pré-traités")
                
                # Traitement par lots pour éviter de surcharger la base vectorielle
                batch_size = ETL_BATCH_SIZE
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i+batch_size]
                    
                    # Ajouter le lot à la base vectorielle
                    for chunk in batch:
                        # Générer un ID unique pour le vecteur
                        chunk_id = chunk["id"]
                        # Utiliser un hachage MD5 et s'assurer d'avoir un entier positif
                        hash_obj = hashlib.md5(chunk_id.encode())
                        numeric_id = abs(int(hash_obj.hexdigest(), 16) % (2**31 - 1))
                        
                        vector_store.add_document(
                            doc_id=chunk_id,
                            title=chunk["title"],
                            content=chunk["text"],
                            doc_type=chunk["metadata"].get("type", "unknown"),
                            date=chunk["metadata"].get("date", datetime.datetime.now().strftime("%Y-%m-%d")),
                            url=chunk["metadata"].get("url", ""),
                            metadata=chunk["metadata"],
                            numeric_id=numeric_id
                        )
                    
                    logger.info(f"Lot {i//batch_size + 1} importé dans la base vectorielle ({len(batch)} chunks)")
                    # Petite pause pour éviter de surcharger le système
                    await asyncio.sleep(0.1)
                    
                logger.info(f"ETL terminé pour {source_id}: {len(chunks)} chunks traités")
                
            else:
                # Méthode traditionnelle pour les autres sources - traitement document par document
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
            logger.exception(e)
    
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

    async def _extract_legifrance_codes(self) -> List[Dict[str, Any]]:
        """
        Extraction des codes juridiques via l'API Légifrance avec chunking efficace
        
        Returns:
            Liste de chunks de textes juridiques avec métadonnées
        """
        logger.info("Début de l'extraction des codes juridiques via l'API Légifrance")
        
        # Termes de recherche pour les codes juridiques
        code_terms = LEGAL_DOMAINS["codes"] + list(LEGAL_CONCEPTS.keys())
        total_chunks = []
        total_documents = 0
        
        for term in tqdm(code_terms, desc="Extraction des codes"):
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
                    date = item.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
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
    
    async def _extract_legifrance_jurisprudence(self) -> List[Dict[str, Any]]:
        """
        Extraction de jurisprudence via l'API Légifrance avec chunking efficace
        
        Returns:
            Liste de chunks de textes juridiques avec métadonnées
        """
        logger.info("Début de l'extraction de jurisprudence via l'API Légifrance")
        
        # Termes de recherche pour la jurisprudence
        jurisprudence_terms = LEGAL_DOMAINS["jurisprudence"]
        for domain, concepts in LEGAL_CONCEPTS.items():
            jurisprudence_terms.extend(concepts)
        
        total_chunks = []
        total_documents = 0
        
        for term in tqdm(jurisprudence_terms, desc="Extraction de jurisprudence"):
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
                    date = item.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
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
                logger.error(f"Erreur lors de l'extraction de jurisprudence pour le terme '{term}': {str(e)}")
        
        logger.success(f"Extraction de jurisprudence terminée. Total: {total_documents} documents, {len(total_chunks)} chunks")
        return total_chunks

    async def run_legifrance_extraction(self, extract_codes: bool = True, extract_jurisprudence: bool = True, custom_terms: List[str] = None):
        """
        Exécuter spécifiquement l'extraction des données de Légifrance avec chunking
        et traitement optimisé
        
        Args:
            extract_codes: Si True, extraire les codes juridiques
            extract_jurisprudence: Si True, extraire la jurisprudence
            custom_terms: Liste personnalisée de termes de recherche (facultative)
        """
        logger.info("Lancement de l'extraction optimisée des données Légifrance")
        
        total_chunks = []
        
        try:
            # Extraction des codes
            if extract_codes:
                logger.info("=== Extraction des Codes Juridiques ===")
                # Utiliser les termes personnalisés ou les termes par défaut
                code_terms = custom_terms if custom_terms else (LEGAL_DOMAINS["codes"] + list(LEGAL_CONCEPTS.keys()))
                
                # Exécuter l'extraction
                code_chunks = await self._extract_legifrance_codes()
                
                if code_chunks:
                    logger.info(f"Traitement de {len(code_chunks)} chunks de codes")
                    # Transformer et charger les chunks
                    await self._transform_and_load(code_chunks, "legifrance_codes")
                    total_chunks.extend(code_chunks)
                else:
                    logger.warning("Aucun chunk de code extrait")
            
            # Extraction de la jurisprudence
            if extract_jurisprudence:
                logger.info("=== Extraction de la Jurisprudence ===")
                
                # Exécuter l'extraction
                jurisprudence_chunks = await self._extract_legifrance_jurisprudence()
                
                if jurisprudence_chunks:
                    logger.info(f"Traitement de {len(jurisprudence_chunks)} chunks de jurisprudence")
                    # Transformer et charger les chunks
                    await self._transform_and_load(jurisprudence_chunks, "legifrance_jurisprudence")
                    total_chunks.extend(jurisprudence_chunks)
                else:
                    logger.warning("Aucun chunk de jurisprudence extrait")
            
            # Statistiques finales
            extraction_info = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_chunks": len(total_chunks),
                "code_chunks": len([c for c in total_chunks if c.get("metadata", {}).get("domain") == "code"]),
                "jurisprudence_chunks": len([c for c in total_chunks if c.get("metadata", {}).get("domain") == "jurisprudence"]),
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP
            }
            
            # Sauvegarder les informations dans un fichier JSON
            stats_file = os.path.join(ETL_DATA_PATH, f"legifrance_extraction_stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(extraction_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Informations d'extraction sauvegardées dans {stats_file}")
            logger.success(f"Extraction et traitement terminés. Total: {len(total_chunks)} chunks stockés.")
            
            return extraction_info
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction optimisée de Légifrance: {str(e)}")
            logger.exception(e)
            return {"error": str(e)}

    def _extract_legifrance_tables(self, start_year=None, end_year=None):
        """
        Extract annual tables from Legifrance API
        
        Args:
            start_year: Starting year (defaults to current year - 1)
            end_year: Ending year (defaults to current year)
            
        Returns:
            List of extracted documents
        """
        # Initialize API client
        legifrance_api = LegifranceAPI()
        
        # Authenticate
        if not legifrance_api.authenticate():
            self.logger.error("Failed to authenticate with Legifrance API")
            return []
        
        logger.info("Successfully authenticated with Legifrance API")
        
        # Set default year range if not provided
        current_year = datetime.now().year
        if not start_year:
            start_year = current_year - 1
        if not end_year:
            end_year = current_year
        
        logger.info(f"Extracting tables for years {start_year} to {end_year}")
        
        # Prepare request payload
        request_payload = {
            "period": {
                "startYear": start_year,
                "endYear": end_year
            }
        }
        
        # Extract data
        try:
            response = legifrance_api._make_api_request(
                method='POST', 
                endpoint='/consult/getTables', 
                data=request_payload  # Using data instead of json
            )
            
            # Save raw response for inspection
            with open('tables_response.json', 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Raw API response saved to tables_response.json")
            
            if not response or 'tables' not in response:
                logger.warning("No tables found in API response")
                return []
            
            tables = response.get('tables', [])
            logger.info(f"Retrieved {len(tables)} tables")
            
            # Transform tables data into documents
            documents = []
            for table in tables:
                table_id = table.get('id', '')
                title = table.get('title', 'Annual Table')
                year = table.get('year', '')
                
                # Get table content
                content = table.get('summary', '')
                if not content and 'sections' in table:
                    content = " ".join([section.get('title', '') for section in table.get('sections', [])])
                
                # Create document structure
                doc = {
                    'doc_id': f"table_{table_id}",
                    'title': f"{title} {year}",
                    'content': content,
                    'doc_type': 'table',
                    'date': f"{year}-12-31",
                    'url': table.get('url', ''),
                    'metadata': {
                        'source': 'legifrance',
                        'type': 'table',
                        'year': year,
                        'table_id': table_id
                    }
                }
                
                documents.append(doc)
            
            logger.info(f"Extracted {len(documents)} table documents from Legifrance API")
            return documents
            
        except Exception as e:
            logger.error(f"Error extracting tables from Legifrance API: {str(e)}")
            return []

# Créer l'instance du gestionnaire ETL
etl_manager = ETLManager()