# Tester depuis le conteneur où l'encodage est correctement configuré
docker-compose exec airflow-worker python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='postgres',
        database='airflow',
        user='airflow', 
        password='airflow'
    )
    cursor = conn.cursor()
    
    cursor.execute('SELECT version()')
    print('Version:', cursor.fetchone()[0])
    
    cursor.execute('SELECT COUNT(*) FROM dag')
    print('DAGs:', cursor.fetchone()[0])
    
    cursor.execute('SELECT COUNT(*) FROM dag_run') 
    print('DAG runs:', cursor.fetchone()[0])
    
    cursor.close()
    conn.close()
    print('✅ Tests réussis depuis Docker')
    
except Exception as e:
    print('❌ Erreur:', e)
    exit(1)
"