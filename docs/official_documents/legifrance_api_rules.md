# Règles d'Accès et d'Utilisation de l'API Légifrance

*Ce document résume les règles officielles d'accès et d'utilisation de l'API Légifrance. Pour la documentation complète, veuillez vous référer aux documents officiels fournis lors de votre inscription.*

## Conditions Générales d'Utilisation

### 1. Cadre Juridique

L'API Légifrance est mise à disposition dans le cadre de la politique d'ouverture des données publiques (Open Data). Son utilisation est soumise au respect des conditions générales d'utilisation de la plateforme PISTE et des conditions spécifiques de l'API Légifrance.

### 2. Procédure d'Accès

L'accès à l'API Légifrance nécessite:
- Une inscription préalable sur la plateforme PISTE
- Une demande d'habilitation via DataPass (https://datapass.api.gouv.fr/dila/legifrance)
- La validation de cette demande par l'administration

### 3. Authentification

L'authentification à l'API se fait par le protocole OAuth 2.0 avec la méthode "client credentials". Les jetons d'accès ont une durée de validité limitée (30 minutes par défaut).

## Limites d'Utilisation

### 1. Quotas

- **Volume quotidien**: 2000 requêtes par jour par compte
- **Débit**: 10 requêtes par seconde maximum
- **Taille des réponses**: Limitée à 2 Mo par défaut

### 2. Disponibilité

- L'API est disponible 24h/24 et 7j/7, sauf pendant les périodes de maintenance
- Les opérations de maintenance sont généralement programmées en dehors des heures ouvrables
- Aucune garantie de niveau de service (SLA) n'est fournie

## Règles d'Utilisation des Données

### 1. Attribution

Toute réutilisation des données doit mentionner la source des données (Légifrance) conformément à la "Licence Ouverte / Open Licence" version 2.0.

### 2. Restrictions

Il est interdit de:
- Présenter les données comme des textes officiels sans mention de leur caractère non-officiel
- Altérer le contenu des textes juridiques
- Revendre l'accès à l'API ou aux données brutes sans valeur ajoutée
- Mettre en cache les données de manière prolongée (plus de 24h recommandé)

### 3. Responsabilité

Les données fournies par l'API Légifrance sont données à titre informatif et n'ont pas de valeur légale officielle. Seuls les textes publiés au Journal Officiel font foi.

## Bonnes Pratiques

### 1. Optimisation des Requêtes

- Limitez le nombre de requêtes en utilisant des filtres appropriés
- Mettez en cache les réponses lorsque c'est pertinent
- Évitez les requêtes trop génériques qui retournent de grands volumes de données

### 2. Gestion des Erreurs

- Implémentez une gestion appropriée des codes d'erreur HTTP
- Mettez en place des mécanismes de retry avec backoff exponentiel
- Surveillez vos quotas d'utilisation

### 3. Mise à Jour

Les données juridiques évoluent constamment. Assurez-vous de:
- Rafraîchir régulièrement vos données en cache
- Vérifier la date de mise à jour des textes
- Informer vos utilisateurs de la date de mise à jour des données présentées

## Contacts et Support

Pour toute question relative à l'utilisation de l'API Légifrance:
- Support technique: support.api@dila.gouv.fr
- Questions d'accès: datapass@api.gouv.fr

*Document révisé le 10/03/2023* 