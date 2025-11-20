from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import json
import os

def mettre_a_jour_dashboard():
    """Met à jour les données pour le dashboard"""
    try:
        hook = PostgresHook(postgres_conn_id='imo_db')
        
        # Vérifier si la table existe et contient des données
        table_check = hook.get_first("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'donnees_aggregees'
            );
        """)
        
        if not table_check or not table_check[0]:
            print("⚠️ Table donnees_aggregees n'existe pas encore")
            stats = (0, 0, None)
        else:
            # Vérifier si la table contient des données
            count_check = hook.get_first("SELECT COUNT(*) FROM donnees_aggregees;")
            
            if count_check and count_check[0] > 0:
                stats = hook.get_first("""
                    SELECT 
                        COUNT(*) as total_aggregations,
                        COALESCE(SUM((metadata->>'total_records')::int), 0) as total_records,
                        MAX(created_at) as last_aggregation
                    FROM donnees_aggregees;
                """)
            else:
                print("ℹ️ Table donnees_aggregees existe mais est vide")
                stats = (0, 0, None)
        
        dashboard_data = {
            'last_updated': datetime.now().isoformat(),
            'total_aggregations': stats[0] if stats else 0,
            'total_records_processed': stats[1] if stats else 0,
            'last_aggregation_time': str(stats[2]) if stats and stats[2] else None,
            'table_exists': bool(table_check and table_check[0]),
            'has_data': bool(stats and stats[0] > 0)
        }
        
        # Créer le dossier logs s'il n'existe pas
        logs_dir = '/opt/airflow/logs'
        os.makedirs(logs_dir, exist_ok=True)
        
        # Sauvegarder pour le dashboard
        dashboard_path = os.path.join(logs_dir, 'dashboard_stats.json')
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        print("📈 Dashboard mis à jour:", dashboard_data)
        return "DASHBOARD_UPDATED"
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du dashboard: {e}")
        # Créer un fichier d'erreur pour le dashboard
        error_data = {
            'last_updated': datetime.now().isoformat(),
            'error': str(e),
            'status': 'ERROR'
        }
        logs_dir = '/opt/airflow/logs'
        os.makedirs(logs_dir, exist_ok=True)
        with open(os.path.join(logs_dir, 'dashboard_error.json'), 'w') as f:
            json.dump(error_data, f, indent=2)
        raise

with DAG(
    'imo_t_dashboard_monitoring',
    default_args={
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=5)
    },
    description='Mise à jour des données du dashboard',
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['dashboard', 'monitoring'],
) as dag:

    update_dashboard = PythonOperator(
        task_id='mettre_a_jour_dashboard',
        python_callable=mettre_a_jour_dashboard,
    )

update_dashboard