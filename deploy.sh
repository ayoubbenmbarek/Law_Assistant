#!/bin/bash

# Script de déploiement pour l'Assistant Juridique IA en production
set -e

echo "📦 Déploiement de l'Assistant Juridique IA en production..."

# Vérifier que git est installé
if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé. Veuillez l'installer pour continuer."
    exit 1
fi

# Vérifier que docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer pour continuer."
    exit 1
fi

# Vérifier que docker-compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer pour continuer."
    exit 1
fi

# 1. Récupérer les dernières modifications
echo "🔄 Récupération des dernières modifications..."
git pull

# 2. Arrêter les conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker-compose -f docker-compose.production.yml down || true

# 3. Construire les nouvelles images
echo "🏗️ Construction des nouvelles images..."
docker-compose -f docker-compose.production.yml build --no-cache

# 4. Démarrer les conteneurs
echo "🚀 Démarrage des conteneurs en production..."
docker-compose -f docker-compose.production.yml up -d

# 5. Vérifier l'état des conteneurs
echo "🔍 Vérification de l'état des conteneurs..."
docker-compose -f docker-compose.production.yml ps

# 6. Vérifier la santé du service principal
echo "🩺 Vérification de la santé du service..."
sleep 10  # Attendre que le service démarre
curl -f http://localhost/health || echo "⚠️ Le service n'a pas répondu au healthcheck."

echo "✅ Déploiement terminé ! L'Assistant Juridique IA est accessible à l'adresse http://localhost"
echo "📝 Pour consulter les logs: docker-compose -f docker-compose.production.yml logs -f app" 