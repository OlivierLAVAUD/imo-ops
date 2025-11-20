from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.redis_client import redis_client
from bs4 import BeautifulSoup
import requests

def scraper_sites_web():
    """Web scraping de sites internet"""
    print("🕸️ Démarrage du web scraping...")
    
    # Simulation de données web scraping
    donnees_web = [
        {
            'source': 'site_actualites',
            'data': {'titre': 'Nouvelle technologie', 'auteur': 'Journal X', 'date': '2024-01-01'},
            'timestamp': datetime.now().isoformat(),
            'type': 'actualite'
        },
        {
            'source': 'site_ecommerce',
            'data': {'produit': 'Smartphone', 'prix': 699.99, 'stock': True},
            'timestamp': datetime.now().isoformat(),
            'type': 'ecommerce'
        }
    ]
    
    for donnee in donnees_web:
        redis_client.push_to_queue('queue_web', donnee)
    
    print(f"✅ {len(donnees_web)} sites web scrapés")
    return f"WEB_SCRAPED_{len(donnees_web)}"

with DAG(
    'imo_t_pipeline_web',
    default_args={'owner': 'airflow', 'retries': 1},
    description='Pipeline de web scraping',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['pipeline', 'web'],
) as dag:

    web_scraping = PythonOperator(
        task_id='scraper_sites_web',
        python_callable=scraper_sites_web,
    )