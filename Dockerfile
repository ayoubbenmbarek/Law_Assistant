FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pour les modèles spaCy français
RUN python -m spacy download fr_core_news_lg

# Créer les répertoires nécessaires
RUN mkdir -p /app/data /app/logs

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 8009

# Commande par défaut pour exécuter l'application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009", "--reload"] 