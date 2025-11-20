from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.redis_client import redis_client
import json
import logging

def normaliser_donnees_api():
    """Normalisation des données API - VERSION REDIS ACTIF"""
    print("🔄 Normalisation des données API...")
    
    donnees_normalisees = []
    max_records = 500  # Limite de sécurité
    
    try:
        queue_length = redis_client.get_queue_length('queue_api')
        print(f"🔴 Queue API: {queue_length} éléments")
        
        records_processed = 0
        while redis_client.get_queue_length('queue_api') > 0 and records_processed < max_records:
            donnee = redis_client.pop_from_queue('queue_api')
            if donnee:
                # Conversion et validation des données
                if isinstance(donnee, str):
                    try:
                        donnee = json.loads(donnee)
                    except json.JSONDecodeError:
                        print(f"⚠️ Donnée API non JSON ignorée: {donnee[:100]}...")
                        continue
                
                # Normalisation standardisée
                donnee_normalisee = {
                    'source': 'api',
                    'data': donnee,
                    'normalized': True,
                    'normalized_timestamp': datetime.now().isoformat(),
                    'format': 'standard_v1',
                    'processing_step': 'normalization'
                }
                
                donnees_normalisees.append(donnee_normalisee)
                redis_client.push_to_queue('queue_normalized', json.dumps(donnee_normalisee))
                records_processed += 1
        
        print(f"✅ {len(donnees_normalisees)} données API normalisées")
        return f"API_NORMALIZED_{len(donnees_normalisees)}"
        
    except Exception as e:
        print(f"❌ Erreur normalisation API: {e}")
        return f"API_ERROR_{str(e)}"

def normaliser_donnees_fichiers():
    """Normalisation des données fichiers - VERSION REDIS ACTIF"""
    print("🔄 Normalisation des données fichiers...")
    
    donnees_normalisees = []
    max_records = 500
    
    try:
        queue_length = redis_client.get_queue_length('queue_file')
        print(f"🔴 Queue Fichiers: {queue_length} éléments")
        
        records_processed = 0
        while redis_client.get_queue_length('queue_file') > 0 and records_processed < max_records:
            donnee = redis_client.pop_from_queue('queue_file')
            if donnee:
                if isinstance(donnee, str):
                    try:
                        donnee = json.loads(donnee)
                    except json.JSONDecodeError:
                        print(f"⚠️ Donnée fichier non JSON ignorée: {donnee[:100]}...")
                        continue
                
                donnee_normalisee = {
                    'source': 'file',
                    'data': donnee,
                    'normalized': True,
                    'normalized_timestamp': datetime.now().isoformat(),
                    'format': 'standard_v1',
                    'processing_step': 'normalization'
                }
                
                donnees_normalisees.append(donnee_normalisee)
                redis_client.push_to_queue('queue_normalized', json.dumps(donnee_normalisee))
                records_processed += 1
        
        print(f"✅ {len(donnees_normalisees)} données fichiers normalisées")
        return f"FILES_NORMALIZED_{len(donnees_normalisees)}"
        
    except Exception as e:
        print(f"❌ Erreur normalisation fichiers: {e}")
        return f"FILES_ERROR_{str(e)}"

def normaliser_donnees_web():
    """Normalisation des données web scraping - VERSION REDIS ACTIF"""
    print("🔄 Normalisation des données web...")
    
    donnees_normalisees = []
    max_records = 500
    
    try:
        queue_length = redis_client.get_queue_length('queue_web')
        print(f"🔴 Queue Web: {queue_length} éléments")
        
        records_processed = 0
        while redis_client.get_queue_length('queue_web') > 0 and records_processed < max_records:
            donnee = redis_client.pop_from_queue('queue_web')
            if donnee:
                if isinstance(donnee, str):
                    try:
                        donnee = json.loads(donnee)
                    except json.JSONDecodeError:
                        print(f"⚠️ Donnée web non JSON ignorée: {donnee[:100]}...")
                        continue
                
                donnee_normalisee = {
                    'source': 'web',
                    'data': donnee,
                    'normalized': True,
                    'normalized_timestamp': datetime.now().isoformat(),
                    'format': 'standard_v1',
                    'processing_step': 'normalization'
                }
                
                donnees_normalisees.append(donnee_normalisee)
                redis_client.push_to_queue('queue_normalized', json.dumps(donnee_normalisee))
                records_processed += 1
        
        print(f"✅ {len(donnees_normalisees)} données web normalisées")
        return f"WEB_NORMALIZED_{len(donnees_normalisees)}"
        
    except Exception as e:
        print(f"❌ Erreur normalisation web: {e}")
        return f"WEB_ERROR_{str(e)}"

