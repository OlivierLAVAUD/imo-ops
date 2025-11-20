from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.dummy import DummyOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'main_orchestrator',
    default_args=default_args,
    description='Orchestrateur principal des pipelines de données',
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['orchestration', 'main'],
) as dag:

    start = DummyOperator(task_id='start')
    
    declencher_pipeline_api = TriggerDagRunOperator(
        task_id='imo_t_declencher_pipeline_api',
        trigger_dag_id='imo_t_pipeline_api',  
        wait_for_completion=False,
        poke_interval=30
    )

    declencher_pipeline_files = TriggerDagRunOperator(
        task_id='imo_t_declencher_pipeline_files',
        trigger_dag_id='imo_t_pipeline_files',  
        wait_for_completion=False,
        poke_interval=30
    )

    declencher_pipeline_web = TriggerDagRunOperator(
        task_id='imo_t_declencher_pipeline_web', 
        trigger_dag_id='imo_t_pipeline_web',  
        wait_for_completion=False,
        poke_interval=30
    )

    declencher_pipeline_db = TriggerDagRunOperator(
        task_id='imo_t_declencher_pipeline_db',
        trigger_dag_id='imo_t_pipeline_db',  
        wait_for_completion=False,
        poke_interval=30
    )

    declencher_normalisation = TriggerDagRunOperator(
        task_id='imo_t_declencher_normalisation',
        trigger_dag_id='imo_t_workers_normalization',  
        wait_for_completion=False,
        poke_interval=30
    )

    declencher_aggregation = TriggerDagRunOperator(
        task_id='imo_t_declencher_aggregation',
        trigger_dag_id='imo_t_workers_aggregation_redis',  
        wait_for_completion=False,
        poke_interval=30
    )

    end = DummyOperator(task_id='end')

    # Workflow parallèle
    start >> [
        declencher_pipeline_api,
        declencher_pipeline_files, 
        declencher_pipeline_web,
        declencher_pipeline_db

    ] >> declencher_normalisation >> declencher_aggregation >> end