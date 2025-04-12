#!/usr/bin/env python3
"""
Script pour explorer l'API Légifrance et ses différentes fonctionnalités
Ce script démontre l'utilisation des différents endpoints de l'API Légifrance
et affiche les résultats au format JSON.
"""

import os
import json
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
import time
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
os.makedirs("logs", exist_ok=True)
logger.add("logs/explore_api.log", rotation="10 MB")

console = Console()

# Liste des fonctionnalités disponibles pour l'exploration
AVAILABLE_FEATURES = [
    "tables", "cnil", "codes", "jurisprudence", "conventions", "loda",
    "articles", "kali", "questions", "dossiers", "docsadmins", "bodmr",
    "concordance", "suggest", "all"
]

async def main():
    """Fonction principale"""
    from app.data.legifrance_api import LegifranceAPI
    
    parser = argparse.ArgumentParser(description="Explorer les fonctionnalités de l'API Légifrance")
    parser.add_argument("--feature", choices=AVAILABLE_FEATURES, required=True,
                       help="Fonctionnalité à explorer")
    parser.add_argument("--query", type=str, default="",
                       help="Requête de recherche (pour search)")
    parser.add_argument("--id", type=str, default="",
                       help="Identifiant spécifique (pour consult)")
    parser.add_argument("--year", type=int, default=None,
                       help="Année (pour tables)")
    parser.add_argument("--sandbox", action="store_true", default=True,
                       help="Utiliser l'environnement sandbox")
    args = parser.parse_args()
    
    feature = args.feature
    query = args.query
    doc_id = args.id
    year = args.year
    use_sandbox = args.sandbox
    
    console.print(Panel.fit(f"[bold blue]Exploration de l'API Légifrance[/bold blue]\nFonctionnalité: [yellow]{feature}[/yellow]"))
    
    # Initialiser le client API
    legifrance = LegifranceAPI(use_sandbox=use_sandbox)
    
    # Authentifier
    await legifrance.authenticate()
    console.print("[green]✓[/green] Authentification réussie")
    
    # Explorer la fonctionnalité demandée
    if feature == "all":
        await explore_all(legifrance)
    else:
        await explore_feature(legifrance, feature, query, doc_id, year)

async def explore_all(legifrance):
    """Explorer toutes les fonctionnalités principales"""
    console.print("[bold]Exploration de plusieurs fonctionnalités de l'API...[/bold]")
    
    # Tables
    console.print("[bold cyan]Tables annuelles[/bold cyan]")
    await explore_feature(legifrance, "tables", year=datetime.now().year - 1)
    
    # Codes (Code Civil)
    console.print("\n[bold cyan]Recherche dans les codes[/bold cyan]")
    await explore_feature(legifrance, "codes", query="contrat")
    
    # Jurisprudence récente
    console.print("\n[bold cyan]Recherche de jurisprudence récente[/bold cyan]")
    await explore_feature(legifrance, "jurisprudence", query="licenciement")
    
    # LODA
    console.print("\n[bold cyan]Liste des LODA (LOI, Décrets, etc.)[/bold cyan]")
    await explore_feature(legifrance, "loda")
    
    # Conventions collectives
    console.print("\n[bold cyan]Conventions collectives[/bold cyan]")
    await explore_feature(legifrance, "conventions")