def normaliser_donnees_db():
    """Normalisation des données bases de données - VERSION REDIS ACTIF"""
    print("🔄 Normalisation des données BD...")
    
    donnees_normalisees = []
    max_records = 500
    
    try:
        queue_length = redis_client.get_queue_length('queue_db')
        print(f"🔴 Queue BD: {queue_length} éléments")
        
        records_processed = 0
        while redis_client.get_queue_length('queue_db') > 0 and records_processed < max_records:
            donnee = redis_client.pop_from_queue('queue_db')
            if donnee:
                if isinstance(donnee, str):
                    try:
                        donnee = json.loads(donnee)
                    except json.JSONDecodeError:
                        print(f"⚠️ Donnée BD non JSON ignorée: {donnee[:100]}...")
                        continue
                
                donnee_normalisee = {
                    'source': 'database',
                    'data': donnee,
                    'normalized': True,
                    'normalized_timestamp': datetime.now().isoformat(),
                    'format': 'standard_v1',
                    'processing_step': 'normalization'
                }
                
                donnees_normalisees.append(donnee_normalisee)
                redis_client.push_to_queue('queue_normalized', json.dumps(donnee_normalisee))
                records_processed += 1
        
        print(f"✅ {len(donnees_normalisees)} données BD normalisées")
        return f"DB_NORMALIZED_{len(donnees_normalisees)}"
        
    except Exception as e:
        print(f"❌ Erreur normalisation BD: {e}")
        return f"DB_ERROR_{str(e)}"

def verifier_queues_normalisation():
    """Vérification des queues avant/après normalisation"""
    print("🔍 ÉTAT DES QUEUES DE NORMALISATION:")
    
    try:
        queues = {
            'API': 'queue_api',
            'Fichiers': 'queue_file',
            'Web': 'queue_web',
            'BD': 'queue_db',
            'Normalisées': 'queue_normalized'
        }
        
        for nom, queue in queues.items():
            length = redis_client.get_queue_length(queue)
            status = "✅ VIDE" if length == 0 else f"🔴 {length}"
            print(f"   {nom} ({queue}): {status}")
            
            # Aperçu pour les queues d'entrée non vides
            if queue != 'queue_normalized' and length > 0:
                try:
                    preview = redis_client.peek_queue(queue)
                    if preview:
                        preview_str = str(preview)[:80] + "..." if len(str(preview)) > 80 else str(preview)
                        print(f"      👀 Aperçu: {preview_str}")
                except:
                    pass
        
        return "QUEUES_CHECKED"
        
    except Exception as e:
        print(f"❌ Erreur vérification queues: {e}")
        return f"QUEUES_ERROR_{str(e)}"

with DAG(
    'imo_t_workers_normalization',
    default_args={
        'owner': 'airflow', 
        'retries': 2,
        'retry_delay': timedelta(minutes=3)
    },
    description='Workers de normalisation des données - REDIS ACTIF',
    schedule_interval=timedelta(minutes=15),  # Toutes les 15 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['workers', 'normalization', 'redis'],
) as dag:

    check_queues = PythonOperator(
        task_id='verifier_queues_normalisation',
        python_callable=verifier_queues_normalisation,
    )

    norm_api = PythonOperator(
        task_id='normaliser_donnees_api',
        python_callable=normaliser_donnees_api,
    )

    norm_files = PythonOperator(
        task_id='normaliser_donnees_fichiers',
        python_callable=normaliser_donnees_fichiers,
    )

    norm_web = PythonOperator(
        task_id='normaliser_donnees_web',
        python_callable=normaliser_donnees_web,
    )

    norm_db = PythonOperator(
        task_id='normaliser_donnees_db',
        python_callable=normaliser_donnees_db,
    )

    # Workflow: vérification → normalisation en parallèle
    check_queues >> [norm_api, norm_files, norm_web, norm_db]