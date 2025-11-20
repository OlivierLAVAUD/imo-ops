from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from shared.redis_client import redis_client
import json
import logging

def agreger_donnees():
    """Agrégation de toutes les données normalisées - VERSION REDIS ACTIF"""
    print("📊 Démarrage de l'agrégation des données depuis Redis...")
    
    donnees_aggregees = {
        'metadata': {
            'aggregation_timestamp': datetime.now().isoformat(),
            'total_records': 0,
            'sources': [],
            'aggregation_type': 'redis_auto',
            'environment': 'imo-ops',
            'redis_queue': 'queue_normalized'
        }
    }
    
    # COLLECTE RÉELLE DEPUIS REDIS
    try:
        queue_length = redis_client.get_queue_length('queue_normalized')
        print(f"🔴 Redis - Éléments dans queue_normalized: {queue_length}")
        
        records_processed = 0
        max_records = 1000  # Limite pour éviter les boucles infinies
        donnees_collectees = []
        
        while redis_client.get_queue_length('queue_normalized') > 0 and records_processed < max_records:
            donnee = redis_client.pop_from_queue('queue_normalized')
            if donnee:
                # Conversion des données si nécessaire
                if isinstance(donnee, str):
                    try:
                        donnee = json.loads(donnee)
                    except json.JSONDecodeError:
                        print(f"⚠️ Donnée non JSON ignorée: {donnee[:100]}...")
                        continue
                
                donnees_collectees.append(donnee)
                records_processed += 1
                
                # Extraire la source
                source = donnee.get('source', 'unknown')
                if source not in donnees_aggregees['metadata']['sources']:
                    donnees_aggregees['metadata']['sources'].append(source)
        
        donnees_aggregees['metadata']['total_records'] = len(donnees_collectees)
        donnees_aggregees['metadata']['redis_initial_count'] = queue_length
        donnees_aggregees['metadata']['records_processed'] = records_processed
        
        print(f"✅ {len(donnees_collectees)} données agrégées depuis Redis")
        print(f"🌐 Sources détectées: {donnees_aggregees['metadata']['sources']}")
        
        # Vérifier s'il reste des données
        remaining = redis_client.get_queue_length('queue_normalized')
        if remaining > 0:
            print(f"⚠️  Il reste {remaining} éléments dans la queue - limite atteinte")
        
    except Exception as e:
        print(f"❌ Erreur collecte Redis: {e}")
        donnees_aggregees['metadata']['error'] = str(e)
        donnees_aggregees['metadata']['fallback_mode'] = True
    
    # Sauvegarde dans PostgreSQL
    sauvegarder_postgresql(donnees_aggregees)
    
    return f"DATA_AGGREGATED_{donnees_aggregees['metadata']['total_records']}"

def sauvegarder_postgresql(donnees_aggregees):
    """Sauvegarde des données agrégées dans PostgreSQL"""
    try:
        hook = PostgresHook(postgres_conn_id='imo_db')
        
        # Vérifier si la table existe
        table_exists = hook.get_first("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'donnees_aggregees'
            );
        """)
        
        if not table_exists or not table_exists[0]:
            print("❌ Table 'donnees_aggregees' n'existe pas dans imo_db")
            raise Exception("Table donnees_aggregees non trouvée")
        
        # Insertion des données
        insert_sql = """
        INSERT INTO donnees_aggregees (metadata, created_at)
        VALUES (%s, %s)
        RETURNING id;
        """
        
        result = hook.get_first(insert_sql, parameters=(
            json.dumps(donnees_aggregees['metadata']),
            datetime.now()
        ))
        
        if result:
            agg_id = result[0]
            print(f"💾 Données sauvegardées dans PostgreSQL (ID: {agg_id})")
            
            # Log détaillé
            print("📋 RÉSUMÉ DE L'AGRÉGATION:")
            metadata = donnees_aggregees['metadata']
            print(f"   • Enregistrements: {metadata['total_records']}")
            print(f"   • Sources: {metadata['sources']}")
            print(f"   • Queue initiale: {metadata.get('redis_initial_count', 'N/A')}")
            print(f"   • Traités: {metadata.get('records_processed', 'N/A')}")
            print(f"   • Type: {metadata['aggregation_type']}")
            
        else:
            print("⚠️ Aucun ID retourné lors de l'insertion")
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde PostgreSQL: {e}")
        logging.error(f"Erreur sauvegarde PostgreSQL: {e}")

def verifier_etat_redis():
    """Vérification complète de l'état Redis"""
    try:
        print("🔴 ÉTAT COMPLET REDIS:")
        
        queues = {
            'API': 'queue_api',
            'Fichiers': 'queue_file', 
            'Web': 'queue_web',
            'BD': 'queue_db',
            'Normalisées': 'queue_normalized'
        }
        
        status_global = {}
        
        for nom, queue in queues.items():
            length = redis_client.get_queue_length(queue)
            status_global[queue] = length
            
            # État détaillé
            if length == 0:
                print(f"   ✅ {nom} ({queue}): VIDE")
            elif length < 10:
                print(f"   ⚠️  {nom} ({queue}): {length} éléments")
            else:
                print(f"   🔥 {nom} ({queue}): {length} éléments")
        
        # Résumé global
        total_elements = sum(status_global.values())
        queues_non_vides = [q for q, l in status_global.items() if l > 0]
        
        print(f"📊 RÉSUMÉ REDIS:")
        print(f"   • Total éléments: {total_elements}")
        print(f"   • Queues non vides: {len(queues_non_vides)}")
        print(f"   • Queues: {queues_non_vides}")
        
        return f"REDIS_CHECK_{total_elements}_ITEMS"
        
    except Exception as e:
        print(f"❌ Erreur vérification Redis: {e}")
        return f"REDIS_ERROR_{str(e)}"

