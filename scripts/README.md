# Guide d'utilisation de l'API Légifrance

Ce document fournit une documentation pour l'utilisation de l'API Légifrance (PISTE/DILA) dans le contexte de l'application Law Assistant.

## Configuration

Pour utiliser l'API Légifrance, vous devez disposer des identifiants d'API suivants :

- `PISTE_API_KEY` (Client ID)
- `PISTE_SECRET_KEY` (Client Secret)

Ces identifiants peuvent être configurés :
1. Dans un fichier `.env` à la racine du projet
2. Ou en les définissant directement comme variables d'environnement

Exemple de fichier `.env` :
```
PISTE_API_KEY=votre_client_id
PISTE_SECRET_KEY=votre_client_secret
```

## Authentification

L'API Légifrance utilise OAuth 2.0 avec le flux "client credentials" pour l'authentification. Voici le processus :

1. Envoi d'une requête à l'URL d'authentification avec les identifiants
2. Récupération d'un token JWT valide pour une durée limitée (généralement 30 minutes)
3. Utilisation du token dans l'en-tête `Authorization` pour les requêtes API

Le client Python implémenté dans ce projet gère automatiquement l'obtention et le renouvellement du token lorsque nécessaire.

## Environnements disponibles

Deux environnements sont disponibles pour l'API Légifrance :

- **Sandbox** : Environnement de test avec des données limitées (`https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app`)
- **Production** : Environnement de production avec les données complètes (`https://api.piste.gouv.fr/dila/legifrance/lf-engine-app`)

Par défaut, le client utilise l'environnement Sandbox pour les tests.

## Endpoints principaux

L'API Légifrance est organisée en plusieurs contrôleurs, chacun couvrant un aspect spécifique des données juridiques :

### Consult Controller (Consultation de textes)

| Endpoint | Description |
|----------|-------------|
| `consult/getCnilWithAncienId` | Récupère une délibération CNIL par son ancien ID |
| `consult/getArticleWithIdEliOrAlias` | Récupère un article par son ID ELI ou alias |
| `consult/kaliArticle` | Récupère un article de convention collective (KALI) |
| `consult/sameNumArticle` | Récupère les articles ayant eu le même numéro (versions précédentes) |
| `consult/concordanceLinksArticle` | Récupère les liens de concordance d'un article |
| `consult/getTables` | Récupère les tables annuelles pour une période donnée |

### Search Controller (Recherche dans les textes)

| Endpoint | Description |
|----------|-------------|
| `search/jurisprudence` | Recherche dans la jurisprudence |
| `search/loda` | Recherche dans les textes de type LODA (Lois, Ordonnances, Décrets, Arrêtés) |
| `search/code` | Recherche dans les codes |
| `search/acco` | Recherche dans les accords d'entreprise |
| `search/cnil` | Recherche dans les délibérations CNIL |
| `search/dossierLegislatif` | Recherche dans les dossiers législatifs |
| `search/conseilEtat` | Recherche dans les avis du Conseil d'État |

### List Controller (Listes paginées)

| Endpoint | Description |
|----------|-------------|
| `list/bodmr` | Liste des bulletins officiels des décorations, médailles et récompenses |
| `list/conventions` | Liste des conventions collectives |
| `list/dossiersLegislatifs` | Liste des dossiers législatifs |
| `list/questionsEcritesParlementaires` | Liste des questions écrites parlementaires |
| `list/loda` | Liste des textes LODA (Lois, Ordonnances, Décrets, Arrêtés) |
| `list/docsAdmins` | Liste des documents administratifs |

### Suggest Controller (Autosuggestion)

| Endpoint | Description |
|----------|-------------|
| `suggest/acco` | Suggestions de SIRET et raisons sociales pour les accords d'entreprise |

## Exemple d'utilisation

Le script `test_legifrance_api.py` montre comment utiliser l'API pour :

1. S'authentifier auprès du service
2. Récupérer une délibération CNIL
3. Rechercher dans la jurisprudence
4. Lister les conventions collectives

Pour exécuter le script de test :

```bash
python scripts/test_legifrance_api.py
```

## Paramètres de filtrage et de tri

La plupart des endpoints prennent en charge les paramètres suivants :

- `page` : Numéro de la page (commençant à 1)
- `pageSize` : Nombre d'éléments par page
- `sort` : Critère de tri (varie selon les endpoints)

Pour les recherches :
- `query` : Texte de recherche
- Des filtres spécifiques selon le type de document (date, juridiction, etc.)

Voir le fichier de documentation détaillée des tris et filtres pour plus d'informations.

## Limites et quotas

L'API Légifrance est soumise à des limites d'utilisation :

- **Sandbox** : Limite de 2000 requêtes par jour et 2 requêtes par seconde
- **Production** : Selon les termes de votre abonnement

Les réponses incluent des en-têtes indiquant la consommation des quotas :
- `X-RateLimit-Remaining` : Nombre de requêtes restantes
- `X-RateLimit-Reset` : Temps restant avant réinitialisation du quota

## Exemples d'implémentation

Notre projet utilise l'API Légifrance de plusieurs façons :

1. **Recherche directe** : Utilisation des endpoints de recherche pour obtenir des données juridiques
2. **Importation dans la base vectorielle** : Stockage local des données pour des recherches plus rapides
3. **Combinaison avec d'autres sources** : Intégration des résultats de l'API avec d'autres sources juridiques

## Ressources supplémentaires

- [Documentation officielle Swagger](https://developer.aife.economie.gouv.fr/api-catalogue-sandbox) (requiert un compte PISTE)
- [Portail PISTE](https://piste.gouv.fr/)
- [Documentation détaillée des tris et filtres](docs/official_documents/Légifrance/description-des-tris-et-filtres-de-l-api.xlsx)
- [Exemples d'utilisation](docs/official_documents/Légifrance/exemples-d-utilisation-de-l-api.docx)

## Dépannage

Si vous rencontrez des problèmes avec l'API Légifrance :

1. Vérifiez la validité de vos identifiants API
2. Assurez-vous que votre quota n'est pas épuisé
3. Vérifiez les logs pour des messages d'erreur spécifiques
4. Consultez le document `troubleshooting_api_access.md` pour des solutions courantes

Pour toute question concernant l'API Légifrance, vous pouvez contacter l'équipe DILA à l'adresse : retours-legifrance-modernise@dila.gouv.fr 