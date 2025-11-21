# Scraper IAD France avec Scrapy + Playwright

Scraper professionnel pour extraire les annonces immobilières de IAD France.

## Installation

```bash
pip install -r requirements.txt
playwright install

# Scraping de base
scrapy crawl iad_france -a localisation="Paris" -a max_biens=50

# Avec paramètres avancés
scrapy crawl iad_france \
  -a localisation="Lyon" \
  -a max_biens=100 \
  -s CONCURRENT_REQUESTS=1 \
  -s DOWNLOAD_DELAY=3
  ```

  ## Utilisation

  ```bash
uv run scrapy crawl iad_france -a localisation="Paris" -a max_biens=10 -a max_pages=3

# Avec le script Python
uv run run.py "Lyon" 100

# Directement avec Scrapy
scrapy crawl iad_france -a localisation="Bordeaux" -a max_biens=200

# Avec logging avancé
scrapy crawl iad_france -a localisation="Paris" -a max_biens=50 --logfile=scrapy.log

# Pour le débogage
scrapy crawl iad_france -a localisation="Test" -a max_biens=5 --loglevel=DEBUG


scrapy crawl iad_france -a localisation="Montpellier" -a max_biens=1

# Ou avec settings personnalisés
scrapy crawl iad_france -a localisation="Paris" -a max_biens=50 -s CONCURRENT_REQUESTS=1 -s DOWNLOAD_DELAY=2

  ```