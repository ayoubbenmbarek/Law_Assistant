# Référence API Légifrance

*Ce document fournit une documentation technique de référence pour l'API Légifrance, basée sur les documents officiels fournis par la DILA.*

## Structure de l'API

L'API Légifrance permet d'accéder aux données juridiques françaises via une interface REST structurée. Voici les principales catégories de ressources accessibles:

### 1. Consultation des codes

```
Endpoint: /consult/code
Méthode: POST
```

Permet de rechercher et consulter les articles des codes juridiques français.

**Exemple de requête**:
```json
{
  "path": "/LEGI/CODE/LEGITEXT000006070721",
  "field": "CODE_DESC",
  "operator": "CONTAINS",
  "query": "propriété"
}
```

### 2. Recherche dans la jurisprudence

```
Endpoint: /search/judilibre
Méthode: GET
```

Permet de rechercher dans la base de jurisprudence judiciaire et administrative.

**Paramètres principaux**:
- `query`: Terme de recherche
- `date_start`: Date de début (format YYYY-MM-DD)
- `date_end`: Date de fin (format YYYY-MM-DD)
- `jurisdiction`: Juridiction (Cour de cassation, Conseil d'État, etc.)
- `chamber`: Chambre (chambres civiles, chambre criminelle, etc.)

### 3. Consultation de la législation

```
Endpoint: /consult/jorf
Méthode: POST
```

Permet de consulter les textes publiés au Journal Officiel.

**Exemple de requête**:
```json
{
  "textCid": "JORFTEXT000041746313"
}
```

## Filtres et Options de Tri

### Filtres pour les codes

| Filtre | Description | Valeurs possibles |
|--------|-------------|-------------------|
| `path` | Identifiant du code | `/LEGI/CODE/LEGITEXT000006070721` (Code civil) |
| `field` | Champ de recherche | `CODE_DESC`, `ARTICLE_TITLE`, `ARTICLE_TEXT` |
| `operator` | Opérateur de recherche | `EQUALS`, `CONTAINS`, `STARTS_WITH` |
| `query` | Terme de recherche | Texte libre |
| `date` | Date de version | Format YYYY-MM-DD |

### Filtres pour la jurisprudence

| Filtre | Description | Valeurs possibles |
|--------|-------------|-------------------|
| `jurisdiction` | Juridiction | `CC` (Cour de cassation), `CE` (Conseil d'État) |
| `chamber` | Chambre | `SOC` (sociale), `CRIM` (criminelle), etc. |
| `publication` | Type de publication | `B` (bulletin), `R` (rapport), `P` (publié) |
| `solution` | Solution | `REJET`, `CASSATION`, `ANNULATION` |
| `decision_date` | Date de décision | Format YYYY-MM-DD |

### Options de tri

| Option | Description | Valeurs possibles |
|--------|-------------|-------------------|
| `sort` | Champ de tri | `date` (date), `relevance` (pertinence) |
| `order` | Ordre de tri | `asc` (ascendant), `desc` (descendant) |

## Identifiants et Références

### Identifiants de codes

| Code | Identifiant |
|------|-------------|
| Code civil | `LEGITEXT000006070721` |
| Code pénal | `LEGITEXT000006070719` |
| Code du travail | `LEGITEXT000006072050` |
| Code de commerce | `LEGITEXT000005634379` |
| Code de procédure civile | `LEGITEXT000006070716` |
| Code de procédure pénale | `LEGITEXT000006071154` |

### Types de textes législatifs

| Type | Description | Préfixe |
|------|-------------|---------|
| `LOI` | Loi | `JORFTEXT` |
| `ORDONNANCE` | Ordonnance | `JORFTEXT` |
| `DECRET` | Décret | `JORFTEXT` |
| `ARRETE` | Arrêté | `JORFTEXT` |

## Formats de Réponse

Les réponses de l'API sont au format JSON. Voici un exemple simplifié de réponse pour une recherche dans le Code civil:

```json
{
  "articles": [
    {
      "id": "LEGIARTI000006419280",
      "title": "Article 544",
      "text": "La propriété est le droit de jouir et disposer des choses de la manière la plus absolue, pourvu qu'on n'en fasse pas un usage prohibé par les lois ou par les règlements.",
      "path": "/LEGI/CODE/LEGITEXT000006070721/LEGISCTA000006117830/LEGIARTI000006419280",
      "lastUpdate": "2023-05-15"
    },
    // Autres articles...
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "total": 42
  }
}
```

## Gestion des Erreurs

| Code HTTP | Description | Solution possible |
|-----------|-------------|-------------------|
| 400 | Requête mal formée | Vérifier les paramètres de la requête |
| 401 | Non autorisé | Renouveler le token d'authentification |
| 403 | Accès interdit | Vérifier les droits d'accès à l'API |
| 404 | Ressource non trouvée | Vérifier l'identifiant de la ressource demandée |
| 429 | Trop de requêtes | Respecter les quotas d'utilisation |
| 500 | Erreur serveur | Contacter le support |

## Limites et Quotas

### Restrictions de quota par endpoint

L'API Légifrance applique les quotas suivants pour chaque endpoint:

| Endpoint | Quotas |
|----------|--------|
| `getCnilWithAncienIdUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `listDocsAdminsUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `siretRcSuggestUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `getTablesUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `listBodmrUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `listDossiersLegislatifsUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `listQuestionsEcritesUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `getCommitIdUsingGET` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `listConventionsUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `getArticleWithIdEliOrAliasUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `displayKaliArticleUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `listLODAUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `displayCodeUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `searchUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `displayJuriUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `displayJorfUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `getArticleUsingPOST` | - 2 requêtes par seconde<br>- 50 000 requêtes par jour<br>- 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |

*Remarque: La liste ci-dessus présente une sélection des endpoints les plus couramment utilisés. Tous les endpoints ont les mêmes limitations de quota.*

### Scopes OAuth

Tous les endpoints de l'API Légifrance nécessitent le scope OAuth `openid`. Voici un extrait des endpoints et leurs scopes requis:

| Endpoint | Scope requis |
|----------|--------------|
| `getCnilWithAncienIdUsingPOST` | `openid` |
| `listDocsAdminsUsingPOST` | `openid` |
| `siretRcSuggestUsingPOST` | `openid` |
| `getTablesUsingPOST` | `openid` |
| `listBodmrUsingPOST` | `openid` |
| `listDossiersLegislatifsUsingPOST` | `openid` |
| `listQuestionsEcritesUsingPOST` | `openid` |
| `getCommitIdUsingGET` | `openid` |
| `listConventionsUsingPOST` | `openid` |
| `getArticleWithIdEliOrAliasUsingPOST` | `openid` |
| `displayKaliArticleUsingPOST` | `openid` |
| `displayCodeUsingPOST` | `openid` |
| `searchUsingPOST` | `openid` |
| `displayJuriUsingPOST` | `openid` |
| `displayJorfUsingPOST` | `openid` |
| `getArticleUsingPOST` | `openid` |
| `crossSearchUsingPOST` | `openid` |

*Remarque: Tous les endpoints de l'API Légifrance utilisent le même scope `openid`.*

## Ressources Complémentaires

- [Document officiel: Description des tris et filtres de l'API](../description-des-tris-et-filtres-de-l-api.xlsx)
- [Document officiel: Exemples d'utilisation de l'API](../exemples-d-utilisation-de-l-api.docx)
- [Documentation Swagger 2.0](../Légifrance.json)

*Document généré à partir des références officielles de la DILA* 