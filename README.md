# AI Legal Assistant 🇫🇷

Assistant juridique IA spécialisé dans le droit français, conçu pour fournir des informations juridiques précises et contextuelles aux professionnels du droit et aux particuliers.

## Fonctionnalités

- ✅ **Recherche sémantique vectorielle** pour trouver les textes juridiques pertinents
- ✅ **Base de connaissances juridiques** couvrant les principaux domaines du droit français
- ✅ **Citations précises** avec références aux sources originales
- ✅ **Interface utilisateur intuitive** pour poser des questions juridiques
- ✅ **Réponses structurées** avec cadre juridique, application, exceptions et recommandations
- ✅ **Multi-sources de données juridiques** intégrant Légifrance, EUR-Lex, jurisprudence et autres

## Domaines de droit couverts

- Droit fiscal
- Droit du travail
- Droit des affaires
- Droit de la famille
- Droit immobilier
- Droit de la consommation
- Droit pénal
- Droit administratif
- Droit constitutionnel
- Protection des données (RGPD)
- Propriété intellectuelle
- Droit de l'environnement
- Droit de la santé
- Sécurité sociale
- Droit européen

## Architecture système

Le système est composé de plusieurs composants clés:

1. **API Backend FastAPI**
   - Traitement des requêtes
   - Génération de réponses juridiques
   - Authentification et gestion des utilisateurs

2. **Base de données vectorielle**
   - Indexation vectorielle des textes juridiques
   - Recherche sémantique rapide
   - Support pour Qdrant et Weaviate

3. **Système ETL et intégration de données**
   - Connecteurs pour différentes sources de données juridiques
   - Pipeline d'ingestion et d'enrichissement automatisé
   - Extraction de métadonnées et d'entités juridiques

4. **Frontend React**
   - Interface utilisateur intuitive
   - Formulaire de requêtes juridiques
   - Affichage structuré des réponses

## Sources de données

L'assistant utilise plusieurs sources officielles:

