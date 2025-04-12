# Documentation du Projet Assistant Juridique

Ce dossier contient la documentation technique du projet d'assistant juridique, notamment pour l'intégration des APIs de données juridiques.

## Table des Matières

### APIs et Intégrations

- [Documentation API Légifrance](api_examples/legifrance_api_usage.md) - Guide d'utilisation de l'API Légifrance
- [Filtres et Tri pour l'API Légifrance](api_examples/legifrance_filters.md) - Options de filtrage et de tri pour l'API Légifrance
- [Exemple d'implémentation](api_examples/legifrance_api_example.py) - Code Python d'exemple pour utiliser l'API
- [Guide de Résolution des Problèmes](troubleshooting_api_access.md) - Solutions aux problèmes d'accès aux APIs
- [Statut de la Connexion aux APIs](api_connection_status.md) - Rapport sur les tests de connexion et solutions alternatives

### Accès aux APIs

- [Obtenir l'accès à l'API Légifrance](../acces_api_legifrance.py) - Script pour demander l'accès à l'API Légifrance
- [Explorer les APIs disponibles](../explore_piste_apis.py) - Script pour explorer les APIs disponibles sur PISTE

### Données Open Source

- [Accès aux données juridiques open source](../open_legal_data.py) - Script pour télécharger des données juridiques open source

### Documents Officiels

- [Documents Officiels](official_documents/README.md) - Documents officiels de référence et ressources juridiques

## Prérequis pour l'intégration des APIs

1. **Compte PISTE** - Créer un compte sur [PISTE](https://piste.gouv.fr/)
2. **Demande d'accès** - Faire une demande d'accès via [DataPass](https://datapass.api.gouv.fr/dila/legifrance)
3. **Clés d'API** - Obtenir et configurer vos clés d'API

## Configuration de l'environnement

Pour utiliser les APIs, vous devez configurer les variables d'environnement suivantes dans un fichier `.env` à la racine du projet:

```
# API PISTE configuration
PISTE_API_KEY=votre_api_key
PISTE_SECRET_KEY=votre_secret_key
PISTE_OAUTH_CLIENT_ID=votre_oauth_client_id
PISTE_OAUTH_SECRET_KEY=votre_oauth_secret_key
```

## Contribuer à la Documentation

Si vous souhaitez contribuer à cette documentation:

1. Créez de nouveaux fichiers Markdown dans le dossier approprié
2. Ajoutez des exemples de code ou des cas d'utilisation
3. Mettez à jour ce README pour inclure vos nouveaux fichiers

## Ressources Additionnelles

- [Documentation officielle PISTE](https://developer.aife.economie.gouv.fr)
- [Guide d'utilisation de l'API Légifrance](https://developer.aife.economie.gouv.fr/composants/legifrance)
- [Documentation DataPass](https://datapass.api.gouv.fr/doc/faq)
- [Data.gouv.fr - Données juridiques](https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/)
- [Legilibre (Etalab)](https://github.com/etalab/legilibre-data/releases) 