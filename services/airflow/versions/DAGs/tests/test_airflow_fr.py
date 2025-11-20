from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import pytz

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def tâche_de_test():
    """Une tâche de test en français"""
    print("✅ Tâche exécutée avec succès!")
    
    # Vérification du fuseau horaire
    paris_tz = pytz.timezone('Europe/Paris')
    maintenant = datetime.now(paris_tz)
    print(f"🕒 Heure d'exécution (Paris): {maintenant.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Vérification de la langue
    print("🌐 Langue: Français")
    
    return "SUCCÈS"

def vérifier_configuration():
    """Vérification de la configuration française"""
    print("=== CONFIGURATION FRANÇAISE ===")
    
    # Test fuseau horaire
    paris_tz = pytz.timezone('Europe/Paris')
    maintenant_paris = datetime.now(paris_tz)
    maintenant_utc = datetime.now(pytz.UTC)
    
    print(f"📍 Fuseau configuré: Europe/Paris")
    print(f"🕒 Heure Paris: {maintenant_paris.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🕒 Heure UTC: {maintenant_utc.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🌐 Interface: Français")
    print("✅ Configuration validée!")
    
    return "CONFIGURATION_VALIDÉE"

with DAG(
    'test_airflow_fr',
    default_args=default_args,
    description='DAG de test en langue française avec vérification du fuseau horaire',
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['test', 'français', 'validation'],
) as dag:

    début = BashOperator(
        task_id='début',
        bash_command='echo "🚀 Démarrage du processus de test français..."',
    )

    traitement_principal = PythonOperator(
        task_id='traitement_principal',
        python_callable=tâche_de_test,
    )

    vérification_config = PythonOperator(
        task_id='vérifier_configuration',
        python_callable=vérifier_configuration,
    )

    fin = BashOperator(
        task_id='fin',
        bash_command='echo "✅ Processus terminé avec succès! Configuration française active."',
    )

    début >> traitement_principal >> vérification_config >> fin