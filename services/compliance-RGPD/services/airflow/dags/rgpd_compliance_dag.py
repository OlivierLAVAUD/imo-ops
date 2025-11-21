# dags/rgpd_compliance_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from scripts.rgpd_compliance import RGPDCompliance
from airflow.providers.postgres.hooks.postgres import PostgresHook

def execute_rgpd_cleanup():
    """Tâche planifiée de nettoyage RGPD"""
    hook = PostgresHook(postgres_conn_id='imo_db')
    conn = hook.get_conn()
    
    rgpd = RGPDCompliance()
    
    # 1. Suppression données anciennes
    rgpd.delete_old_data(conn)
    
    # 2. Audit données sensibles
    audit_results = rgpd.audit_sensitive_data(conn)
    
    # 3. Log de conformité
    rgpd.generate_compliance_report(audit_results)
    
    conn.close()
    return "RGPD_CLEANUP_COMPLETED"

# DAG mensuel de conformité RGPD
with DAG(
    'imo_t_rgpd_compliance',
    default_args={'owner': 'airflow', 'retries': 1},
    description='Nettoyage et conformité RGPD mensuelle',
    schedule_interval='@monthly',  # Exécution mensuelle
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    rgpd_task = PythonOperator(
        task_id='execute_rgpd_cleanup',
        python_callable=execute_rgpd_cleanup,
    )