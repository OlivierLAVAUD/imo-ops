FROM python:3.11-slim

# Installer les dépendances système nécessaires pour Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances pour Chromium
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de l'application
WORKDIR /app

# Copier les fichiers de configuration
COPY requirements.txt .
COPY config.json .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer les browsers pour Playwright
RUN playwright install chromium
RUN playwright install-deps

# Copier le code source
COPY iad_scraper.py .

# Créer un répertoire pour les résultats
RUN mkdir -p /app/results

# Variable d'environnement pour Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Commande par défaut
CMD ["python", "iad_scraper.py"]