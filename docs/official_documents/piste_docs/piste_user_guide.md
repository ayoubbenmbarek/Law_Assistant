# Guide d'Utilisation de la Plateforme PISTE

*Ce document résume les informations essentielles pour l'utilisation de la plateforme PISTE (Plateforme d'Intermédiation des Services pour la Transformation de l'État).*

## Présentation de PISTE

PISTE est la plateforme d'API management de l'État français, destinée à simplifier l'accès et l'utilisation des API fournies par les différentes administrations. Elle centralise l'accès à de nombreuses API publiques, dont l'API Légifrance.

## Inscription et Accès

### 1. Création de compte

1. Accédez au portail PISTE: https://piste.gouv.fr/
2. Cliquez sur "Créer un compte"
3. Remplissez le formulaire d'inscription avec des informations professionnelles valides
4. Validez votre compte via l'email de confirmation

### 2. Demande d'accès aux API

Une fois votre compte créé:

1. Connectez-vous à votre espace PISTE
2. Accédez à la section "Catalogue d'API"
3. Sélectionnez l'API désirée (ex: Légifrance)
4. Suivez les instructions spécifiques à l'API (généralement via DataPass)

### 3. Obtention des clés d'API

Après approbation de votre demande:

1. Accédez à "Mes applications" dans votre espace personnel
2. Créez une nouvelle application ou utilisez une existante
3. Souscrivez à l'API avec votre application
4. Récupérez vos clés client (client_id et client_secret)

## Authentification

### 1. Méthode OAuth 2.0

PISTE utilise principalement OAuth 2.0 pour l'authentification:

```python
import requests

def get_piste_token(client_id, client_secret):
    """Obtenir un token d'accès PISTE"""
    
    url = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "openid"  # ou autre scope selon l'API
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Erreur: {response.status_code} - {response.text}")
        return None
```

### 2. Utilisation du token

Utilisez le token obtenu dans l'en-tête Authorization de vos requêtes:

```python
def call_api(token, endpoint, method="GET", data=None):
    """Appeler une API PISTE avec le token"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if method.upper() == "GET":
        response = requests.get(endpoint, headers=headers)
    elif method.upper() == "POST":
        response = requests.post(endpoint, headers=headers, json=data)
    # etc. pour d'autres méthodes
    
    return response
```

## Structure des API

### 1. Format d'URL

Les API PISTE suivent généralement cette structure:
```
https://api.piste.gouv.fr/<fournisseur>/<api>/<ressource>
```

Exemple pour Légifrance:
```
https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/consult/code
```

### 2. Environnements

- **Production**: https://api.piste.gouv.fr/...
- **Bac à sable**: https://sandbox-api.piste.gouv.fr/... (si disponible)

## Bonnes Pratiques

### 1. Sécurité

- Ne partagez jamais vos clés d'API
- Stockez-les dans des variables d'environnement ou des coffres-forts de secrets
- Renouvelez régulièrement vos secrets si possible

### 2. Performance

- Mettez en cache le token OAuth jusqu'à son expiration
- Implémentez des stratégies de retry adaptées
- Respectez les limites de rate (nombre de requêtes par seconde)

### 3. Monitoring

- Suivez vos consommations d'API via le tableau de bord PISTE
- Mettez en place des alertes en cas d'approche des quotas
- Documentez les erreurs rencontrées pour le support

## Ressources Additionnelles

- [Documentation officielle PISTE](https://developer.aife.economie.gouv.fr/)
- [Support PISTE](mailto:support@api.piste.gouv.fr)
- [Guide d'intégration OAuth](https://oauth.piste.gouv.fr/doc)

*Document révisé le 15/03/2023* 