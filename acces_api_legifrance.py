#!/usr/bin/env python3
"""
Script d'aide pour accéder à l'API Légifrance avec un compte PISTE existant
"""

import os
import webbrowser
import textwrap
import sys
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# URLs importantes
PISTE_LOGIN_URL = "https://piste.gouv.fr/login"
PISTE_API_CENTER_URL = "https://piste.gouv.fr/apimgt/api-center"
PISTE_SUBSCRIPTION_URL = "https://piste.gouv.fr/apimgt/apis"
LEGIFRANCE_DATAPASS_URL = "https://datapass.api.gouv.fr/dila/legifrance"
PISTE_SUBSCRIBE_LEGIFRANCE_URL = "https://piste.gouv.fr/apimgt/apis/legifrance"
LEGIFRANCE_DOC_URL = "https://developer.aife.economie.gouv.fr/composants/legifrance"

def print_header(title):
    """Affiche un en-tête formaté"""
    width = 80
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width + "\n")

def print_step(number, title):
    """Affiche une étape numérotée"""
    print(f"\n{number}. {title}")

def print_info(text):
    """Affiche un texte informatif avec indentation"""
    for line in textwrap.wrap(text, width=76):
        print(f"   {line}")

def open_url(url, description):
    """Ouvre une URL dans le navigateur"""
    print(f"\nOuverture de {description}...")
    try:
        webbrowser.open(url)
        print(f"✅ URL ouverte: {url}")
    except Exception as e:
        print(f"❌ Impossible d'ouvrir l'URL: {e}")
        print(f"   Veuillez ouvrir manuellement: {url}")

def guide_legifrance_access():
    """Guide l'utilisateur pour accéder à l'API Légifrance"""
    print_header("Accès à l'API Légifrance via PISTE")
    
    # Étape 1: Se connecter à PISTE
    print_step(1, "Se connecter à votre compte PISTE")
    print_info("Connectez-vous à votre compte PISTE existant.")
    input("Appuyez sur Entrée pour ouvrir la page de connexion PISTE: ")
    open_url(PISTE_LOGIN_URL, "page de connexion PISTE")
    
    # Étape 2: Accéder à l'API Légifrance
    print_step(2, "S'abonner à l'API Légifrance sur PISTE")
    print_info("Vous devez d'abord vous abonner à l'API Légifrance sur PISTE.")
    input("Appuyez sur Entrée pour accéder à la page de l'API Légifrance: ")
    open_url(PISTE_SUBSCRIBE_LEGIFRANCE_URL, "page de l'API Légifrance sur PISTE")
    
    # Étape 3: Faire une demande d'accès via DataPass
    print_step(3, "Faire une demande d'accès via DataPass")
    print_info("L'accès à l'API Légifrance nécessite une habilitation via DataPass.")
    print_info("Vous allez maintenant être redirigé vers DataPass pour faire votre demande.")
    print_info("Vous devrez indiquer le motif de votre demande et fournir les informations requises.")
    input("Appuyez sur Entrée pour continuer vers DataPass: ")
    open_url(LEGIFRANCE_DATAPASS_URL, "page de demande d'accès DataPass pour Légifrance")
    
    # Étape 4: Consulter la documentation
    print_step(4, "Consulter la documentation de l'API Légifrance")
    print_info("En attendant que votre demande soit traitée, vous pouvez consulter la documentation.")
    input("Appuyez sur Entrée pour accéder à la documentation: ")
    open_url(LEGIFRANCE_DOC_URL, "documentation de l'API Légifrance")
    
    # Étape 5: Configurer vos clés API
    print_step(5, "Configurer vos clés API")
    print_info("Une fois votre demande approuvée, retournez sur PISTE pour récupérer vos clés API.")
    input("Appuyez sur Entrée pour accéder au centre d'API PISTE: ")
    open_url(PISTE_API_CENTER_URL, "centre d'API PISTE")
    
    # Instructions pour configurer les variables d'environnement
    print_step(6, "Configurer les variables d'environnement")
    print_info("Après avoir récupéré vos clés, configurez-les dans votre application:")
    
    print("\n```")
    print("# Dans votre fichier .env")
    print("PISTE_API_KEY=votre_nouvelle_api_key")
    print("PISTE_SECRET_KEY=votre_nouvelle_secret_key")
    print("```")
    
    print("\nOu dans votre terminal:")
    
    print("\n```")
    print("export PISTE_API_KEY=votre_nouvelle_api_key")
    print("export PISTE_SECRET_KEY=votre_nouvelle_secret_key")
    print("```")
    
    # Information sur les délais
    print_step(7, "Attendre l'approbation")
    print_info("Le traitement de votre demande peut prendre plusieurs jours. Vous recevrez ")
    print_info("une notification par email lorsque votre demande aura été approuvée.")
    
    print("\n----------------------------")
    print("Processus terminé! En attendant l'accès à l'API, vous pouvez:")
    print("- Utiliser les données juridiques open data disponibles sur data.gouv.fr")
    print("- Consulter directement le site legifrance.gouv.fr pour vos recherches manuelles")
    print("- Préparer votre application pour intégrer l'API une fois l'accès obtenu")

def main():
    try:
        guide_legifrance_access()
        print("\nAu revoir!")
        return 0
    except KeyboardInterrupt:
        print("\n\nOpération annulée par l'utilisateur.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 