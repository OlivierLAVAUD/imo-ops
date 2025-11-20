from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

def test_python_function():
    print("✅ Fonction Python exécutée avec succès")
    return "Python OK"

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'test_a_full_test_dag',
    default_args=default_args,
    description='DAG de test complet',
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=['test', 'debug'],
) as dag:

    start = BashOperator(
        task_id='start',
        bash_command='date && echo "Démarrage du test"'
    )

    python_test = PythonOperator(
        task_id='python_test',
        python_callable=test_python_function
    )

    bash_test = BashOperator(
        task_id='bash_test',
        bash_command='echo "Bash operator fonctionne" && sleep 2'
    )

    end = BashOperator(
        task_id='end',
        bash_command='echo "✅ Tous les tests passés avec succès!"'
    )

    start >> python_test >> bash_test >> end