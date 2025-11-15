# Web Scraping to Json files (c1-scrap)

Ce projet est un scraper automatisé développé en Python pour extraire des données immobilières depuis le site IAD France. 

Utilisant Playwright pour le navigateur headless, il permet de collecter des informations détaillées sur les annonces immobilières incluant les caractéristiques du bien, les prix, les photos, les performances énergétiques (DPE/GES), les informations de copropriété et les coordonnées des conseillers.

 Le scraper intègre une gestion intelligente des cookies avec plusieurs stratégies de contournement, une extraction avancée des médias (photos, vidéos, visites virtuelles), et supporte la pagination pour collecter des données à grande échelle.
 
 Configuration via fichier JSON, export des résultats structurés et paramétrage flexible font de cet outil une architecture de solution complète pour l'analyse du marché immobilier français à partir du web.

## 🛠 Stack Technologique
### Langage & Environnement

    - Python 3.7+ - Langage principal avec support asynchrone
    - Asyncio - Pour le traitement concurrent et les opérations I/O non-bloquantes

### Web Scraping & Automatisation
    - Playwright - Navigation headless moderne avec support multi-navigateurs
    - Async API - Version asynchrone pour des performances optimales

### Traitement des Données

    - JSON - Configuration et export des données
    - Regex - Extraction et nettoyage des textes
    - Typing - Annotations de types pour la maintenabilité

### Architecture & Conception

    - Programmation Orientée Objet - Design modulaire et extensible

    - Classes Spécialisées :

        - CookieManager - Gestion intelligente des consentements
        - DataExtractor - Extraction structurée des données
        - MediaExtractor - Traitement des médias et photos
        - PerformanceEnergetiqueExtractor - Analyse DPE/GES

### Sélecteurs & Parsing

    - CSS Selectors - Localisation des éléments principaux
    - XPath - Sélecteurs avancés pour cas complexes
    - Text Processing - Nettoyage et validation des données

### Gestion de Configuration

    - Fichiers JSON - Configuration flexible du scraping
    - Variables d'environnement - Paramétrage déploiement
    - Arguments CLI - Interface en ligne de commande

### Fonctionnalités Avancées

    - Gestion d'erreurs robuste - Continuité de service
    - Pagination automatique - Collecte multi-pages
    - Délais configurables - Respect des politiques sites
    - Export structuré - Données prêtes pour analyse

# Prerequisite

    - uv: 
    - config.json: fichier référencant les proprietes d'acessibilité du site web, désirant être collectées, ainsi que 

# Installation

## with sources
```bash

git clone https://OlivierLAVAUD/imo-ops.git 
cd immo-ops
uv sync

cd c1-scrap

uv run iad_scraper.py
```

## with dockerfile


```bash
# Construire l'image
docker build -t iad-scraper .

# Exécuter avec paramètres par défaut
docker run -it --rm iad-scraper

# Exécuter avec paramètres personnalisés (Powershell)
docker run -it --rm `
  -v "${PWD}/results:/app/results" `
  -e LOCALISATION="Lyon" `
  -e MAX_BIENS=10 `
  iad-scraper

# Linux Ubuntu
docker run -it --rm \
  -v "$(pwd)/results:/app/results" \
  -e LOCALISATION="Lyon" \
  -e MAX_BIENS=10 \
  iad-scraper

```

## with docker-compose
```bash
# Avec les valeurs par défaut
docker-compose up iad-scraper

# Avec des variables personnalisées ( powershell)
$env:MAX_BIENS=10; $env:LOCALISATION="Marseille"; docker-compose up iad-scraper-custom

# vec des variables personnalisées Linux/Ubunu
MAX_BIENS=10 LOCALISATION="Marseille" docker-compose up iad-scraper-custom

```
