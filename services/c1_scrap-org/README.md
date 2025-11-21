# Web Scraping to Json files (c1-scrap)

Ce projet est un scraper automatisé développé en Python pour extraire des données immobilières depuis le site IAD France. 

Utilisant Playwright pour le navigateur headless, il permet de collecter des informations détaillées sur les annonces immobilières incluant les caractéristiques du bien, les prix, les photos, les performances énergétiques (DPE/GES), les informations de copropriété et les coordonnées des conseillers.

 Le scraper intègre une gestion des cookies , une extraction avancée des médias (photos, vidéos, visites virtuelles), et supporte la pagination pour collecter des données à grande échelle.
 
 Configuration via fichier JSON, export des résultats structurés et paramétrage flexible font de cet outil une architecture de solution complète pour l'analyse du marché immobilier français à partir du web.

## 🛠 Stack Technologique
### Langage & Environnement

    - Python 3.7+
    - Asyncio - Pour le traitement concurrent et les opérations I/O non-bloquantes

### Web Scraping & Automatisation
    - Playwright - Navigation headless moderne avec support multi-navigateurs
    - Async API - Version asynchrone pour des performances optimales

### Traitement des Données

    - JSON - Configuration et export des données
    - Regex - Extraction et nettoyage des textes
    - Typing - Annotations de types pour la maintenabilité

### Architecture & Conception

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
    - Gestion d'erreurs robuste - Continuité de service
    - Pagination automatique - Collecte multi-pages
    - Délais configurables - Respect des politiques sites
    - Export structuré - Données prêtes pour analyse

# Configuration

    - config.json: fichier référencant les proprietes d'acessibilité du site web, désirant être collectées
    - config-playwright.json: détermine la structure de sortie du json en sortie:

# Usage

## with sources
```bash
# scrape avec les valeurs par defaut
uv run iad_scraper.py

# → Scrape 20 biens à Bordeaux sur 5 pages maximum
uv run iad_scraper.py --localisation "Bordeaux" --max-biens 20 --max-pages 5
```

## with dockerfile

```bash
# 1. Demarrer le service de scraping (le conteneur reste démarré et actif)
docker-compose up -d

# 2. Lancer la requete de scraping
docker exec iad-scraper python iad_scraper.py --localisation "Tours" --max-bien 1
docker exec iad-scraper python iad_scraper.py --localisation "Montpellier" --transaction louer --max-biens 1
docker exec iad-scraper python iad_scraper.py --localisation "Lyon" --transaction louer --max-biens 1
docker exec iad-scraper python iad_scraper.py --localisation "Montpellier" --transaction acheter --bien prestige --max-biens 1

#Note:
#usage: iad_scraper.py [-h] [--localisation LOCALISATION]
                      [--transaction {acheter,louer,vendre}]
                      [--bien {ancien,neuf,prestige,international,terrain,entreprises_commerces,immeuble}]
                      [--max-biens MAX_BIENS] [--max-pages MAX_PAGES]


# 3. Voir les fichiers dans le conteneur
docker exec iad-scraper ls -la /app/results/

# 4. Copier tout le répertoire de resultats produits
docker cp iad-scraper:/app/results/ ./downloads/

# 5. Copier un fichier spécifique du conteneur vers votre machine
docker cp iad-scraper:/app/results/mon_fichier.json ./downloads/

# 6. Arrêter & supprimer le conteneur, images, .. associées
docker-compose --profile scraping down -v --rmi all

```

docker exec -it iad-scraper /bin/bash
python iad_scraper.py --localisation "Tours" --max-bien 1


docker exec -it iad-scraper python iad_scraper.py --localisation "Tours" --max-bien 1