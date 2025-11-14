from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import redis

def test_redis_connection():
    """Test la connexion Redis depuis une tâche Airflow"""
    try:
        r = redis.Redis(
            host='redis',
            port=6379,
            password='redis_password',
            db=0
        )
        
        # Test de connexion
        if r.ping():
            print("✅ Redis connecté depuis tâche Airflow")
            
            # Test de performance
            import time
            start = time.time()
            
            # Opérations de test
            for i in range(50):
                r.set(f"airflow_test_{i}", f"value_{i}")
                r.get(f"airflow_test_{i}")
                
            duration = time.time() - start
            print(f"✅ 50 opérations Redis en {duration:.2f} secondes")
            
            # Nettoyage
            for i in range(50):
                r.delete(f"airflow_test_{i}")
                
        else:
            print("❌ Redis ne répond pas")
            
    except Exception as e:
        print(f"❌ Erreur Redis: {e}")

with DAG(
    'test_redis_connection',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['test']
) as dag:

    test_task = PythonOperator(
        task_id='test_redis_connection',
        python_callable=test_redis_connection
    )