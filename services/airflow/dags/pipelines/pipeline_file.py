from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.redis_client import redis_client
import pandas as pd
import os
import json

def traiter_fichiers():
    """Traitement de fichiers (CSV, Excel, JSON) - VERSION AMÉLIORÉE"""
    print("📁 Démarrage du traitement des fichiers...")
    
    # Simulation de données fichiers plus réalistes
    donnees_fichiers = [
        {
            'source': 'fichier_csv_1',
            'data': {
                'id_client': 'CLI_001',
                'nom': 'Client A', 
                'email': 'client.a@example.com',
                'valeur_achat': 1000,
                'categorie': 'Premium',
                'date_inscription': '2024-01-15'
            },
            'timestamp': datetime.now().isoformat(),
            'type': 'client',
            'format_origine': 'CSV',
            'taille_fichier': '2.5MB'
        },
        {
            'source': 'fichier_excel_1',
            'data': {
                'id_produit': 'PROD_XYZ',
                'produit': 'Produit Y', 
                'quantite': 50,
                'prix_unitaire': 29.99,
                'categorie': 'Électronique',
                'stock_alerte': 10
            },
            'timestamp': datetime.now().isoformat(), 
            'type': 'inventaire',
            'format_origine': 'Excel',
            'taille_fichier': '1.8MB'
        },
        {
            'source': 'fichier_json_1',
            'data': {
                'transaction_id': 'TXN_789',
                'montant': 450.75,
                'devise': 'EUR',
                'moyen_paiement': 'Carte',
                'statut': 'Complétée',
                'date_transaction': '2024-01-20 14:30:00'
            },
            'timestamp': datetime.now().isoformat(),
            'type': 'transaction', 
            'format_origine': 'JSON',
            'taille_fichier': '0.8MB'
        }
    ]
    
    fichiers_traites = 0
    try:
        for donnee in donnees_fichiers:
            # Validation des données avant envoi
            if isinstance(donnee, dict) and 'data' in donnee:
                redis_client.push_to_queue('queue_file', json.dumps(donnee))
                fichiers_traites += 1
                print(f"  📤 Fichier envoyé: {donnee['source']}")
            else:
                print(f"⚠️  Format de donnée invalide ignoré: {donnee}")
        
        print(f"✅ {fichiers_traites} fichiers traités et envoyés vers Redis")
        
        # Vérification de la queue
        queue_length = redis_client.get_queue_length('queue_file')
        print(f"🔴 État queue fichiers: {queue_length} éléments")
        
        return f"FILES_PROCESSED_{fichiers_traites}"
        
    except Exception as e:
        print(f"❌ Erreur traitement fichiers: {e}")
        return f"FILES_ERROR_{str(e)}"

def verifier_fichiers_disponibles():
    """Vérification des fichiers disponibles - NOUVELLE TÂCHE"""
    print("🔍 Vérification des fichiers à traiter...")
    
    # Simulation de la détection de fichiers
    fichiers_detectes = [
        {'nom': 'clients_2024.csv', 'taille': '2.5MB', 'lignes': 1500},
        {'nom': 'inventaire.xlsx', 'taille': '1.8MB', 'feuilles': 3},
        {'nom': 'transactions.json', 'taille': '0.8MB', 'enregistrements': 89}
    ]
    
    print(f"📋 Fichiers détectés ({len(fichiers_detectes)}):")
    for fichier in fichiers_detectes:
        print(f"   • {fichier['nom']} ({fichier['taille']})")
    
    return f"FILES_DETECTED_{len(fichiers_detectes)}"

def nettoyer_fichiers_traites():
    """Nettoyage après traitement - NOUVELLE TÂCHE"""
    print("🧹 Nettoyage des fichiers traités...")
    
    # Simulation du nettoyage
    try:
        # Vérifier l'état de la queue après traitement
        queue_restante = redis_client.get_queue_length('queue_file')
        
        if queue_restante == 0:
            print("✅ Tous les fichiers ont été traités avec succès")
            # Simulation : suppression des fichiers sources
            print("🗑️  Suppression des fichiers sources temporaires...")
        else:
            print(f"⚠️  Il reste {queue_restante} fichiers en attente de traitement")
        
        return "CLEANUP_COMPLETED"
        
    except Exception as e:
        print(f"⚠️  Erreur lors du nettoyage: {e}")
        return "CLEANUP_WITH_WARNINGS"

# CORRECTION : Nom du DAG pour correspondre à l'orchestrateur
with DAG(
    'imo_t_pipeline_files', 
    default_args={
        'owner': 'airflow', 
        'retries': 2,
        'retry_delay': timedelta(minutes=3)
    },
    description='Pipeline de traitement de fichiers - IMO',
    schedule_interval=None, 
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['pipeline', 'file', 'processing', 'imo'],
) as dag:

    check_files = PythonOperator(
        task_id='verifier_fichiers_disponibles',
        python_callable=verifier_fichiers_disponibles,
    )

    process_files = PythonOperator(
        task_id='traiter_fichiers',
        python_callable=traiter_fichiers,
    )

    cleanup_files = PythonOperator(
        task_id='nettoyer_fichiers_traites',
        python_callable=nettoyer_fichiers_traites,
    )

    # Workflow: vérification → traitement → nettoyage
    check_files >> process_files >> cleanup_files