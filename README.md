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
   - Adminer (gestion BDD): http://localhost:8080

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