FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements en premier (meilleure utilisation du cache Docker)
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Création de la structure de dossiers
RUN mkdir -p /app/data /app/config /app/logs /app/scripts

# Copie des scripts
COPY scripts/ /app/scripts/
COPY config/ /app/config/
COPY data/ /app/data/

# Création d'un utilisateur non-root pour plus de sécurité
#RUN useradd -m -u 1000 importer && \
#    chown -R importer:importer /app

# USER importer

# Variable d'environnement pour Python
ENV PYTHONPATH=/app

# Commande par défaut
CMD ["python", "-m", "scripts.import_mongodb_agrege"]