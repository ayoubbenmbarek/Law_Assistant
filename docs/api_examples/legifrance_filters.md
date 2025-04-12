# Filtres et Tri pour l'API Légifrance

Ce document présente les options de filtrage et de tri disponibles dans l'API Légifrance pour affiner vos recherches juridiques.

## Recherche dans les Codes

### Options de Tri

```python
# Tri par pertinence (par défaut)
payload = {
    "recherche": {
        "champ": "droit travail",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "pertinence"
    }
}

# Tri par date (du plus récent au plus ancien)
payload = {
    "recherche": {
        "champ": "droit travail",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "date desc"
    }
}

# Tri par date (du plus ancien au plus récent)
payload = {
    "recherche": {
        "champ": "droit travail",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "date asc"
    }
}
```

### Filtres par Code

```python
# Filtrer par un code spécifique (exemple: Code du travail)
payload = {
    "recherche": {
        "champ": "contrat",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "CODE",
                "value": "LEGITEXT000006072050"  # ID du Code du travail
            }
        ]
    }
}

# Codes courants et leurs identifiants
codes = {
    "Code civil": "LEGITEXT000006070721",
    "Code du travail": "LEGITEXT000006072050",
    "Code de commerce": "LEGITEXT000005634379",
    "Code pénal": "LEGITEXT000006070719",
    "Code de procédure pénale": "LEGITEXT000006071154",
    "Code de procédure civile": "LEGITEXT000006070716",
    "Code de la santé publique": "LEGITEXT000006072665",
    "Code général des impôts": "LEGITEXT000006069577",
    "Code de l'environnement": "LEGITEXT000006074220",
    "Code de la consommation": "LEGITEXT000006069565"
}
```

### Filtres par Type d'Article

```python
# Filtrer par type d'article (exemple: ARTICLE)
payload = {
    "recherche": {
        "champ": "licenciement",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "NATURE",
                "value": "ARTICLE"
            }
        ]
    }
}

# Types d'articles disponibles:
# - ARTICLE
# - ANNEXE
# - SECTION
# - CHAPITRE
# - TITRE
# - LIVRE
# - PARTIE
```

### Filtres par Date

```python
# Filtrer par plage de dates
payload = {
    "recherche": {
        "champ": "droit travail",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "DATE_VERSION",
                "start": "2020-01-01",  # Date au format YYYY-MM-DD
                "end": "2022-12-31"
            }
        ]
    }
}

# Filtrer les articles en vigueur
payload = {
    "recherche": {
        "champ": "droit travail",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "ETAT",
                "value": "VIGUEUR"
            }
        ]
    }
}
```

### Combinaison de Filtres

```python
# Combiner plusieurs filtres
payload = {
    "recherche": {
        "champ": "congé parental",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "date desc",
        "filtres": [
            {
                "name": "CODE",
                "value": "LEGITEXT000006072050"  # Code du travail
            },
            {
                "name": "NATURE",
                "value": "ARTICLE"
            },
            {
                "name": "ETAT",
                "value": "VIGUEUR"
            }
        ]
    }
}
```

## Recherche dans la Jurisprudence

### Options de Tri

```python
# Tri par date (par défaut)
payload = {
    "recherche": {
        "champ": "licenciement sans cause réelle",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "date desc"
    }
}

# Tri par pertinence
payload = {
    "recherche": {
        "champ": "licenciement sans cause réelle",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "pertinence"
    }
}
```

### Filtres par Juridiction

```python
# Filtrer par juridiction (exemple: Cour de cassation)
payload = {
    "recherche": {
        "champ": "rupture conventionnelle",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "JURIDICTION",
                "value": "Cour de cassation"
            }
        ]
    }
}

# Juridictions principales:
# - Cour de cassation
# - Conseil d'État
# - Cour d'appel
# - Tribunal administratif
# - Conseil constitutionnel
```

### Filtres par Formation

```python
# Filtrer par formation (exemple: Chambre sociale)
payload = {
    "recherche": {
        "champ": "harcèlement moral",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "FORMATION",
                "value": "CHAMBRE_SOCIALE"
            }
        ]
    }
}

# Formations de la Cour de cassation:
# - CHAMBRE_SOCIALE
# - CHAMBRE_CIVILE_1
# - CHAMBRE_CIVILE_2
# - CHAMBRE_CIVILE_3
# - CHAMBRE_COMMERCIALE
# - CHAMBRE_CRIMINELLE
# - ASSEMBLEE_PLENIERE
# - CHAMBRE_MIXTE
```

### Filtres par Solution

```python
# Filtrer par solution (exemple: Rejet)
payload = {
    "recherche": {
        "champ": "temps de travail",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "SOLUTION",
                "value": "REJET"
            }
        ]
    }
}

# Solutions possibles:
# - REJET
# - CASSATION
# - CASSATION_PARTIELLE
# - CASSATION_SANS_RENVOI
# - IRRECEVABILITE
# - NON_LIEU_A_STATUER
```

