#!/usr/bin/env python3
"""
Script d'aide à la souscription aux API PISTE pour l'assistant juridique
"""

import os
import webbrowser
import textwrap
import sys
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
PISTE_API_KEY = os.getenv("PISTE_API_KEY", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
PISTE_SECRET_KEY = os.getenv("PISTE_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")
PISTE_OAUTH_CLIENT_ID = os.getenv("PISTE_OAUTH_CLIENT_ID", "8687ddca-33a7-47d3-a5b7-970b71a6af92")
PISTE_OAUTH_SECRET_KEY = os.getenv("PISTE_OAUTH_SECRET_KEY", "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2")

# URLs
PISTE_SIGNUP_URL = "https://piste.gouv.fr/account/register"
PISTE_LOGIN_URL = "https://piste.gouv.fr/login"
PISTE_API_CENTER_URL = "https://piste.gouv.fr/apimgt/api-center"
PISTE_SUBSCRIPTION_URL = "https://piste.gouv.fr/apimgt/apis"
DATAPASS_URL = "https://datapass.api.gouv.fr/api-entreprise"
LEGIFRANCE_DATAPASS_URL = "https://datapass.api.gouv.fr/dila/legifrance"
API_ENTREPRISE_DATAPASS_URL = "https://datapass.api.gouv.fr/api-entreprise"

# Liste des APIs nécessaires pour l'assistant juridique
REQUIRED_APIS = [
    {
        "name": "Légifrance",
        "description": "Données juridiques (codes, jurisprudence, législation)",
        "datapass_url": LEGIFRANCE_DATAPASS_URL,
        "importance": "Essentielle"
    },
    {
        "name": "API Entreprise",
        "description": "Données sur les entreprises et organismes",
        "datapass_url": API_ENTREPRISE_DATAPASS_URL,
        "importance": "Utile pour les affaires commerciales"
    }
]

def print_header(title):
    """Affiche un en-tête formaté"""
    width = 80
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width + "\n")

def print_section(title):
    """Affiche un titre de section formaté"""
    print(f"\n--- {title} ---\n")

def print_step(number, title):
    """Affiche une étape numérotée"""
    print(f"\n{number}. {title}")

def print_info(text):
    """Affiche un texte informatif avec indentation"""
    for line in textwrap.wrap(text, width=76):
        print(f"   {line}")

def print_api_info(api):
    """Affiche les informations sur une API"""
    print(f"  • {api['name']} - {api['importance']}")
    print(f"    {api['description']}")
    print(f"    URL DataPass: {api['datapass_url']}")

def open_url(url, description):
    """Ouvre une URL dans le navigateur"""
    print(f"\nOuverture de {description}...")
    try:
        webbrowser.open(url)
        print(f"✅ URL ouverte: {url}")
    except Exception as e:
        print(f"❌ Impossible d'ouvrir l'URL: {e}")
        print(f"   Veuillez ouvrir manuellement: {url}")

def show_api_keys():
    """Affiche les clés d'API configurées"""
    print_section("Vos clés d'API actuelles")
    
    # API Key
    print("API Key:")
    print(f"  • Clé: {PISTE_API_KEY}")
    print(f"  • Secret: {PISTE_SECRET_KEY[:4]}{'*' * (len(PISTE_SECRET_KEY) - 8)}{PISTE_SECRET_KEY[-4:]}")
    
    # OAuth
    print("\nOAuth Credentials:")
    print(f"  • Client ID: {PISTE_OAUTH_CLIENT_ID}")
    if PISTE_OAUTH_SECRET_KEY:
        print(f"  • Secret: {PISTE_OAUTH_SECRET_KEY[:4]}{'*' * (len(PISTE_OAUTH_SECRET_KEY) - 8)}{PISTE_OAUTH_SECRET_KEY[-4:]}")
    else:
        print("  • Secret: Non configuré")

def check_environment():
    """Vérifie la configuration des variables d'environnement"""
    print_section("Vérification de l'environnement")
    
    issues = []
    
    # Vérifier les clés API
    if not PISTE_API_KEY or PISTE_API_KEY == "8687ddca-33a7-47d3-a5b7-970b71a6af92":
        issues.append("La clé API PISTE semble être la valeur par défaut, elle pourrait ne pas être valide.")
    
    if not PISTE_SECRET_KEY or PISTE_SECRET_KEY == "bb6476dd-7e31-4e8f-800b-d0e4ed3a9df2":
        issues.append("La clé secrète PISTE semble être la valeur par défaut, elle pourrait ne pas être valide.")
    
    if not PISTE_OAUTH_CLIENT_ID or not PISTE_OAUTH_SECRET_KEY:
        issues.append("Les identifiants OAuth ne sont pas entièrement configurés.")
    
    # Afficher les problèmes ou confirmer que tout est ok
    if issues:
        print("⚠️ Problèmes potentiels détectés:")
        for issue in issues:
            print(f"  • {issue}")
        print("\nCes problèmes peuvent affecter votre capacité à vous connecter aux API PISTE.")
    else:
        print("✅ L'environnement semble correctement configuré.")

