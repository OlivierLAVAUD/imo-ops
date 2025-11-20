# test_postgres_fixed.py
import psycopg2
import sys
import traceback

def test_postgres_connection():
    try:
        # Paramètres de connexion avec encodage forcé
        conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'airflow',
            'user': 'airflow',
            'password': 'airflow',
            'client_encoding': 'utf8'
        }
        
        print(f"🔗 Connexion à PostgreSQL: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        
        # Établir la connexion avec gestion d'encodage
        conn = psycopg2.connect(**conn_params)
        
        # Forcer l'encodage UTF-8
        conn.set_client_encoding('UTF8')
        
        cursor = conn.cursor()
        print("✅ Connexion PostgreSQL établie!")
        
        # Test simple d'abord
        cursor.execute('SELECT 1 as test')
        simple_test = cursor.fetchone()
        print(f'✅ Test basique réussi: {simple_test[0]}')
        
        # Test version PostgreSQL (peut contenir des caractères spéciaux)
        cursor.execute('SELECT version()')
        version = cursor.fetchone()
        version_str = str(version[0]).encode('utf-8', errors='replace').decode('utf-8')
        print(f'📋 Version PostgreSQL: {version_str}')
        
        # Test COUNT sans afficher de données potentiellement problématiques
        cursor.execute('SELECT COUNT(*) FROM dag')
        dag_count = cursor.fetchone()
        print(f'📊 Nombre de DAGs: {dag_count[0]}')
        
        cursor.execute('SELECT COUNT(*) FROM dag_run')
        run_count = cursor.fetchone()
        print(f'🎯 Nombre de DAG runs: {run_count[0]}')
        
        # Test informations basiques
        cursor.execute("SELECT current_database(), current_user")
        db_info = cursor.fetchone()
        print(f'🗃️ Base: {db_info[0]}, Utilisateur: {db_info[1]}')
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Tous les tests PostgreSQL ont réussi!")
        return True
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        print(f'🔍 Détails: {traceback.format_exc()}')
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)