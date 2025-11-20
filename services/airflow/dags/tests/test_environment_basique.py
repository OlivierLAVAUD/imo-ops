from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def test_imports():
    """Test des imports des bibliothèques courantes"""
    try:
        import pandas as pd
        import requests
        import psycopg2
        print("✓ Tous les imports réussis")
        return "SUCCESS"
    except ImportError as e:
        print(f"✗ Erreur d'import: {e}")
        raise e

def test_environment():
    """Test des variables d'environnement et configuration"""
    import os
    print(f"Environment: {os.environ.get('AIRFLOW__CORE__EXECUTOR', 'Non défini')}")
    print(f"Database: {os.environ.get('AIRFLOW__DATABASE__SQL_ALCHEMY_CONN', 'Non défini').split('@')[1] if 'AIRFLOW__DATABASE__SQL_ALCHEMY_CONN' in os.environ else 'Non défini'}")
    return "ENVIRONMENT_CHECKED"

with DAG(
    'test_environment_basique',
    default_args=default_args,
    description='DAG de test pour environnement de base',
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['test', 'environment'],
) as dag:

    start = DummyOperator(task_id='start')
    
    test_imports_task = PythonOperator(
        task_id='test_imports',
        python_callable=test_imports,
    )
    
    test_env_task = PythonOperator(
        task_id='test_environment',
        python_callable=test_environment,
    )
    
    bash_test = BashOperator(
        task_id='bash_operation',
        bash_command='echo "Hello Airflow 2.7.3 - Date: $(date)" && sleep 5',
    )
    
    end = DummyOperator(task_id='end')

    start >> test_imports_task >> test_env_task >> bash_test >> end