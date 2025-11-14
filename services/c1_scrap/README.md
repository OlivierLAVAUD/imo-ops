# c1-scrap


# Prerequisite

    - uv: 
    - config.json: fichier référencant les proprietes d'acessibilité du site web, désirant être collectées, ainsi que d'autres paramètres

# Installation

## with sources
```bash

git clone https://OlivierLAVAUD/imo-ops.git 
cd immo-ops
uv sync

cd c1-scrap

uv run app.py
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

## Notes

```bash
docker-compose down
docker-compose build
```
