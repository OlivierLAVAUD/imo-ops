from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator

# Fonctions pour les tâches
def tache_1():
    print("Exécution de la tâche 1")

def tache_2():
    print("Exécution de la tâche 2")

def tache_3():
    print("Exécution de la tâche 3 (après que les tâches 1 et 2 soient terminées)")

# Définition du DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'taches_paralleles_et_sequentielles',
    default_args=default_args,
    description='DAG avec deux tâches parallèles suivies d\'une tâche séquentielle',
    schedule_interval=None,
    catchup=False,
)

# Définition des tâches
tache_1 = PythonOperator(
    task_id='tache_1',
    python_callable=tache_1,
    dag=dag,
)

tache_2 = PythonOperator(
    task_id='tache_2',
    python_callable=tache_2,
    dag=dag,
)

tache_3 = PythonOperator(
    task_id='tache_3',
    python_callable=tache_3,
    dag=dag,
)

# Définition des dépendances
[tache_1, tache_2] >> tache_3
