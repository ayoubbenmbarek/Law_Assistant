# Exemples d'utilisation de l'API Légifrance

Ce dossier contient des scripts d'exemple pour interagir avec l'API Légifrance via la plateforme PISTE.

## Prérequis

- Compte PISTE avec accès à l'API Légifrance
- Clés d'API configurées dans le fichier `.env` à la racine du projet:
  ```
  PISTE_API_KEY=votre_clé_api
  PISTE_SECRET_KEY=votre_clé_secrète
  ```

## Scripts disponibles

### 1. Explorer les fonctionnalités de l'API

Le script `explore_legifrance_api.py` permet d'explorer différentes fonctionnalités de l'API Légifrance.

#### Utilisation

```bash
# Installer les dépendances nécessaires
pip install rich

# Explorer les tables annuelles
python -m app.admin.examples.explore_legifrance_api --feature tables --year 2021

# Rechercher dans les codes
python -m app.admin.examples.explore_legifrance_api --feature codes --query "responsabilité civile"

# Rechercher dans la jurisprudence
python -m app.admin.examples.explore_legifrance_api --feature jurisprudence --query "licenciement faute grave"

# Explorer les conventions collectives
python -m app.admin.examples.explore_legifrance_api --feature conventions

# Consulter un article spécifique
python -m app.admin.examples.explore_legifrance_api --feature articles --id "LEGIARTI000006436298"

# Explorer toutes les fonctionnalités principales
python -m app.admin.examples.explore_legifrance_api --feature all
```

### 2. Importer des tables annuelles

Le script `import_legifrance_tables.py` à la racine du projet permet d'importer les tables annuelles de Légifrance et d'extraire le contenu des PDF dans la base vectorielle.

#### Utilisation

```bash
# Importer les tables de l'année 2021
python import_legifrance_tables.py --start-year 2021 --end-year 2021

# Importer les tables des 3 dernières années avec un lot de 20 documents
python import_legifrance_tables.py --start-year 2020 --end-year 2022 --batch-size 20
```

## Fonctionnalités de l'API

L'API Légifrance est organisée en plusieurs contrôleurs:

1. **Consult Controller**: Accès aux textes
   - Consulter des articles
   - Récupérer des délibérations CNIL
   - Consulter les textes des conventions collectives (KALI)
   - Récupérer les tables annuelles

2. **List Controller**: Liste les textes
   - Listes des conventions collectives
   - Liste des textes LODA (lois, décrets, etc.)
   - Liste des dossiers législatifs
   - Liste des documents administratifs

3. **Search Controller**: Recherche sur les textes
   - Recherche dans les codes
   - Recherche dans la jurisprudence

4. **Suggest Controller**: Autocomplétion
   - Suggestions pour les accords d'entreprise

## Structure du module API

Le module API Légifrance se trouve dans `app/data/legifrance_api.py` et propose une classe `LegifranceAPI` qui implémente tous les endpoints de l'API organisés par catégories. Chaque méthode est documentée avec des informations sur les paramètres et les résultats.

## Exemples de réponses

### Tables annuelles

```json
[
  {
    "id": "TABLE000039585405",
    "title": "Tables chronologique et thématique consolidées du Journal Officiel de la République Française (Lois et décrets) - 2021",
    "nature": "TABLE",
    "date": "2021-12-31",
    "number": "2021",
    "pdfUrl": "https://www.legifrance.gouv.fr/download/pdf/table?year=2021"
  }
]
```

### Code civil - Article 1134

```json
{
  "id": "LEGIARTI000006436298",
  "title": "Article 1134",
  "text": "Les conventions légalement formées tiennent lieu de loi à ceux qui les ont faites.\nElles ne peuvent être révoquées que de leur consentement mutuel, ou pour les causes que la loi autorise.\nElles doivent être exécutées de bonne foi.",
  "num": "1134",
  "etat": "ABROGE",
  "dateDebut": "1804-03-17",
  "dateFin": "2016-10-01"
}
```

## Ressources supplémentaires

- [Documentation officielle de l'API Légifrance](https://www.legifrance.gouv.fr/contenu/pied-de-page/open-data-et-api)
- [Plateforme PISTE](https://piste.gouv.fr)
- [Description des tris et filtres de l'API](docs/official_documents/Légifrance/description-des-tris-et-filtres-de-l-api.xlsx)
- [Exemples d'utilisation de l'API](docs/official_documents/Légifrance/exemples-d-utilisation-de-l-api.docx) 