# test_postgres.py
import sys
import time

def test_postgres_connection():
    try:
        print("🔗 Test de connexion à PostgreSQL...")
        
        # Essayer d'importer psycopg2
        try:
            import psycopg2
            print("✅ Module psycopg2 importé")
        except ImportError:
            print("❌ psycopg2 non disponible")
            return False

        # Test connexion de base
        try:
            conn = psycopg2.connect(
                host='postgres',
                port=5432,
                database='airflow',
                user='airflow',
                password='airflow',
                connect_timeout=10
            )
            cursor = conn.cursor()
            cursor.execute('SELECT version()')
            version = cursor.fetchone()
            print(f'✅ PostgreSQL: {version[0].split(",")[0]}')
            
            # Vérifier les bases
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            dbs = [db[0] for db in cursor.fetchall()]
            print(f'🗃️ Bases: {", ".join(dbs)}')
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f'❌ Erreur connexion: {e}')
            return False
            
    except Exception as e:
        print(f'❌ Erreur générale: {e}')
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)