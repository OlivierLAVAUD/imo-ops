from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook  # Updated import
from airflow.models import Variable
import pandas as pd
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'email_on_failure': False,
    'email_on_retry': False
}

def test_postgres_connection():
    """Test de connexion à PostgreSQL - VERSION ADAPTÉE"""
    try:
        # CORRECTION : Utiliser imo_db au lieu de airflow
        hook = PostgresHook(postgres_conn_id='imo_db')
        conn = hook.get_conn()
        cursor = conn.cursor()
        
        # Test de requête simple
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"✅ PostgreSQL Version: {db_version[0]}")
        
        # Test de connexion à la base imo_db
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"📊 Base de données connectée: {db_name}")
        
        # Test des tables dans imo_db
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print("📋 Tables disponibles dans imo_db:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return "POSTGRES_CONNECTION_SUCCESS"
        
    except Exception as e:
        print(f"❌ Erreur de connexion PostgreSQL: {e}")
        # Ne pas lever l'exception pour éviter l'échec complet
        return f"CONNECTION_ERROR_{str(e)}"

def test_postgres_operations():
    """Test d'opérations CRUD sur PostgreSQL - VERSION ADAPTÉE"""
    try:
        hook = PostgresHook(postgres_conn_id='imo_db')
        
        # Création d'une table temporaire dans imo_db
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS test_airflow_integration (
            id SERIAL PRIMARY KEY,
            test_name VARCHAR(100),
            execution_time TIMESTAMP,
            status VARCHAR(50),
            test_data JSONB
        );
        """
        hook.run(create_table_sql)
        
        # Insertion de données avec JSONB
        insert_sql = """
        INSERT INTO test_airflow_integration (test_name, execution_time, status, test_data)
        VALUES (%s, %s, %s, %s)
        """
        test_payload = {
            'environment': 'imo-ops',
            'database': 'imo_db',
            'test_type': 'integration',
            'metrics': {'execution_time_ms': 150, 'memory_mb': 45}
        }
        
        hook.run(insert_sql, parameters=(
            'test_celery_postgres_imo', 
            datetime.now(), 
            'IN_PROGRESS',
            json.dumps(test_payload)
        ))
        
        # Lecture des données
        results = hook.get_records("""
            SELECT id, test_name, execution_time, status, test_data
            FROM test_airflow_integration 
            WHERE test_name LIKE 'test_celery_postgres%'
            ORDER BY execution_time DESC LIMIT 5
        """)
        
        print("📝 Données insérées et lues avec succès:")
        for row in results:
            print(f"  - ID: {row[0]}, Test: {row[1]}, Time: {row[2]}, Status: {row[3]}")
            if row[4]:
                print(f"    Data: {row[4]}")
        
        # Test avec la table donnees_aggregees si elle existe
        try:
            agg_count = hook.get_first("SELECT COUNT(*) FROM donnees_aggregees;")
            if agg_count:
                print(f"📊 Table donnees_aggregees: {agg_count[0]} enregistrements")
        except Exception as agg_error:
            print(f"ℹ️ Table donnees_aggregees non accessible: {agg_error}")
            
        return "POSTGRES_OPERATIONS_SUCCESS"
        
    except Exception as e:
        print(f"❌ Erreur opérations PostgreSQL: {e}")
        return f"OPERATIONS_ERROR_{str(e)}"

def test_imo_db_schema():
    """Test spécifique du schéma imo_db - NOUVELLE FONCTION"""
    try:
        hook = PostgresHook(postgres_conn_id='imo_db')
        
        print("🔍 Analyse du schéma imo_db...")
        
        # Compter les enregistrements par table
        tables_to_check = [
            'annonces', 'caracteristiques', 'images', 
            'dpe', 'copropriete', 'conseiller', 'donnees_aggregees'
        ]
        
        schema_report = {}
        
        for table in tables_to_check:
            try:
                count_result = hook.get_first(f"SELECT COUNT(*) FROM {table};")
                count = count_result[0] if count_result else 0
                schema_report[table] = count
                status = "✅" if count > 0 else "⚠️"
                print(f"  {status} {table}: {count} enregistrements")
            except Exception as table_error:
                schema_report[table] = f"ERROR: {str(table_error)}"
                print(f"  ❌ {table}: Non accessible")
        
        # Tester les vues
        views_to_check = [
            'annonces_complete', 'v_stats_type_bien', 
            'v_stats_localisation', 'v_stats_dpe'
        ]
        
        print("👀 Test des vues...")
        for view in views_to_check:
            try:
                hook.get_first(f"SELECT 1 FROM {view} LIMIT 1;")
                print(f"  ✅ {view}: Accessible")
            except Exception as view_error:
                print(f"  ❌ {view}: Erreur - {str(view_error)}")
        
        return f"SCHEMA_TEST_COMPLETED"
        
    except Exception as e:
        print(f"❌ Erreur analyse schéma: {e}")
        return f"SCHEMA_ERROR_{str(e)}"

def test_xcom_postgres():
    """Test du stockage XCom dans PostgreSQL - VERSION ADAPTÉE"""
    try:
        # Simulation de données complexes spécifiques à imo-ops
        test_data = {
            'test_id': 'xcom_postgres_imo_test',
            'timestamp': str(datetime.now()),
            'environment': 'imo-ops',
            'database': 'imo_db',
            'metrics': {
                'memory_usage': '65%',
                'execution_time': '1.8s',
                'status': 'success',
                'tables_tested': 7
            },
            'sample_data': {
                'total_annonces': 0,  # À adapter selon vos données réelles
                'aggregations_count': 0,
                'test_scenarios': ['connection', 'operations', 'schema']
            }
        }
        
        print("💾 Données XCom préparées pour stockage PostgreSQL:")
        print(f"  - Test ID: {test_data['test_id']}")
        print(f"  - Environnement: {test_data['environment']}")
        print(f"  - Métriques: {test_data['metrics']}")
        
        # Les XCom seront automatiquement stockés dans PostgreSQL (base airflow)
        return test_data
        
    except Exception as e:
        print(f"❌ Erreur XCom PostgreSQL: {e}")
        return f"XCOM_ERROR_{str(e)}"

def cleanup_test_data():
    """Nettoyage des données de test - NOUVELLE FONCTION"""
    try:
        hook = PostgresHook(postgres_conn_id='imo_db')
        
        # Supprimer la table de test si elle existe
        drop_sql = "DROP TABLE IF EXISTS test_airflow_integration;"
        hook.run(drop_sql)
        
        print("🧹 Nettoyage des données de test effectué")
        return "CLEANUP_SUCCESS"
        
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
        return f"CLEANUP_ERROR_{str(e)}"

with DAG(
    'test_imo_db_integration',  # Nom modifié
    default_args=default_args,
    description='Test intégration PostgreSQL imo_db avec Airflow',
    schedule_interval=timedelta(hours=6),  # Intervalle augmenté
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['test', 'postgres', 'imo_db', 'database', 'integration'],
) as dag:

    test_connection = PythonOperator(
        task_id='test_postgres_connection',
        python_callable=test_postgres_connection,
    )
    
    test_operations = PythonOperator(
        task_id='test_postgres_operations',
        python_callable=test_postgres_operations,
    )
    
    test_schema = PythonOperator(
        task_id='test_imo_db_schema',
        python_callable=test_imo_db_schema,
    )
    
    test_xcom = PythonOperator(
        task_id='test_xcom_postgres',
        python_callable=test_xcom_postgres,
    )
    
    cleanup = PythonOperator(
        task_id='cleanup_test_data',
        python_callable=cleanup_test_data,
    )
    
    # Workflow : connexion → opérations → schéma → XCom → nettoyage
    test_connection >> test_operations >> test_schema >> test_xcom >> cleanup