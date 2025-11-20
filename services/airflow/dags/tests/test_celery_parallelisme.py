from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import time
import random

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def worker_intensive_task(task_id, duration=10):
    """Tâche simulant une charge de travail"""
    print(f"🚀 Début de la tâche {task_id} sur le worker")
    print(f"Simulation de traitement pendant {duration} secondes...")
    
    # Simulation de traitement
    start_time = time.time()
    while time.time() - start_time < duration:
        # Calcul inutile pour consommer du CPU
        _ = random.random() * random.random()
        time.sleep(0.1)
    
    print(f"✅ Tâche {task_id} terminée après {duration}s")
    return f"Task {task_id} completed"

# Création dynamique de tâches parallèles
def create_parallel_tasks():
    tasks_config = [
        {'id': 'task_courte_1', 'duration': 5},
        {'id': 'task_courte_2', 'duration': 5},
        {'id': 'task_moyenne_1', 'duration': 15},
        {'id': 'task_moyenne_2', 'duration': 15},
        {'id': 'task_longue_1', 'duration': 30},
        {'id': 'task_longue_2', 'duration': 30},
    ]
    
    return tasks_config

with DAG(
    'test_celery_parallelisme',
    default_args=default_args,
    description='Test du parallélisme avec CeleryExecutor',
    schedule_interval=timedelta(hours=2),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['test', 'celery', 'parallel'],
) as dag:

    tasks_config = create_parallel_tasks()
    parallel_tasks = []
    
    # Création des tâches parallèles
    for config in tasks_config:
        task = PythonOperator(
            task_id=config['id'],
            python_callable=worker_intensive_task,
            op_kwargs={'task_id': config['id'], 'duration': config['duration']},
            pool='default_pool',
        )
        parallel_tasks.append(task)
    
    # Tâche de synthèse
    def synthesis_task(**context):
        print("🎯 Toutes les tâches parallèles sont terminées")
        print("✅ CeleryExecutor fonctionne correctement")
        return "SYNTHESIS_COMPLETE"
    
    synthesis = PythonOperator(
        task_id='synthesis',
        python_callable=synthesis_task,
        trigger_rule='all_done',
    )
    
    # Déclaration des dépendances
    parallel_tasks >> synthesis