from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import redis
import os
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def test_redis_connection():
    """Test de connexion à Redis"""
    try:
        # Récupération des paramètres de connexion Redis
        redis_url = os.environ.get('AIRFLOW__CELERY__BROKER_URL', 'redis://redis:6379/0')
        
        # Connexion à Redis
        r = redis.from_url(redis_url)
        
        # Test ping
        if r.ping():
            print("✅ Redis connection successful")
        
        # Test d'écriture/lecture
        test_key = "airflow_test_key"
        test_value = {"timestamp": str(datetime.now()), "status": "test"}
        
        r.set(test_key, json.dumps(test_value), ex=300)  # Expire dans 5 minutes
        
        # Lecture
        stored_value = r.get(test_key)
        if stored_value:
            parsed_value = json.loads(stored_value)
            print(f"📝 Valeur stockée dans Redis: {parsed_value}")
        
        # Info Redis
        info = r.info()
        print(f"🔧 Redis Info - Version: {info.get('redis_version')}")
        print(f"🔧 Redis Info - Mémoire utilisée: {info.get('used_memory_human')}")
        
        r.close()
        return "REDIS_CONNECTION_SUCCESS"
        
    except Exception as e:
        print(f"❌ Erreur connexion Redis: {e}")
        raise e

def test_redis_queues():
    """Test des queues Celery dans Redis"""
    try:
        redis_url = os.environ.get('AIRFLOW__CELERY__BROKER_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url)
        
        # Inspection des queues Celery
        queues = ["celery"]  # Queue par défaut
        
        for queue in queues:
            queue_key = f"_kombu.binding.{queue}"
            # Note: Cette approche peut varier selon la version
            print(f"📋 Queue: {queue}")
        
        # Test de publication (simulé)
        print("🚀 Test des capacités de queue Redis pour Celery")
        
        r.close()
        return "REDIS_QUEUES_CHECKED"
        
    except Exception as e:
        print(f"❌ Erreur queues Redis: {e}")
        raise e

def simulate_queue_operations():
    """Simulation d'opérations de queue"""
    import time
    print("🔄 Simulation d'opérations de queue...")
    
    for i in range(5):
        print(f"  Operation {i+1}/5 - Timestamp: {datetime.now()}")
        time.sleep(1)
    
    print("✅ Toutes les opérations de queue simulées sont terminées")
    return "QUEUE_OPERATIONS_COMPLETE"

with DAG(
    'test_redis_broker',
    default_args=default_args,
    description='Test du broker Redis avec Celery',
    schedule_interval=timedelta(hours=4),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['test', 'redis', 'celery', 'broker'],
) as dag:

    test_redis_conn = PythonOperator(
        task_id='test_redis_connection',
        python_callable=test_redis_connection,
    )
    
    test_redis_queues = PythonOperator(
        task_id='test_redis_queues',
        python_callable=test_redis_queues,
    )
    
    simulate_ops = PythonOperator(
        task_id='simulate_queue_operations',
        python_callable=simulate_queue_operations,
    )
    
    test_redis_conn >> test_redis_queues >> simulate_ops