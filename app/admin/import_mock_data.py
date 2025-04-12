#!/usr/bin/env python3
"""
Script d'importation de données juridiques simulées pour tester l'application
"""

import sys
import os
import asyncio
import uuid
import time
from loguru import logger

# Ajouter le répertoire parent au chemin pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importer après l'ajout du chemin
from app.utils.vector_store import vector_store

# Données simulées
MOCK_LEGAL_DOCUMENTS = [
    {
        "id": str(uuid.uuid4()),
        "title": "Article 1134 du Code Civil",
        "type": "loi",
        "content": "Les conventions légalement formées tiennent lieu de loi à ceux qui les ont faites. Elles ne peuvent être révoquées que de leur consentement mutuel, ou pour les causes que la loi autorise. Elles doivent être exécutées de bonne foi.",
        "date": "2023-01-01",
        "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006436298",
        "metadata": {
            "code": "Code Civil",
            "section": "Des contrats"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Article L1231-1 du Code du travail",
        "type": "loi",
        "content": "Le contrat de travail à durée indéterminée peut être rompu à l'initiative de l'employeur ou du salarié, ou d'un commun accord, dans les conditions prévues par les dispositions du présent titre. Ces dispositions sont applicables aux contrats à durée indéterminée conclus pour l'exercice d'une première activité professionnelle.",
        "date": "2023-01-01",
        "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037730625",
        "metadata": {
            "code": "Code du travail",
            "section": "Rupture du contrat de travail à durée indéterminée",
            "domains": ["travail", "contrat", "rupture"]
        }
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Article 371-1 du Code Civil",
        "type": "loi",
        "content": "L'autorité parentale est un ensemble de droits et de devoirs ayant pour finalité l'intérêt de l'enfant. Elle appartient aux parents jusqu'à la majorité ou l'émancipation de l'enfant pour le protéger dans sa sécurité, sa santé et sa moralité, pour assurer son éducation et permettre son développement, dans le respect dû à sa personne.",
        "date": "2023-01-01",
        "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038749626",
        "metadata": {
            "code": "Code Civil",
            "section": "De l'autorité parentale",
            "domains": ["famille", "enfant", "autorité parentale"]
        }
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Cour de Cassation, civile, Chambre sociale, 25 mai 2022, 20-23.428",
        "type": "jurisprudence",
        "content": "Attendu que pour fixer la créance du salarié au titre d'un rappel de salaire pour la période du 1er décembre 2015 au 30 mai 2016, l'arrêt retient qu'il n'est pas contesté que le salarié a perçu la somme brute de 9 274,32 euros pour cette période alors qu'il aurait dû percevoir la somme de 11 400 euros; Qu'en statuant ainsi, alors que le rappel de salaire s'entend de la différence entre la rémunération effectivement perçue et celle qui aurait dû l'être, la cour d'appel a violé les textes susvisés;",
        "date": "2022-05-25",
        "url": "https://www.legifrance.gouv.fr/juri/id/JURITEXT000045932183",
        "metadata": {
            "juridiction": "Cour de Cassation",
            "chambre": "Chambre sociale",
            "domains": ["travail", "salaire", "rémunération"]
        }
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Conseil d'État, 5ème chambre, 22/12/2021, 453080 - Affaire Getaround",
        "type": "jurisprudence",
        "content": "Vu la procédure suivante : Par une requête sommaire et un mémoire complémentaire, enregistrés les 28 mai et 30 août 2021 au secrétariat du contentieux du Conseil d'Etat, la société Getaround demande au Conseil d'Etat d'annuler pour excès de pouvoir la décision implicite de rejet résultant du silence gardé par le Premier ministre sur sa demande tendant à l'abrogation du 2° de l'article 1er du décret n° 2020-1310 du 29 octobre 2020 prescrivant les mesures générales nécessaires pour faire face à l'épidémie de covid-19 dans le cadre de l'état d'urgence sanitaire.",
        "date": "2021-12-22",
        "url": "https://www.legifrance.gouv.fr/ceta/id/CETATEXT000044615886",
        "metadata": {
            "juridiction": "Conseil d'État",
            "chambre": "5ème chambre",
            "domains": ["administratif", "covid-19", "mesures sanitaires"]
        }
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Article 197 du Code général des impôts",
        "type": "loi",
        "content": "I. En ce qui concerne les contribuables visés à l'article 4 B, il est fait application des règles suivantes pour le calcul de l'impôt sur le revenu : 1. L'impôt est calculé en appliquant à la fraction de chaque part de revenu qui excède 10 777 € le taux de : - 11 % pour la fraction supérieure à 10 777 € et inférieure ou égale à 27 478 € ; - 30 % pour la fraction supérieure à 27 478 € et inférieure ou égale à 78 570 € ; - 41 % pour la fraction supérieure à 78 570 € et inférieure ou égale à 168 994 € ; - 45 % pour la fraction supérieure à 168 994 €.",
        "date": "2023-01-01",
        "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000044978995",
        "metadata": {
            "code": "Code général des impôts",
            "section": "Calcul de l'impôt",
            "domains": ["fiscal", "impôt", "revenus"]
        }
    }
]

def setup_logger():
    """Configure le logger"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("logs/import_mock_data.log", rotation="500 MB", level="DEBUG")

async def import_mock_data():
    """Importe les données simulées dans la base vectorielle"""
    try:
        logger.info("Vérification de la base vectorielle...")
        if not vector_store or not vector_store.is_functional:
            logger.error("La base vectorielle n'est pas disponible ou non fonctionnelle.")
            return False
        
        logger.info(f"Importation de {len(MOCK_LEGAL_DOCUMENTS)} documents juridiques simulés...")
        
        success_count = 0
        
        # Importer chaque document séparément avec une pause entre chaque
        for i, doc in enumerate(MOCK_LEGAL_DOCUMENTS):
            logger.info(f"Importation du document {i+1}/{len(MOCK_LEGAL_DOCUMENTS)}: {doc['title']}")
            
            try:
                # Ajouter le document
                result = vector_store.add_document(
                    doc_id=doc["id"],
                    title=doc["title"],
                    content=doc["content"],
                    doc_type=doc["type"],
                    date=doc["date"],
                    url=doc["url"],
                    metadata=doc["metadata"]
                )
                
                if result:
                    logger.info(f"Document importé avec succès: {doc['id']} - {doc['title']}")
                    success_count += 1
                else:
                    logger.error(f"Échec de l'importation du document: {doc['id']} - {doc['title']}")
                
                # Pause pour réduire l'utilisation mémoire
                logger.info("Pause de 2 secondes pour libérer la mémoire...")
                await asyncio.sleep(2)
                
                # Force la libération de la mémoire
                import gc
                gc.collect()
                
            except Exception as e:
                logger.error(f"Erreur lors de l'importation du document {doc['id']}: {str(e)}")
        
        logger.info(f"Importation terminée. {success_count}/{len(MOCK_LEGAL_DOCUMENTS)} documents importés avec succès.")
        
        # Tester la recherche seulement si au moins un document a été importé
        if success_count > 0:
            # Pause pour s'assurer que l'indexation est terminée
            logger.info("Pause avant le test de recherche...")
            await asyncio.sleep(2)
            
            # Test de recherche simple
            logger.info("Test de la base vectorielle après importation...")
            test_query = "contrat de travail"
            results = vector_store.search(test_query, limit=3)
            
            if results:
                logger.info(f"Recherche de test réussie. {len(results)} résultats trouvés pour '{test_query}'")
                for i, result in enumerate(results):
                    logger.info(f"Résultat {i+1}: {result.get('title')} (score: {result.get('score', 'N/A')})")
            else:
                logger.warning(f"Aucun résultat trouvé pour la recherche '{test_query}'")
        
        return success_count > 0
    
    except Exception as e:
        logger.error(f"Erreur lors de l'importation des données simulées: {str(e)}")
        return False

async def main():
    """Fonction principale"""
    setup_logger()
    logger.info("Démarrage de l'importation des données juridiques simulées")
    
    success = await import_mock_data()
    
    if success:
        logger.info("Importation des données juridiques simulées terminée avec succès")
    else:
        logger.error("Échec de l'importation des données juridiques simulées")

if __name__ == "__main__":
    asyncio.run(main()) 