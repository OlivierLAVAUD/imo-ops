from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from shared.redis_client import redis_client

def extraire_bases_donnees():
    """Extraction depuis bases de données SQL/NoSQL"""
    print("🗃️ Démarrage de l'extraction des bases de données...")
    
    # Simulation de données BD
    donnees_bd = [
        {
            'source': 'postgres_utilisateurs',
            'data': {'id': 1, 'nom': 'Jean Dupont', 'email': 'jean@example.com'},
            'timestamp': datetime.now().isoformat(),
            'type': 'utilisateur'
        },
        {
            'source': 'mongodb_logs',
            'data': {'action': 'connexion', 'user_id': 123, 'status': 'success'},
            'timestamp': datetime.now().isoformat(),
            'type': 'log'
        }
    ]
    
    for donnee in donnees_bd:
        redis_client.push_to_queue('queue_db', donnee)
    
    print(f"✅ {len(donnees_bd)} bases de données extraites")
    return f"DB_EXTRACTED_{len(donnees_bd)}"

with DAG(
    'imo_t_pipeline_db',
    default_args={'owner': 'airflow', 'retries': 1},
    description='Pipeline extraction bases de données',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['pipeline', 'database'],
) as dag:

    extract_db = PythonOperator(
        task_id='extraire_bases_donnees',
        python_callable=extraire_bases_donnees,
    )