- **Légifrance API (PISTE)** : Codes, lois, règlements et jurisprudence
- **EUR-Lex** : Réglementations européennes applicables en France
- **Conseil Constitutionnel** : Décisions constitutionnelles
- **Sources ETL** :
  - BOFIP (Bulletin Officiel des Finances Publiques)
  - CNIL (délibérations et décisions)
  - Cour de Cassation (via JudiLibre)
  - Conseil d'État
  - ANIL (Agence Nationale pour l'Information sur le Logement)

## Système d'ETL et enrichissement

Le système comprend un pipeline complet d'ETL (Extract, Transform, Load) pour:

1. **Extraction** de données depuis diverses sources:
   - APIs officielles (Légifrance, EUR-Lex, etc.)
   - Web scraping pour les sources sans API officielle
   - Sources de données structurées et non structurées

2. **Transformation** avec enrichissement avancé:
   - Classification automatique par domaine juridique
   - Extraction d'entités nommées (personnes, organisations, lieux)
   - Génération de résumés automatiques
   - Extraction des références légales et citation
   - Analyse de lisibilité et de complexité des textes
   - Génération de métadonnées structurées

3. **Chargement** dans la base de connaissances:
   - Indexation vectorielle pour la recherche sémantique
   - Organisation par domaine, type et juridiction
   - Stockage des métadonnées enrichies
   - Création de liens entre les documents

## Outils d'administration des données

Un outil d'administration en ligne de commande permet de:

- Importer des données depuis différentes sources
- Enrichir des documents juridiques existants
- Rechercher dans la base de connaissances
- Afficher des statistiques sur les données
- Exporter des données en différents formats
- Valider la qualité et la cohérence des données

## Installation et déploiement

### Prérequis

- Python 3.10+
- PostgreSQL avec pgvector
- Qdrant ou Weaviate (base vectorielle)
- Redis (optionnel, pour la mise en cache)
- Docker et Docker Compose (pour le déploiement)

### Installation avec Docker

1. Cloner le dépôt:
   ```bash
   git clone https://github.com/votre-utilisateur/law_assistant.git
   cd law_assistant
   ```

2. Configurer les variables d'environnement:
   ```bash
   cp .env.example .env
   # Modifier .env avec vos clés API et configurations
   ```

3. Lancer l'application avec Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Accéder à l'application:
   - API: http://localhost:8009
   - Documentation API: http://localhost:8009/docs
   - Adminer (gestion BDD): http://localhost:8089

### Installation manuelle

1. Cloner le dépôt:
   ```bash
   git clone https://github.com/votre-utilisateur/law_assistant.git
   cd law_assistant
   ```

2. Créer un environnement virtuel:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

3. Installer les dépendances:
   ```bash
   pip install -r requirements.txt
   python -m spacy download fr_core_news_lg
   ```

4. Configurer les variables d'environnement:
   ```bash
   cp .env.example .env
   # Modifier .env avec vos clés API et configurations
   ```

5. Créer la base de données:
   ```bash
   psql -U postgres -c "CREATE DATABASE law_assistant"
   psql -U postgres -d law_assistant -f database/schema.sql
   ```

6. Lancer l'application:
   ```bash
   uvicorn main:app --reload
   ```

## Utilisation de l'outil d'administration des données

```bash
# Importer toutes les sources de données
python -m app.admin.data_admin import --source all

# Importer une source spécifique
python -m app.admin.data_admin import --source legifrance

# Enrichir des documents JSON
python -m app.admin.data_admin enrich --file documents.json --output enriched_docs.json

# Rechercher dans la base vectorielle
python -m app.admin.data_admin search --query "licenciement économique" --limit 10

# Afficher les statistiques de la base de données
python -m app.admin.data_admin stats

# Exporter des données
python -m app.admin.data_admin export --format json --query "RGPD" --limit 100 --output rgpd_docs.json
```

## Avertissement

Cet assistant juridique fournit des informations à titre indicatif uniquement et ne constitue pas un avis juridique professionnel. Il est développé pour assister les professionnels du droit et informer les particuliers, mais ne remplace en aucun cas la consultation d'un avocat ou d'un professionnel du droit qualifié.

## Licence

© 2023. Tous droits réservés.

## Architecture

L'application est composée de :
- Un **backend** FastAPI en Python qui gère l'API REST, la recherche vectorielle et la génération de réponses
- Un **frontend** React qui fournit l'interface utilisateur
- Une base de données **PostgreSQL** pour le stockage des données relationnelles
- Une base de données vectorielle **Qdrant** pour la recherche sémantique
- **Redis** pour la mise en cache et les tâches asynchrones

## Prérequis

- Docker et Docker Compose
- Git
- Python 3.11+ (pour le développement local)
- Node.js 16+ (pour le développement frontend local)

## Configuration en développement

1. Cloner le dépôt :
   ```bash
   git clone <url-du-depot>
   cd law_assistant
   ```

2. Configurer les variables d'environnement :
   ```bash
   cp .env.example .env
   # Modifier les valeurs selon votre environnement
   ```

3. Lancer l'application en mode développement :
   ```bash
   docker-compose up -d
   ```

4. Accéder à l'application :
   - Backend: http://localhost:8009
   - Frontend: http://localhost:3009
   - API Docs: http://localhost:8009/docs
   - Adminer (gestion BD): http://localhost:8099

## Configuration en production

1. Préparer l'environnement de production :
   ```bash
   cp .env.example .env.production
   # Modifier les valeurs pour la production (secrets, URLs, etc.)
   ```

2. Déployer avec le script de déploiement :
   ```bash
   ./deploy.sh
   ```

3. Accéder à l'application :
   - Application (Frontend + Backend): http://votre-domaine.com
   - API: http://votre-domaine.com/api
   - API Docs: http://votre-domaine.com/docs

## Résolution des problèmes de connectivité

Si vous rencontrez des problèmes de connexion entre le frontend et le backend :

1. Vérifiez que les URLs d'API sont correctement configurées :
   - En développement : `.env.development` -> `REACT_APP_API_URL=http://localhost:8009`
   - En production : `.env.production` -> `REACT_APP_API_URL=` (vide pour utiliser la même origine)

2. Assurez-vous que les origines CORS sont correctement configurées :
   - Vérifiez `.env` ou `.env.production` -> `CORS_ORIGINS=http://localhost:3009,http://localhost:8009,...`

3. Si les services ne sont pas accessibles dans Docker :
   - Utilisez les noms de service Docker plutôt que localhost dans les variables d'environnement Docker (exemple : `redis` au lieu de `localhost`)

## Structure des fichiers clés

```
├── app/                    # Code source de l'application
│   ├── api/                # Endpoints d'API
│   ├── components/         # Composants React
│   ├── data/               # Gestion des données
│   ├── frontend/           # Configuration frontend
│   ├── models/             # Modèles de données
│   ├── utils/              # Utilitaires
│   └── main.py             # Point d'entrée FastAPI
├── database/               # Scripts SQL
├── docker/                 # Fichiers Docker personnalisés
├── .env.development        # Variables d'environnement dev frontend
├── .env.production         # Variables d'environnement production
├── docker-compose.yml      # Configuration Docker développement
├── docker-compose.production.yml  # Configuration Docker production
└── deploy.sh               # Script de déploiement
```

## Adaptation pour votre domaine

Pour configurer l'application sur votre propre domaine :

1. Modifiez `.env.production` :
   ```
   CORS_ORIGINS=https://votre-domaine.com
   ```

2. Modifiez `app/core/config.py` pour ajouter votre domaine à la liste `CORS_ORIGINS`

3. Reconstruisez et redéployez l'application 