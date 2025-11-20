from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def test_function():
    print("✅ DAG test exécuté avec succès!")
    return "Success"

with DAG(
    'a_test_dag_new',
    default_args=default_args,
    description='DAG de test new',
    schedule_interval=timedelta(minutes=10),
    catchup=False,
    tags=['test'],
) as dag:

    t1 = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    t2 = PythonOperator(
        task_id='test_task',
        python_callable=test_function,
    )

    t1 >> t2