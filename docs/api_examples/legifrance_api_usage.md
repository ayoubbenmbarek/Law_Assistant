# Documentation API Légifrance PISTE

## Introduction

Cette documentation explique comment utiliser l'API Légifrance pour accéder aux données juridiques françaises à travers la plateforme PISTE (Plateforme d'Intermédiation des Services pour la Transformation de l'État).

## Prérequis

Pour utiliser l'API Légifrance, vous devez:

1. Créer un compte sur [PISTE](https://piste.gouv.fr/)
2. Demander un accès à l'API Légifrance via [DataPass](https://datapass.api.gouv.fr/dila/legifrance)
3. Obtenir vos clés d'API (client_id et client_secret)

## Configuration

```python
# Configuration de l'API
PISTE_API_KEY = "votre_client_id" 
PISTE_SECRET_KEY = "votre_client_secret"
PISTE_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
```

## Authentification

L'API utilise OAuth 2.0 pour l'authentification.

```python
import requests
from datetime import datetime, timedelta

def authenticate():
    """Authentification à l'API Légifrance pour obtenir un token"""
    auth_data = {
        "client_id": PISTE_API_KEY,
        "client_secret": PISTE_SECRET_KEY,
        "grant_type": "client_credentials",
        "scope": "openid"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
        
    response = requests.post(PISTE_AUTH_URL, data=auth_data, headers=headers)
    response.raise_for_status()
    
    auth_result = response.json()
    token = auth_result.get("access_token")
    
    # Token expires in (default 30min)
    expires_in = auth_result.get("expires_in", 1800)
    token_expiry = datetime.now() + timedelta(seconds=expires_in)
    
    return token
```

## Exemples d'utilisation

### Recherche dans les codes

```python
def search_codes(token, query="travail", limit=10, page=1):
    """Recherche dans les codes"""
    endpoint = f"{LEGIFRANCE_API_BASE_URL}/consult/code"
    
    payload = {
        "recherche": {
            "champ": query,
            "pageNumber": page,
            "pageSize": limit
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    
    results = response.json()
    return results
```

### Recherche dans la jurisprudence

```python
def search_jurisprudence(token, query="contrat", limit=10, page=1):
    """Recherche dans la jurisprudence"""
    endpoint = f"{LEGIFRANCE_API_BASE_URL}/consult/juri"
    
    payload = {
        "recherche": {
            "champ": query,
            "pageNumber": page,
            "pageSize": limit
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    
    results = response.json()
    return results
```

### Recherche dans la législation

```python
def search_legislation(token, query="environnement", limit=10, page=1):
    """Recherche dans la législation"""
    endpoint = f"{LEGIFRANCE_API_BASE_URL}/consult/legi"
    
    payload = {
        "recherche": {
            "champ": query,
            "pageNumber": page,
            "pageSize": limit
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    
    results = response.json()
    return results
```

## Format des résultats

### Exemple de résultat de recherche dans les codes

```json
{
  "results": [
    {
      "id": "LEGIARTI000006901785",
      "title": "Article L1237-1 - Code du travail",
      "text": "En cas de résiliation du contrat de travail à durée indéterminée par le salarié, l'existence et la durée du préavis sont fixées par la loi, ou par convention ou accord collectif de travail...",
      "date": "2008-05-01",
      "nature": "ARTICLE",
      "url": "/codes/article_lc/LEGIARTI000006901785"
    },
    {
      "id": "LEGIARTI000035644154",
      "title": "Article L1237-11 - Code du travail",
      "text": "La rupture conventionnelle, exclusive du licenciement ou de la démission, ne peut être imposée par l'une ou l'autre des parties...",
      "date": "2017-09-24",
      "nature": "ARTICLE",
      "url": "/codes/article_lc/LEGIARTI000035644154"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalResults": 124
  }
}
```

## Traitement des erreurs

```python
def handle_api_errors(func):
    """Décorateur pour gérer les erreurs d'API"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("Erreur d'authentification: Token invalide ou expiré")
            elif e.response.status_code == 403:
                print("Accès interdit: Vérifiez vos droits d'accès à l'API")
            elif e.response.status_code == 429:
                print("Trop de requêtes: Limite de taux d'utilisation atteinte")
            else:
                print(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.ConnectionError:
            print("Erreur de connexion: Vérifiez votre connexion internet")
        except Exception as e:
            print(f"Erreur inattendue: {str(e)}")
        return None
    return wrapper

@handle_api_errors
def search_with_error_handling(token, query):
    return search_codes(token, query)
```

## Exemple d'intégration complète

```python
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
PISTE_API_KEY = os.getenv("PISTE_API_KEY")
PISTE_SECRET_KEY = os.getenv("PISTE_SECRET_KEY")
PISTE_AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
LEGIFRANCE_API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"

def main():
    # Authentification
    token = authenticate()
    if not token:
        print("Erreur d'authentification")
        return 1
    
    # Recherche
    query = "rupture conventionnelle"
    results = search_codes(token, query, limit=5)
    
    # Affichage des résultats
    if results:
        print(f"Résultats pour '{query}':")
        for i, item in enumerate(results.get("results", [])):
            print(f"\n--- Résultat {i+1} ---")
            print(f"Titre: {item.get('title')}")
            print(f"Date: {item.get('date')}")
            print(f"URL: {item.get('url')}")
            print(f"Extrait: {item.get('text')[:150]}...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Ressources additionnelles

- [Documentation officielle PISTE](https://developer.aife.economie.gouv.fr)
- [Guide d'utilisation de l'API Légifrance](https://developer.aife.economie.gouv.fr/composants/legifrance)
- [Documentation DataPass](https://datapass.api.gouv.fr/doc/faq)

## Limites et quotas

L'API Légifrance est soumise à des limites d'utilisation:

- 2000 requêtes par jour par clé API
- 10 requêtes par seconde
- Les tokens d'accès expirent après 30 minutes 