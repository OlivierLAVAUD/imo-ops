from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.redis_client import redis_client
import requests
import json

def collecter_donnees_api():
    """Collecte de données depuis des APIs externes"""
    print("🌐 Démarrage de la collecte API...")
    
    # Simulation de données API
    donnees_api = [
        {
            'source': 'api_meteo',
            'data': {'temperature': 22, 'humidite': 65, 'ville': 'Paris'},
            'timestamp': datetime.now().isoformat(),
            'type': 'meteo'
        },
        {
            'source': 'api_finance', 
            'data': {'prix': 150.50, 'devise': 'EUR', 'produit': 'Action X'},
            'timestamp': datetime.now().isoformat(),
            'type': 'finance'
        }
    ]
    
    # Envoi vers Redis
    for donnee in donnees_api:
        redis_client.push_to_queue('queue_api', donnee)
    
    print(f"✅ {len(donnees_api)} données API collectées")
    return f"API_COLLECTED_{len(donnees_api)}"

with DAG(
    'imo_t_pipeline_api',
    default_args={'owner': 'airflow', 'retries': 1},
    description='Pipeline de collecte de données API',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['pipeline', 'api'],
) as dag:

    collect_api = PythonOperator(
        task_id='collecter_donnees_api',
        python_callable=collecter_donnees_api,
    )