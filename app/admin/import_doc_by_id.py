#!/usr/bin/env python3
"""
Script d'importation d'un seul document à la fois, identifié par un ID
"""

import sys
import os
import uuid
import argparse
from loguru import logger

# Ajouter le répertoire parent au chemin pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

# Liste des documents prédéfinis (ID statiques)
MOCK_DOCUMENTS = {
    "civil1": {
        "id": "00000000-0000-0000-0000-000000000001",
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
    "travail1": {
        "id": "00000000-0000-0000-0000-000000000002",
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
    "famille1": {
        "id": "00000000-0000-0000-0000-000000000003",
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
    "juris1": {
        "id": "00000000-0000-0000-0000-000000000004",
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
    "impot1": {
        "id": "00000000-0000-0000-0000-000000000005",
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
    },
    "simple1": {
        "id": "00000000-0000-0000-0000-000000000006",
        "title": "Document simple sur la garde d'enfants",
        "type": "loi",
        "content": "La garde des enfants peut être attribuée à l'un des parents ou partagée entre les deux parents.",
        "date": "2023-01-01",
        "url": "https://example.com/garde-enfants",
        "metadata": {
            "code": "Code Civil",
            "section": "Garde d'enfants",
            "domains": ["famille", "enfant", "garde"]
        }
    }
}

def setup_logger():
    """Configure le logger"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")

def main():
    """Fonction principale"""
    setup_logger()
    
    # Configurer les arguments
    parser = argparse.ArgumentParser(description="Importer un document juridique spécifique dans la base vectorielle")
    parser.add_argument("doc_id", choices=list(MOCK_DOCUMENTS.keys()), help="ID du document à importer")
    parser.add_argument("--list", action="store_true", help="Lister les documents disponibles sans importer")
    args = parser.parse_args()
    
    # Si l'option --list est utilisée, afficher la liste des documents disponibles
    if args.list:
        logger.info("Documents disponibles:")
        for key, doc in MOCK_DOCUMENTS.items():
            logger.info(f"  - {key}: {doc['title']}")
        return True
    
    # Vérifier que l'ID existe
    if args.doc_id not in MOCK_DOCUMENTS:
        logger.error(f"Document non trouvé: {args.doc_id}")
        logger.info("Documents disponibles: " + ", ".join(MOCK_DOCUMENTS.keys()))
        return False
    
    logger.info(f"Importation du document: {args.doc_id}")
    
    # Importation conditionnelle du vector_store pour éviter les problèmes de mémoire
    try:
        from app.utils.vector_store import vector_store
        logger.info("Vector store module imported successfully")
    except Exception as e:
        logger.error(f"Failed to import vector store: {str(e)}")
        return False
    
    # Vérification que le vector store est fonctionnel
    if not vector_store or not vector_store.is_functional:
        logger.error("Vector store is not available or not functional")
        return False
    
    # Récupérer le document
    doc = MOCK_DOCUMENTS[args.doc_id]
    
    # Tentative d'ajout du document
    logger.info(f"Attempting to add document: {doc['title']}")
    try:
        success = vector_store.add_document(
            doc_id=doc['id'],
            title=doc['title'],
            content=doc['content'],
            doc_type=doc['type'],
            date=doc['date'],
            url=doc['url'],
            metadata=doc['metadata']
        )
        
        if success:
            logger.info("Document added successfully!")
            return True
        else:
            logger.error("Failed to add document.")
            return False
            
    except Exception as e:
        logger.error(f"Error during document addition: {str(e)}")
        return False
        
if __name__ == "__main__":
    result = main()
    if not result:
        sys.exit(1) 