### Filtres par Date

```python
# Filtrer par plage de dates
payload = {
    "recherche": {
        "champ": "préjudice d'anxiété",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "DATE_DECISION",
                "start": "2019-01-01",
                "end": "2022-12-31"
            }
        ]
    }
}
```

## Recherche dans la Législation

### Options de Tri

```python
# Tri par pertinence (par défaut)
payload = {
    "recherche": {
        "champ": "loi climat",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "pertinence"
    }
}

# Tri par date (du plus récent au plus ancien)
payload = {
    "recherche": {
        "champ": "loi climat",
        "pageNumber": 1,
        "pageSize": 10,
        "sort": "date desc"
    }
}
```

### Filtres par Nature de Texte

```python
# Filtrer par nature de texte (exemple: LOI)
payload = {
    "recherche": {
        "champ": "réforme",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "NATURE",
                "value": "LOI"
            }
        ]
    }
}

# Natures de texte possibles:
# - LOI
# - ORDONNANCE
# - DECRET
# - ARRETE
# - CIRCULAIRE
```

### Filtres par Date

```python
# Filtrer par plage de dates de signature
payload = {
    "recherche": {
        "champ": "réforme",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "DATE_SIGNATURE",
                "start": "2020-01-01",
                "end": "2022-12-31"
            }
        ]
    }
}

# Filtrer par plage de dates de publication
payload = {
    "recherche": {
        "champ": "réforme",
        "pageNumber": 1,
        "pageSize": 10,
        "filtres": [
            {
                "name": "DATE_PUBLICATION",
                "start": "2020-01-01",
                "end": "2022-12-31"
            }
        ]
    }
}
```

## Exemples d'Utilisation en Python

### Fonction de Recherche avec Filtres

```python
def search_with_filters(client, query, source_type="code", filters=None, sort="pertinence", page=1, limit=10):
    """
    Recherche avec filtres dans l'API Légifrance
    
    Args:
        client (LegifranceAPI): Client API Légifrance
        query (str): Terme de recherche
        source_type (str): Type de source ('code', 'jurisprudence', 'legislation')
        filters (list): Liste de filtres à appliquer
        sort (str): Ordre de tri ('pertinence', 'date asc', 'date desc')
        page (int): Numéro de page
        limit (int): Nombre de résultats par page
    
    Returns:
        dict: Résultats de la recherche
    """
    # Construire la requête de base
    payload = {
        "recherche": {
            "champ": query,
            "pageNumber": page,
            "pageSize": limit,
            "sort": sort
        }
    }
    
    # Ajouter les filtres si fournis
    if filters:
        payload["recherche"]["filtres"] = filters
    
    # Déterminer l'endpoint selon le type de source
    if source_type == "code":
        return client.search_codes(query, limit, page, filters)
    elif source_type == "jurisprudence":
        return client.search_jurisprudence(query, limit, page, filters=filters)
    elif source_type == "legislation":
        endpoint = f"{client.base_url}/consult/legi"
        # Appel à l'API...
    
    return None
```

### Exemples de Recherches Complexes

```python
# Exemple: Recherche d'articles du Code du travail sur le télétravail, en vigueur, triés par date
from legifrance_api_example import LegifranceAPI

client = LegifranceAPI()

filters = [
    {"name": "CODE", "value": "LEGITEXT000006072050"},  # Code du travail
    {"name": "NATURE", "value": "ARTICLE"},
    {"name": "ETAT", "value": "VIGUEUR"}
]

results = client.search_codes("télétravail", limit=10, page=1, filters=filters)

# Exemple: Recherche de jurisprudence de la Chambre sociale sur le burnout depuis 2020
filters = [
    {"name": "FORMATION", "value": "CHAMBRE_SOCIALE"},
    {"name": "DATE_DECISION", "start": "2020-01-01"}
]

results = client.search_jurisprudence("burnout syndrome épuisement", limit=10, page=1, filters=filters)
```

## Astuces pour Optimiser vos Recherches

1. **Utilisez des synonymes** dans vos requêtes pour élargir les résultats
2. **Combinez les filtres** pour des recherches plus précises
3. **Utilisez le tri par pertinence** pour les recherches exploratoires
4. **Utilisez le tri par date** pour suivre les évolutions récentes
5. **Limitez le nombre de résultats** par page (10-20) pour des performances optimales
6. **Enregistrez les identifiants** des codes et articles importants pour y accéder directement

## Notes Importantes

- Les identifiants des codes et articles peuvent changer avec le temps
- Certaines combinaisons de filtres peuvent ne renvoyer aucun résultat
- Les résultats peuvent varier en fonction des mises à jour de l'API
- Les requêtes sont limitées à un certain nombre par jour et par seconde 