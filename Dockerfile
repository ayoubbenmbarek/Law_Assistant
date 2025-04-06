FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Stratégie d'installation modifiée pour éviter les conflits
# 1. D'abord installer NumPy 2.2.4
RUN pip install --no-cache-dir --upgrade pip && \
    pip cache purge && \
    pip install --no-cache-dir numpy==2.2.4

# 2. Installer les dépendances scientifiques qui sont compatibles avec NumPy 2.x
RUN pip install --no-cache-dir scipy>=1.11.0 scikit-learn>=1.3.0 pandas>=2.0.0 && \
    pip install --no-cache-dir huggingface_hub==0.30.1 filelock==3.18.0 fsspec==2025.3.2 certifi==2025.1.31 charset-normalizer==3.4.1 && \
    pip install --no-cache-dir langchain>=0.1.0 langchain-community>=0.0.16

# 3. Installer les autres packages de manière sélective pour éviter les conflits
RUN grep -v "numpy\|langchain\|pgvector\|qdrant-client\|transformers\|sentence-transformers" requirements.txt > filtered_requirements.txt && \
    pip install --no-cache-dir -r filtered_requirements.txt

# 4. Installer individuellement les packages problématiques avec leurs dépendances
RUN pip install --no-cache-dir pgvector==0.2.0 && \
    pip install --no-cache-dir qdrant-client==1.5.4 && \
    pip install --no-cache-dir transformers==4.41.0 && \
    pip install --no-cache-dir sentence-transformers==2.3.1 && \
    pip install --no-cache-dir "spacy>=3.6.0" && \
    python -m spacy download fr_core_news_lg

# 5. Vérifier et réinstaller numpy pour être sûr
RUN pip uninstall -y numpy && \
    pip install --no-cache-dir numpy==2.2.4

# 6. Assurer la compatibilité de passlib avec bcrypt moderne
RUN pip install --no-cache-dir "passlib[bcrypt]" && \
    pip install --no-cache-dir bcrypt==4.3.0

# Créer un script de patch pour passlib/bcrypt
RUN echo '#!/usr/bin/env python3\n\
import sys\n\
import os\n\
\n\
# Trouver le chemin de passlib\n\
import passlib\n\
passlib_path = os.path.dirname(passlib.__file__)\n\
bcrypt_path = os.path.join(passlib_path, "handlers", "bcrypt.py")\n\
\n\
# Lire le fichier\n\
with open(bcrypt_path, "r") as f:\n\
    content = f.read()\n\
\n\
# Modifier le code pour supporter bcrypt moderne\n\
if "version = _bcrypt.__about__.__version__" in content:\n\
    content = content.replace(\n\
        "version = _bcrypt.__about__.__version__",\n\
        "try:\\n                version = _bcrypt.__about__.__version__\\n            except AttributeError:\\n                version = _bcrypt.__version__"\n\
    )\n\
\n\
    # Écrire le fichier modifié\n\
    with open(bcrypt_path, "w") as f:\n\
        f.write(content)\n\
    print("Passlib bcrypt patch appliqué avec succès.")\n\
' > /app/patch_passlib.py && chmod +x /app/patch_passlib.py

# Créer les répertoires nécessaires
RUN mkdir -p /app/data /app/logs

# Copier le code source
COPY . .

# Appliquer le patch à passlib
RUN python /app/patch_passlib.py

# Exposer le port
EXPOSE 8009

# Commande par défaut pour exécuter l'application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009", "--reload"] 