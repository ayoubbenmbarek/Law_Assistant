# Rapport de Test des Identifiants OAuth

*Date du rapport: 7 avril 2025*

## Résumé des Tests

Nous avons testé deux jeux d'identifiants OAuth pour accéder aux APIs Légifrance et JudiLibre:

### Premier jeu d'identifiants:
- **Client ID**: 8687ddca-33a7-47d3-a5b7-970b71a6af92
- **Client Secret**: bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2

### Deuxième jeu d'identifiants:
- **Client ID**: 8687ddca-33a7-47d3-a5b7-970b71a6af92
- **Client Secret**: bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2

## Résultats des Tests

Pour les deux jeux d'identifiants, nous avons obtenu des erreurs d'authentification similaires:

```
{"error":"invalid_client","error_description":"Client authentication failed (e.g. unknown client, no client authentication included, or unsupported authentication method)."}
```

Nous avons testé plusieurs méthodes d'authentification:
1. OAuth 2.0 standard (client_credentials)
2. OAuth 2.0 avec scope "openid"
3. Authentification HTTP Basic

Aucune des méthodes n'a fonctionné avec les identifiants fournis.

## Analyse

L'erreur "invalid_client" indique généralement que:
- Les identifiants ne sont pas reconnus par le serveur d'authentification
- Les identifiants n'ont pas été activés
- L'application n'est pas correctement configurée sur la plateforme PISTE

## Informations sur les Quotas API

D'après la documentation officielle, les quotas pour l'API JudiLibre sont les suivants:

| Endpoint | Quotas |
|----------|--------|
| `/decision` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/healthcheck` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/transactionalhistory` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/search` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/taxonomy` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/stats` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |
| `/export` | - 1 000 000 requêtes par jour<br>- 20 requêtes par seconde |

Ces quotas sont bien plus élevés que les quotas standard de Légifrance (initialement documentés à 2000 requêtes par jour), ce qui indique que l'API JudiLibre offre une capacité d'utilisation importante une fois l'accès activé.

## Prochaines Étapes Recommandées

1. **Vérifier le statut d'activation**:
   - Connectez-vous à la plateforme PISTE: https://piste.gouv.fr
   - Vérifiez que votre application est active
   - Vérifiez que vous avez bien souscrit aux APIs Légifrance et JudiLibre

2. **Vérifier le statut de votre demande DataPass**:
   - Connectez-vous à DataPass: https://datapass.api.gouv.fr
   - Vérifiez que votre demande d'accès a été approuvée
   - Vérifiez si vous avez reçu des communications concernant votre demande

3. **Créer une nouvelle application sur PISTE**:
   - Si les identifiants actuels ne fonctionnent pas, créez une nouvelle application
   - Souscrivez aux APIs Légifrance et JudiLibre
   - Générez de nouveaux identifiants OAuth

4. **Contacter le support**:
   - Support PISTE: support.api@dila.gouv.fr
   - Mentionnez l'erreur "invalid_client" et les méthodes d'authentification testées
   - Fournissez vos identifiants Client ID (mais jamais le Client Secret)

## Solutions Alternatives

En attendant la résolution des problèmes d'accès:

1. **Utiliser les données open source**:
   - Le script `open_legal_data.py` permet d'accéder à des données juridiques ouvertes
   - Ces données sont moins à jour mais permettent de développer et tester l'application

2. **Utiliser les échantillons de test**:
   - Utiliser les petits échantillons XML du Code Civil et du Code du Travail
   - Ces échantillons sont suffisants pour développer la logique métier de base

## Conclusion

L'accès aux APIs Légifrance et JudiLibre n'est pas encore fonctionnel avec les identifiants fournis. Il est recommandé de vérifier leur activation sur la plateforme PISTE et, si nécessaire, de contacter le support technique. 

Les quotas disponibles une fois l'accès activé sont très généreux (1 million de requêtes par jour pour JudiLibre), ce qui permettra une utilisation intensive des APIs pour votre projet d'assistant juridique. 