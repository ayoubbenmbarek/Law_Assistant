# Référence API JudiLibre

*Ce document fournit une documentation technique de référence pour l'API JudiLibre, le point d'accès à la jurisprudence judiciaire française.*

## Présentation de JudiLibre

JudiLibre est l'API de diffusion des décisions de justice judiciaire. Elle permet l'accès programmatique aux décisions de la Cour de cassation et des juridictions du fond.

## Structure de l'API

### Endpoints principaux

```
Base URL: https://api.piste.gouv.fr/dila/judilibre/v1
```

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/search` | GET | Recherche dans les décisions de justice |
| `/decision` | GET | Récupération d'une décision spécifique |
| `/export` | GET | Export des résultats au format JSON ou XML |
| `/taxonomy` | GET | Récupération des taxonomies (thèmes, juridictions) |
| `/stats` | GET | Statistiques sur les données disponibles |
| `/healthcheck` | GET | Vérification de l'état du service |
| `/transactionalhistory` | GET | Historique des transactions |

## Paramètres de Recherche

### Paramètres généraux

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `query` | string | Termes de recherche | `"propriété intellectuelle"` |
| `date_start` | string | Date de début (format YYYY-MM-DD) | `"2020-01-01"` |
| `date_end` | string | Date de fin (format YYYY-MM-DD) | `"2023-12-31"` |
| `page_size` | int | Nombre de résultats par page (défaut: 10, max: 100) | `20` |
| `page` | int | Numéro de page (commence à 0) | `1` |
| `sort` | string | Champ de tri (`"date"` ou `"score"`) | `"date"` |
| `order` | string | Ordre de tri (`"asc"` ou `"desc"`) | `"desc"` |

### Filtres spécifiques

| Paramètre | Type | Description | Valeurs possibles |
|-----------|------|-------------|-------------------|
| `jurisdiction` | string | Juridiction | `"cc"` (Cour de cassation), `"ca"` (Cours d'appel), `"tgi"` (Tribunaux) |
| `chamber` | string | Chambre | `"soc"` (Sociale), `"crim"` (Criminelle), `"civ1"` (Civile 1ère), `"civ2"` (Civile 2ème), `"civ3"` (Civile 3ème), `"com"` (Commerciale), `"mixte"` (Chambre mixte), `"pl"` (Plénière) |
| `formation` | string | Formation | `"f"` (Formation), `"fs"` (Formation de section), etc. |
| `publication` | string | Type de publication | `"b"` (Bulletin), `"r"` (Rapport), `"p"` (Publié), `"n"` (Non publié) |
| `solution` | string | Solution | `"rejet"` (Rejet), `"cassation"` (Cassation), `"irrecevabilite"` (Irrecevabilité), etc. |
| `themes` | string[] | Thèmes de la décision | Liste de thèmes juridiques |
| `location` | string | Localisation | Code géographique de juridiction |

## Exemples de Requêtes

### Recherche simple

```http
GET /search?query=propriété&jurisdiction=cc&date_start=2020-01-01&date_end=2023-12-31
```

### Recherche avancée

```http
GET /search?query=licenciement&jurisdiction=cc&chamber=soc&publication=b&solution=cassation&date_start=2020-01-01&date_end=2023-12-31&page_size=20&page=0&sort=date&order=desc
```

### Récupération d'une décision spécifique

```http
GET /decision/{id}
```

## Format de Réponse

### Résultat de recherche

```json
{
  "total": 42,
  "page_size": 10,
  "page": 0,
  "results": [
    {
      "id": "6241b2f5b2519013ad4307b9",
      "jurisdiction": "cc",
      "chamber": "soc",
      "number": "19-21.316",
      "decision_date": "2021-03-17",
      "solution": "cassation",
      "title": "Cour de cassation, civile, Chambre sociale, 17 mars 2021, 19-21.316, Publié au bulletin",
      "publication": ["b", "r", "p"],
      "formation": "fs",
      "summary": "Résumé de la décision...",
      "text_extract": "Extrait du texte de la décision contenant les termes recherchés...",
      "files": [
        {
          "name": "Décision",
          "type": "pdf",
          "url": "https://www.courdecassation.fr/decision/6241b2f5b2519013ad4307b9/document"
        }
      ]
    },
    // Autres résultats...
  ]
}
```

### Récupération d'une décision

```json
{
  "id": "6241b2f5b2519013ad4307b9",
  "jurisdiction": "cc",
  "chamber": "soc",
  "number": "19-21.316",
  "decision_date": "2021-03-17",
  "ecli": "ECLI:FR:CCASS:2021:SO00374",
  "solution": "cassation",
  "title": "Cour de cassation, civile, Chambre sociale, 17 mars 2021, 19-21.316, Publié au bulletin",
  "publication": ["b", "r", "p"],
  "formation": "fs",
  "source": "Bulletin",
  "analysis": "Analyse de la décision...",
  "themes": ["CONTRAT DE TRAVAIL, EXECUTION", "LICENCIEMENT"],
  "text": "Texte intégral de la décision...",
  "nac": "41-25-02",
  "files": [
    {
      "name": "Décision",
      "type": "pdf",
      "url": "https://www.courdecassation.fr/decision/6241b2f5b2519013ad4307b9/document"
    }
  ]
}
```

## Codes des Juridictions

### Cour de cassation

| Code | Description |
|------|-------------|
| `cc` | Cour de cassation |

### Chambres de la Cour de cassation

| Code | Description |
|------|-------------|
| `soc` | Chambre sociale |
| `crim` | Chambre criminelle |
| `civ1` | Première chambre civile |
| `civ2` | Deuxième chambre civile |
| `civ3` | Troisième chambre civile |
| `com` | Chambre commerciale |
| `mixte` | Chambre mixte |
| `pl` | Assemblée plénière |

### Cours d'appel

| Code | Description |
|------|-------------|
| `ca` | Toutes les cours d'appel |
| `ca_aix_en_provence` | Cour d'appel d'Aix-en-Provence |
| `ca_paris` | Cour d'appel de Paris |
| ... | ... |

## Gestion des Erreurs

| Code HTTP | Description | Solution possible |
|-----------|-------------|-------------------|
| 400 | Requête mal formée | Vérifier les paramètres de la requête |
| 401 | Non autorisé | Renouveler le token d'authentification |
| 403 | Accès interdit | Vérifier les droits d'accès à l'API |
| 404 | Décision non trouvée | Vérifier l'identifiant de la décision |
| 429 | Trop de requêtes | Respecter les quotas d'utilisation |
| 500 | Erreur serveur | Contacter le support |

## Bonnes Pratiques

1. **Mise en cache**: Mettre en cache les résultats de recherche et les décisions pour éviter des appels répétés.
2. **Pagination**: Utiliser la pagination pour traiter les grands ensembles de résultats.
3. **Recherche ciblée**: Utiliser des filtres pertinents pour limiter le nombre de résultats.
4. **Gestion des erreurs**: Implémenter une gestion robuste des erreurs et des mécanismes de retry.

## Limites et Quotas

### Restrictions de quota par endpoint

| Endpoint | Quotas |
|----------|--------|
| `/decision` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/healthcheck` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/transactionalhistory` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/search` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/taxonomy` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/stats` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/export` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |

### Scopes OAuth

Chaque endpoint de l'API JudiLibre nécessite le scope OAuth `openid`. Voici la liste complète des endpoints et leurs scopes requis:

| Endpoint | Scope requis |
|----------|--------------|
| `/decision` | `openid` |
| `/healthcheck` | `openid` |
| `/transactionalhistory` | `openid` |
| `/search` | `openid` |
| `/taxonomy` | `openid` |
| `/stats` | `openid` |
| `/export` | `openid` |

## Exemple d'Utilisation en Python

```python
import requests
import json

def search_judilibre(token, query, jurisdiction="cc", date_start="2020-01-01", date_end="2023-12-31"):
    """Effectue une recherche dans JudiLibre"""
    
    endpoint = "https://api.piste.gouv.fr/dila/judilibre/v1/search"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    params = {
        "query": query,
        "jurisdiction": jurisdiction,
        "date_start": date_start,
        "date_end": date_end,
        "page_size": 10,
        "sort": "date",
        "order": "desc"
    }
    
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur: {response.status_code} - {response.text}")
        return None
```

## Ressources Complémentaires

- [Documentation officielle de l'API JudiLibre](https://developer.aife.economie.gouv.fr/composants/judilibre)
- [Portail officiel de la Cour de cassation](https://www.courdecassation.fr/)

*Document généré à partir des références officielles de la DILA* 