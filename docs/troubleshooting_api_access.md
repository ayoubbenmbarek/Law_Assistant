# Guide de Résolution des Problèmes d'Accès aux APIs

Ce document fournit des conseils pour diagnostiquer et résoudre les problèmes d'accès aux APIs de Légifrance et JudiLibre via la plateforme PISTE.

## Problèmes d'Authentification

### Erreur "invalid_client"

Si vous rencontrez l'erreur:
```
{"error":"invalid_client","error_description":"Client authentication failed (e.g. unknown client, no client authentication included, or unsupported authentication method)."}
```

#### Causes possibles:

1. **Identifiants incorrects**: Les clés API (client_id et client_secret) sont incorrectes ou mal formatées.
2. **Application non activée**: Votre application n'est pas encore activée sur la plateforme PISTE.
3. **Souscription manquante**: Vous n'avez pas souscrit à l'API que vous essayez d'utiliser.
4. **Problème de configuration**: L'application n'est pas correctement configurée pour l'API désirée.

#### Solutions:

1. **Vérifiez vos identifiants**: Assurez-vous que le client_id et le client_secret sont correctement copiés, sans espaces supplémentaires.
2. **Vérifiez le statut de votre application**:
   - Connectez-vous à [PISTE](https://piste.gouv.fr)
   - Accédez à "Mes applications"
   - Vérifiez que le statut de votre application est "Actif"
3. **Vérifiez vos souscriptions**:
   - Dans votre espace PISTE, allez dans "Mes souscriptions"
   - Assurez-vous que vous avez bien souscrit à l'API que vous essayez d'utiliser
   - Vérifiez que votre souscription est active
4. **Renouvelez vos clés**:
   - Si vos clés sont anciennes, essayez de les renouveler
   - Dans "Mes applications", sélectionnez votre application
   - Cliquez sur "Renouveler les clés"

### Problème avec le scope

Si vous avez essayé différentes valeurs de "scope" sans succès:

#### Solutions:

1. **Utilisez le scope correct**:
   - Pour Légifrance et JudiLibre, le scope standard est généralement "openid"
   - Si cela ne fonctionne pas, essayez sans spécifier de scope
2. **Vérifiez la documentation spécifique**:
   - Certaines APIs nécessitent des scopes spécifiques
   - Consultez la documentation officielle de l'API concernée

## Problèmes d'Accès à l'API

Si vous avez obtenu un token mais que l'accès à l'API échoue:

### Erreur 403 (Forbidden)

#### Causes possibles:

1. **Droits insuffisants**: Votre application n'a pas les droits nécessaires pour accéder à l'API.
2. **Souscription limitée**: Votre souscription a des limitations qui empêchent l'accès.

#### Solutions:

1. **Vérifiez les droits de votre application**: Assurez-vous que votre application a les droits nécessaires.
2. **Vérifiez votre souscription DataPass**: Si vous avez demandé l'accès via DataPass, vérifiez le statut de votre demande.

### Erreur 429 (Too Many Requests)

#### Causes possibles:

1. **Quota dépassé**: Vous avez dépassé le nombre de requêtes autorisées.
2. **Rate limit**: Vous envoyez des requêtes trop rapidement.

#### Solutions:

1. **Respectez les quotas**: Limitez le nombre de requêtes à 2000 par jour.
2. **Implémentez un rate limiting**: Limitez vos requêtes à 10 par seconde maximum.

## Étapes de Vérification sur la Plateforme PISTE

1. **Vérifiez votre compte PISTE**:
   - Assurez-vous que votre compte est actif
   - Vérifiez que vous avez complété toutes les informations requises

2. **Vérifiez votre application**:
   - Assurez-vous que vous avez bien créé une application
   - Vérifiez que l'application est configurée pour le type d'authentification OAuth 2.0

3. **Vérifiez vos souscriptions**:
   - Assurez-vous d'avoir souscrit aux APIs que vous souhaitez utiliser
   - Vérifiez que ces souscriptions sont associées à votre application

4. **Vérifiez vos demandes DataPass**:
   - Connectez-vous à [DataPass](https://datapass.api.gouv.fr)
   - Vérifiez le statut de vos demandes d'accès
   - Si une demande est en attente, contactez le support

## Outils de Diagnostic

### Scripts de Test

Ce projet inclut plusieurs scripts pour tester l'accès aux APIs:

- `test_legifrance_connection.py`: Test complet de connexion aux APIs Légifrance et JudiLibre
- `test_legifrance_basic_auth.py`: Test avec authentification basique
- `test_piste_auth_official.py`: Test suivant strictement la documentation officielle

Exécutez ces scripts pour diagnostiquer précisément les problèmes d'accès.

### Exemple de Requête Curl

Pour tester l'authentification avec curl:

```bash
curl -X POST https://sandbox-oauth.piste.gouv.fr/api/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=VOTRE_CLIENT_ID&client_secret=VOTRE_CLIENT_SECRET"
```

## Contact et Support

Si vous ne parvenez pas à résoudre votre problème:

1. **Support PISTE**: support.api@dila.gouv.fr
2. **Support DataPass**: assistance.datapass@api.gouv.fr
3. **Forum API.gouv.fr**: https://forum.api.gouv.fr

## Délais d'Activation

Notez que l'activation des accès peut prendre:
- 24-48h pour l'activation de votre compte PISTE
- Jusqu'à 2 semaines pour la validation d'une demande DataPass

Soyez patient et gardez un œil sur vos emails pour les notifications. 