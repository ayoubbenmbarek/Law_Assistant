import os
import asyncio
import datetime
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from loguru import logger

# Importation pour l'enrichissement des données
import spacy
import re
import textstat
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor

from app.utils.vector_store import vector_store

# Charger les variables d'environnement
load_dotenv()

# Configuration
NLP_MODEL = os.getenv("NLP_MODEL", "fr_core_news_lg")
ENRICHMENT_BATCH_SIZE = int(os.getenv("ENRICHMENT_BATCH_SIZE", "50"))
MAX_THREADS = int(os.getenv("MAX_THREADS", "4"))

class DataEnrichment:
    """
    Service d'enrichissement des données juridiques
    Ajoute des métadonnées, des annotations et des classifications aux textes juridiques
    """
    
    def __init__(self):
        """Initialiser le service d'enrichissement avec les modèles NLP"""
        try:
            # Charger le modèle spaCy
            logger.info(f"Chargement du modèle spaCy: {NLP_MODEL}")
            self.nlp = spacy.load(NLP_MODEL)
            
            # Initialiser le classifier de thématiques juridiques
            logger.info("Initialisation du classifier de thématiques juridiques")
            self.domain_classifier = pipeline(
                "text-classification", 
                model=os.getenv("LEGAL_CLASSIFIER_MODEL", "camembert-base"),
                device=-1  # CPU par défaut, 0 pour GPU
            )
            
            # Initialiser le résumeur automatique
            logger.info("Initialisation du résumeur automatique")
            self.summarizer = pipeline(
                "summarization", 
                model=os.getenv("SUMMARIZER_MODEL", "ccdv/legalbert-base-fr"),
                device=-1
            )
            
            # Thread pool pour paralléliser les traitements
            self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
            
            logger.info("Service d'enrichissement initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service d'enrichissement: {str(e)}")
            # Utiliser des enrichissements basiques si les modèles ne sont pas disponibles
            self.nlp = None
            self.domain_classifier = None
            self.summarizer = None
    
    async def enrich_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrichir une liste de documents juridiques
        
        Args:
            documents: Liste des documents à enrichir
            
        Returns:
            Liste des documents enrichis
        """
        if not documents:
            logger.warning("Aucun document à enrichir")
            return []
            
        try:
            enriched_docs = []
            
            # Traitement par lots pour les documents volumineux
            batch_size = ENRICHMENT_BATCH_SIZE
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                logger.info(f"Enrichissement du lot {i//batch_size + 1}/{(len(documents)+batch_size-1)//batch_size} ({len(batch)} documents)")
                
                # Enrichir chaque document du lot
                batch_tasks = []
                for doc in batch:
                    # Créer une tâche pour chaque document
                    batch_tasks.append(self.enrich_document(doc))
                
                # Exécuter les tâches en parallèle
                enriched_batch = await asyncio.gather(*batch_tasks)
                enriched_docs.extend(enriched_batch)
                
                logger.info(f"Lot {i//batch_size + 1} enrichi avec succès")
            
            logger.info(f"Enrichissement terminé: {len(enriched_docs)} documents enrichis")
            return enriched_docs
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement des documents: {str(e)}")
            return documents  # Retourner les documents non enrichis en cas d'erreur
    
    async def enrich_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrichir un document juridique individuel
        
        Args:
            document: Document à enrichir
            
        Returns:
            Document enrichi
        """
        try:
            # Copie du document pour éviter de modifier l'original
            enriched_doc = document.copy()
            
            # Initialiser ou enrichir les métadonnées
            if "metadata" not in enriched_doc:
                enriched_doc["metadata"] = {}
                
            # Contenu à enrichir
            content = enriched_doc.get("content", "")
            title = enriched_doc.get("title", "")
            
            if not content:
                logger.warning(f"Document sans contenu: {enriched_doc.get('id', 'ID inconnu')}")
                return enriched_doc
                
            # Enrichissements linguistiques
            await self._add_linguistic_features(enriched_doc, content)
            
            # Classification des domaines juridiques
            await self._classify_legal_domains(enriched_doc, content, title)
            
            # Génération d'un résumé
            await self._generate_summary(enriched_doc, content)
            
            # Extraction de références légales
            await self._extract_legal_references(enriched_doc, content)
            
            # Métadonnées de lisibilité
            await self._add_readability_metrics(enriched_doc, content)
            
            # Horodatage de l'enrichissement
            enriched_doc["metadata"]["enrichment_date"] = datetime.datetime.now().isoformat()
            
            return enriched_doc
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement du document {document.get('id', 'ID inconnu')}: {str(e)}")
            return document  # Retourner le document non enrichi en cas d'erreur
    
    async def _add_linguistic_features(self, doc: Dict[str, Any], content: str):
        """Ajouter des caractéristiques linguistiques au document"""
        try:
            if not self.nlp:
                # Enrichissement basique si spaCy n'est pas disponible
                doc["metadata"]["word_count"] = len(content.split())
                return
                
            # Utiliser un thread pour exécuter l'analyse spaCy (CPU-bound)
            loop = asyncio.get_event_loop()
            nlp_doc = await loop.run_in_executor(self.executor, self.nlp, content)
            
            # Extraire les entités nommées
            entities = {}
            for ent in nlp_doc.ents:
                ent_type = ent.label_
                if ent_type not in entities:
                    entities[ent_type] = []
                if ent.text not in entities[ent_type]:
                    entities[ent_type].append(ent.text)
            
            # Statistiques linguistiques
            doc["metadata"]["entities"] = entities
            doc["metadata"]["word_count"] = len(nlp_doc)
            doc["metadata"]["sentence_count"] = len(list(nlp_doc.sents))
            
            # Mots-clés (basés sur les noms et adjectifs les plus fréquents)
            keywords = {}
            for token in nlp_doc:
                if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop and len(token.text) > 3:
                    if token.lemma_ in keywords:
                        keywords[token.lemma_] += 1
                    else:
                        keywords[token.lemma_] = 1
            
            # Trier les mots-clés par fréquence et garder les 20 premiers
            sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20]
            doc["metadata"]["keywords"] = [k[0] for k in sorted_keywords]
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des caractéristiques linguistiques: {str(e)}")
    
    async def _classify_legal_domains(self, doc: Dict[str, Any], content: str, title: str):
        """Classifier le document par domaine juridique"""
        try:
            if not self.domain_classifier:
                # Classification simple basée sur des mots-clés si le modèle n'est pas disponible
                domains = self._keyword_based_domain_classification(content, title)
                doc["metadata"]["domains"] = domains
                return
                
            # Utiliser le titre et le début du document pour la classification
            classification_text = f"{title}. {content[:1000]}"
            
            # Utiliser un thread pour exécuter la classification (GPU/CPU-bound)
            loop = asyncio.get_event_loop()
            classification = await loop.run_in_executor(
                self.executor, 
                lambda: self.domain_classifier(classification_text, top_k=3)
            )
            
            # Stocker les domaines prédits et leurs scores
            predicted_domains = []
            domain_scores = {}
            
            for result in classification:
                label = result["label"].lower()
                score = result["score"]
                
                predicted_domains.append(label)
                domain_scores[label] = score
            
            doc["metadata"]["domains"] = predicted_domains
            doc["metadata"]["domain_scores"] = domain_scores
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification des domaines: {str(e)}")
            # Classification simple basée sur des mots-clés en cas d'erreur
            domains = self._keyword_based_domain_classification(content, title)
            doc["metadata"]["domains"] = domains
    
    def _keyword_based_domain_classification(self, content: str, title: str) -> List[str]:
        """Classification basique des domaines basée sur des mots-clés"""
        content_lower = (title + " " + content).lower()
        
        domain_keywords = {
            "fiscal": ["impôt", "fiscal", "taxe", "tva", "bénéfice", "revenu", "imposition"],
            "travail": ["travail", "salarié", "employeur", "contrat de travail", "licenciement", "embauche"],
            "affaires": ["société", "commercial", "entreprise", "contrat", "associé", "responsabilité"],
            "famille": ["famille", "mariage", "divorce", "adoption", "garde", "pension", "succession"],
            "immobilier": ["immobilier", "bail", "loyer", "propriété", "copropriété", "logement"],
            "consommation": ["consommateur", "garantie", "défaut", "achat", "vente", "remboursement"],
            "penal": ["pénal", "infraction", "crime", "délit", "peine", "amende", "prison"],
            "administratif": ["administratif", "préfet", "décision", "recours", "service public"],
            "constitutionnel": ["constitution", "constitutionnel", "loi", "principe", "liberté"],
            "rgpd": ["rgpd", "données", "cnil", "protection", "traitement", "information"],
            "propriete_intellectuelle": ["propriété intellectuelle", "marque", "brevet", "droit d'auteur"],
            "environnement": ["environnement", "pollution", "écologie", "développement durable"],
            "sante": ["santé", "médecin", "patient", "hôpital", "soins", "médical"],
            "securite_sociale": ["sécurité sociale", "cotisation", "assurance maladie", "retraite", "prestation"],
            "europeen": ["européen", "union européenne", "ue", "directive", "règlement européen"]
        }
        
        # Compter les occurrences de mots-clés par domaine
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = 0
            for keyword in keywords:
                score += content_lower.count(keyword)
            if score > 0:
                domain_scores[domain] = score
        
        # Trier les domaines par score et retourner les 3 premiers
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return [d[0] for d in sorted_domains[:3]] if sorted_domains else ["autre"]
    
    async def _generate_summary(self, doc: Dict[str, Any], content: str):
        """Générer un résumé du document"""
        try:
            if not self.summarizer:
                # Résumé simple si le modèle n'est pas disponible
                sentences = content.split(".")[:3]
                summary = ". ".join(sentences) + "."
                doc["metadata"]["summary"] = summary
                return
                
            # Limiter le contenu pour le résumeur (beaucoup de modèles ont une limite d'entrée)
            max_chars = 1024  # Ajuster selon les capacités du modèle
            truncated_content = content[:max_chars]
            
            # Utiliser un thread pour exécuter le résumeur (GPU/CPU-bound)
            loop = asyncio.get_event_loop()
            summary_result = await loop.run_in_executor(
                self.executor, 
                lambda: self.summarizer(truncated_content, max_length=100, min_length=30, do_sample=False)
            )
            
            summary = summary_result[0]["summary_text"]
            doc["metadata"]["summary"] = summary
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {str(e)}")
            # Résumé simple en cas d'erreur
            sentences = content.split(".")[:3]
            summary = ". ".join(sentences) + "."
            doc["metadata"]["summary"] = summary
    
    async def _extract_legal_references(self, doc: Dict[str, Any], content: str):
        """Extraire les références légales du document"""
        try:
            # Extraire les références aux articles de code
            article_pattern = r"article[s]?\s+([LRD]?\.\s*)?(\d+[-.]\d+|\d+)(?:\s+(?:du|de la|du code|de|des)\s+([a-zéèêàâôùûçë'\s]+))?(?:[-–]\s*\d+)?|\
                              [LRD]\.?\s*(\d+[-.]\d+|\d+)(?:\s+(?:du|de la|du code|de|des)\s+([a-zéèêàâôùûçë'\s]+))?(?:[-–]\s*\d+)?"
            
            article_matches = re.finditer(article_pattern, content, re.IGNORECASE)
            
            legal_refs = []
            codes_mentioned = set()
            
            for match in article_matches:
                ref_text = match.group(0).strip()
                
                # Essayer de déterminer le code concerné
                code = None
                for code_part in match.groups():
                    if code_part and any(c in code_part.lower() for c in ["civil", "pénal", "commerce", "travail", "consommation"]):
                        code = code_part.strip()
                        codes_mentioned.add(code)
                        break
                
                legal_refs.append({
                    "text": ref_text,
                    "code": code
                })
            
            # Extraire les références aux décisions de jurisprudence
            decision_pattern = r"(?:arrêt|décision)(?:\s+(?:n°|numéro))?\s+(\d+[-_.]\d+|\d+)(?:\s+(?:du|de la)\s+([a-zéèêàâôùûçë'\s]+))?"
            
            decision_matches = re.finditer(decision_pattern, content, re.IGNORECASE)
            
            for match in decision_matches:
                ref_text = match.group(0).strip()
                legal_refs.append({
                    "text": ref_text,
                    "type": "jurisprudence"
                })
            
            # Stocker les références dans les métadonnées
            doc["metadata"]["legal_references"] = legal_refs
            doc["metadata"]["codes_mentioned"] = list(codes_mentioned)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des références légales: {str(e)}")
    
    async def _add_readability_metrics(self, doc: Dict[str, Any], content: str):
        """Ajouter des métriques de lisibilité au document"""
        try:
            readability = {}
            
            # Indice de Flesch (adapté au français)
            readability["flesch_score"] = textstat.flesch_reading_ease(content)
            
            # Complexité de lecture
            if readability["flesch_score"] >= 80:
                readability["complexity"] = "simple"
            elif readability["flesch_score"] >= 60:
                readability["complexity"] = "moyen"
            else:
                readability["complexity"] = "complexe"
            
            # Niveau d'éducation requis (approximatif)
            readability["grade_level"] = textstat.text_standard(content, float_output=False)
            
            doc["metadata"]["readability"] = readability
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des métriques de lisibilité: {str(e)}")

# Créer l'instance du service d'enrichissement
data_enrichment = DataEnrichment() 