def verifier_agregation():
    """Vérification de l'agrégation récente"""
    try:
        hook = PostgresHook(postgres_conn_id='imo_db')
        
        # Dernière agrégation
        derniere_agg = hook.get_first("""
            SELECT 
                id,
                metadata->>'total_records' as total_records,
                metadata->>'sources' as sources,
                metadata->>'redis_initial_count' as redis_count,
                created_at
            FROM donnees_aggregees 
            ORDER BY created_at DESC 
            LIMIT 1;
        """)
        
        if derniere_agg:
            agg_id, total_records, sources, redis_count, created_at = derniere_agg
            print("✅ DERNIÈRE AGRÉGATION VÉRIFIÉE:")
            print(f"   • ID: {agg_id}")
            print(f"   • Enregistrements: {total_records}")
            print(f"   • Redis initial: {redis_count}")
            print(f"   • Sources: {sources}")
            print(f"   • Date: {created_at}")
        else:
            print("ℹ️ Aucune agrégation trouvée dans la base")
            
        return "VERIFICATION_COMPLETED"
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return f"VERIFICATION_ERROR_{str(e)}"

def nettoyer_agregations_anciennes():
    """Nettoyage des agrégations anciennes"""
    try:
        hook = PostgresHook(postgres_conn_id='imo_db')
        
        # Compter avant nettoyage
        count_avant = hook.get_first("SELECT COUNT(*) FROM donnees_aggregees;")
        
        # Supprimer les agrégations de plus de 30 jours
        delete_sql = """
        DELETE FROM donnees_aggregees 
        WHERE created_at < NOW() - INTERVAL '30 days';
        """
        
        hook.run(delete_sql)
        
        # Compter après nettoyage
        count_apres = hook.get_first("SELECT COUNT(*) FROM donnees_aggregees;")
        supprimes = (count_avant[0] if count_avant else 0) - (count_apres[0] if count_apres else 0)
        
        print(f"🧹 Nettoyage des agrégations anciennes:")
        print(f"   • Agrégations supprimées: {supprimes}")
        print(f"   • Agrégations restantes: {count_apres[0] if count_apres else 0}")
        
        return "CLEANUP_COMPLETED"
        
    except Exception as e:
        print(f"⚠️ Erreur nettoyage: {e}")
        return f"CLEANUP_ERROR_{str(e)}"


with DAG(
    'imo_t_workers_aggregation_redis',
    default_args={
        'owner': 'airflow', 
        'retries': 2,
        'retry_delay': timedelta(minutes=5)  
    },
    description='Workers d agrégation des données - REDIS ACTIF',
    schedule_interval=timedelta(hours=1),  
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['workers', 'aggregation', 'imo_db', 'redis'],
) as dag:

    check_redis = PythonOperator(
        task_id='verifier_etat_redis',
        python_callable=verifier_etat_redis,
    )

    aggregate_data = PythonOperator(
        task_id='agreger_donnees',
        python_callable=agreger_donnees,
    )

    verify_aggregation = PythonOperator(
        task_id='verifier_agregation',
        python_callable=verifier_agregation,
    )

    cleanup_old = PythonOperator(
        task_id='nettoyer_agregations_anciennes',
        python_callable=nettoyer_agregations_anciennes,
    )

    # Workflow: vérification Redis → agrégation → vérification → nettoyage
    check_redis >> aggregate_data >> verify_aggregation >> cleanup_old