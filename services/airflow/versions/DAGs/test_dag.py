from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta  # Importation de timedelta

# Fonction simple qui sera exécutée par la tâche
def print_hello():
    print("Hello, Airflow!")

# Définition du DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),  # Utilisation de timedelta après importation
}

with DAG(
    'test_dag',  # Nom du DAG
    default_args=default_args,
    description='A simple test DAG',
    schedule_interval='@once',  # Exécution une seule fois
    start_date=datetime(2025, 3, 13),  # Date de début du DAG
    catchup=False,  # Ne pas exécuter les tâches passées
) as dag:

    # Définir une tâche qui exécute la fonction print_hello
    task1 = PythonOperator(
        task_id='print_hello_task',  # ID de la tâche
        python_callable=print_hello,  # Fonction Python à exécuter
    )

    # La tâche `print_hello_task` est l'unique tâche du DAG
    task1