async def explore_feature(legifrance, feature, query="", doc_id="", year=None):
    """Explorer une fonctionnalité spécifique de l'API"""
    result = None
    
    try:
        if feature == "tables":
            # Tables annuelles
            result = await legifrance.get_tables(start_year=year, end_year=year)
            
        elif feature == "cnil":
            # Délibérations CNIL
            cnil_id = doc_id or "20070210"  # ID par défaut
            result = await legifrance.get_cnil_with_ancien_id(cnil_id)
            
        elif feature == "codes":
            # Recherche dans les codes
            search_query = query or "contrat de travail"
            result = await legifrance.search_codes(search_query, page=1, page_size=5)
            
        elif feature == "jurisprudence":
            # Recherche dans la jurisprudence
            search_query = query or "licenciement"
            result = await legifrance.search_jurisprudence(search_query, page=1, page_size=5)
            
        elif feature == "conventions":
            # Liste des conventions collectives
            result = await legifrance.list_conventions(page=1, page_size=5)
            
        elif feature == "loda":
            # Liste des textes LODA (Lois, Ordonnances, Décrets, Arrêtés)
            result = await legifrance.list_loda(page=1, page_size=5)
            
        elif feature == "articles":
            # Détail d'un article
            article_id = doc_id or "LEGIARTI000006420207"  # Article 1134 du Code Civil par défaut
            result = await legifrance.get_article_with_id_eli_or_alias(id_eli=article_id)
            
        elif feature == "kali":
            # Consulter un article de convention collective
            kali_id = doc_id or "KALIARTI000005820259"
            result = await legifrance.get_kali_article(kali_id)
            
        elif feature == "docsadmins":
            # Liste des documents administratifs
            years_list = [year] if year else [2020, 2021, 2022]
            result = await legifrance.list_docs_admins(years_list)
            
        elif feature == "bodmr":
            # Liste des bulletins officiels des décorations
            result = await legifrance.list_bodmr(page=1, page_size=5)
            
        elif feature == "dossiers":
            # Liste des dossiers législatifs
            result = await legifrance.list_dossiers_legislatifs(page=1, page_size=5)
            
        elif feature == "questions":
            # Liste des questions écrites parlementaires
            result = await legifrance.list_questions_ecrites(page=1, page_size=5)
            
        elif feature == "concordance":
            # Liens de concordance d'un article
            article_id = doc_id or "LEGIARTI000006420207"
            result = await legifrance.get_concordance_links_article(article_id)
            
        elif feature == "suggest":
            # Suggestions accords d'entreprise
            suggest_query = query or "Michelin"
            result = await legifrance.suggest_acco(suggest_query)
    
    except Exception as e:
        console.print(f"[bold red]Erreur:[/bold red] {str(e)}")
        logger.error(f"Erreur lors de l'exploration de la fonctionnalité {feature}: {str(e)}")
        return
    
    # Afficher les résultats
    display_result(result, feature)

def display_result(result, feature):
    """Affiche les résultats de façon formatée"""
    if result is None:
        console.print("[yellow]Aucun résultat[/yellow]")
        return
    
    # Formatter le résultat en JSON
    result_json = json.dumps(result, ensure_ascii=False, indent=2)
    
    # Limiter la taille si très grand
    if len(result_json) > 4000:
        # Troncation intelligente selon le type de résultat
        if isinstance(result, list):
            # Pour les listes, afficher quelques éléments
            truncated = json.dumps(result[:2], ensure_ascii=False, indent=2)
            console.print(f"[blue]Résultat tronqué ({len(result)} éléments au total):[/blue]")
            syntax = Syntax(truncated, "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif isinstance(result, dict) and "results" in result:
            # Pour les résultats de recherche avec pagination
            count = len(result.get("results", []))
            total = result.get("totalResultNumber", count)
            truncated_results = result.copy()
            truncated_results["results"] = result["results"][:2] if "results" in result else []
            truncated = json.dumps(truncated_results, ensure_ascii=False, indent=2)
            console.print(f"[blue]Résultat tronqué ({count} résultats affichés sur {total} au total):[/blue]")
            syntax = Syntax(truncated, "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            # Pour les autres types, montrer le début
            console.print(f"[blue]Résultat tronqué ({len(result_json)} caractères):[/blue]")
            syntax = Syntax(result_json[:2000] + "...", "json", theme="monokai", line_numbers=True)
            console.print(syntax)
    else:
        # Afficher tout le résultat
        syntax = Syntax(result_json, "json", theme="monokai", line_numbers=True)
        console.print(syntax)
    
    # Statistiques et informations supplémentaires
    if isinstance(result, list):
        console.print(f"[green]Nombre d'éléments: {len(result)}[/green]")
    elif isinstance(result, dict) and "results" in result:
        count = len(result.get("results", []))
        total = result.get("totalResultNumber", count)
        console.print(f"[green]Résultats: {count} affichés sur {total} au total[/green]")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    console.print(f"\n[dim]Exécution terminée en {end_time - start_time:.2f} secondes[/dim]") 