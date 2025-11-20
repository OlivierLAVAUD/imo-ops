import os
import sqlite3
import sys

print("🔧 Réparation d'Airflow...")

# Chemin de la base de données
db_path = os.path.join(os.getcwd(), 'airflow.db')
print(f"Base de données: {db_path}")

# 1. Vérifier si le fichier existe et est accessible
if os.path.exists(db_path):
    try:
        # Tester la connexion
        conn = sqlite3.connect(db_path)
        conn.close()
        print("✓ Base de données accessible")
    except Exception as e:
        print(f"✗ Base de données corrompue: {e}")
        # Sauvegarder l'ancien fichier
        backup_path = db_path + '.backup'
        os.rename(db_path, backup_path)
        print(f"✓ Ancienne DB sauvegardée: {backup_path}")
else:
    print("✓ Base de données à créer")

# 2. Réinitialiser avec les commandes Airflow
print("Initialisation de la base de données...")
os.system('airflow db migrate')
os.system('airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin')

print("✅ Réparation terminée!")