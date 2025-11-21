FROM python:3.11-slim

# Installer les dépendances système nécessaires pour Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
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

# Installer UV
RUN pip install uv

WORKDIR /app

# Copier les fichiers
COPY requirements.txt config.json config-playwright.json config_out.json iad_scraper.py ./

# Installer les dépendances Python avec UV
RUN uv pip install --system -r requirements.txt

# Installer Playwright
RUN playwright install chromium
RUN playwright install-deps

# Créer les répertoires
RUN mkdir -p /app/results /app/logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Commande par défaut - juste garder le conteneur en vie
CMD ["tail", "-f", "/dev/null"]