def write_env_instructions():
    """Génère des instructions pour configurer les variables d'environnement"""
    print_section("Instructions pour configurer les variables d'environnement")
    
    print("Après avoir créé votre compte PISTE et obtenu vos clés, ajoutez-les à votre fichier .env:")
    
    print("\n```")
    print("# API PISTE configuration")
    print("PISTE_API_KEY=votre_nouvelle_api_key")
    print("PISTE_SECRET_KEY=votre_nouvelle_secret_key")
    print("PISTE_OAUTH_CLIENT_ID=votre_oauth_client_id")
    print("PISTE_OAUTH_SECRET_KEY=votre_oauth_secret_key")
    print("```")
    
    print("\nOu exécutez les commandes suivantes dans votre terminal:")
    
    print("\n```")
    print("export PISTE_API_KEY=votre_nouvelle_api_key")
    print("export PISTE_SECRET_KEY=votre_nouvelle_secret_key")
    print("export PISTE_OAUTH_CLIENT_ID=votre_oauth_client_id")
    print("export PISTE_OAUTH_SECRET_KEY=votre_oauth_secret_key")
    print("```")

def subscription_process():
    """Guide l'utilisateur à travers le processus de souscription aux API"""
    # Étape 1: Créer un compte PISTE si nécessaire
    print_step(1, "Créer un compte PISTE")
    print_info("Si vous n'avez pas encore de compte PISTE, vous devez en créer un.")
    input("Appuyez sur Entrée pour ouvrir la page d'inscription PISTE (ou Ctrl+C pour quitter): ")
    open_url(PISTE_SIGNUP_URL, "page d'inscription PISTE")
    
    # Étape 2: Se connecter à PISTE
    print_step(2, "Se connecter à PISTE")
    print_info("Connectez-vous à votre compte PISTE.")
    input("Appuyez sur Entrée pour ouvrir la page de connexion PISTE: ")
    open_url(PISTE_LOGIN_URL, "page de connexion PISTE")
    
    # Étape 3: Vérifier les APIs souscrites
    print_step(3, "Vérifier vos souscriptions aux API")
    print_info("Vérifiez les API auxquelles vous êtes déjà abonné.")
    input("Appuyez sur Entrée pour ouvrir la page des APIs PISTE: ")
    open_url(PISTE_SUBSCRIPTION_URL, "page des APIs PISTE")
    
    # Étape 4: Souscrire aux API nécessaires
    print_step(4, "Souscrire aux API nécessaires via DataPass")
    print_info("Pour utiliser les API nécessaires à votre assistant juridique, vous devez faire des demandes d'accès via DataPass.")
    print("\nAPIs nécessaires:")
    for api in REQUIRED_APIS:
        print_api_info(api)
    
    # Ouvrir DataPass pour Légifrance
    print("\nDemande d'accès à l'API Légifrance")
    print_info("Vous allez maintenant être redirigé vers DataPass pour demander l'accès à l'API Légifrance.")
    input("Appuyez sur Entrée pour continuer: ")
    open_url(LEGIFRANCE_DATAPASS_URL, "demande d'accès à l'API Légifrance sur DataPass")
    
    # Étape 5: Obtenir et configurer les clés API
    print_step(5, "Obtenir et configurer vos clés API")
    print_info("Une fois vos demandes approuvées, vous recevrez vos clés API. Vous devrez les configurer dans votre application.")
    print_info("Retournez sur PISTE pour voir vos clés API:")
    input("Appuyez sur Entrée pour ouvrir la page de gestion des clés API: ")
    open_url(PISTE_API_CENTER_URL, "page de gestion des clés API")
    
    # Afficher instructions pour configurer les variables d'environnement
    write_env_instructions()

def main():
    print_header("Guide de souscription aux API PISTE pour l'assistant juridique")
    
    print("Ce script vous guidera dans le processus de souscription aux API PISTE")
    print("nécessaires pour votre assistant juridique.")
    print("\nDate: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    # Afficher les clés actuelles
    show_api_keys()
    
    # Vérifier l'environnement
    check_environment()
    
    # Menu principal
    while True:
        print_section("Menu principal")
        print("1. Guide de souscription aux API PISTE")
        print("2. Vérifier les clés API configurées")
        print("3. Instructions pour configurer les variables d'environnement")
        print("4. Quitter")
        
        choice = input("\nChoix (1-4): ")
        
        if choice == "1":
            subscription_process()
        elif choice == "2":
            show_api_keys()
        elif choice == "3":
            write_env_instructions()
        elif choice == "4":
            print("\nAu revoir!")
            return 0
        else:
            print("\n⚠️ Choix invalide. Veuillez réessayer.")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOpération annulée par l'utilisateur.")
        sys.exit(1) 