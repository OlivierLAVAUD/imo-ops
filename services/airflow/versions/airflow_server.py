import os
import sys

# BLOCAGE des modules problématiques AVANT toute importation
sys.modules['daemon'] = None
sys.modules['pwd'] = None
sys.modules['grp'] = None

# Configuration
os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = 'sqlite:////D:/dev/imo-ops/services/airflow/airflow.db'
os.environ['AIRFLOW_HOME'] = 'D:/dev/imo-ops/services/airflow'

print("🚀 Démarrage d'Airflow...")

try:
    # Maintenant importer Airflow
    from airflow.www.app import create_app
    
    app = create_app()
    print("✅ Serveur Airflow DÉMARRÉ sur http://localhost:8080")
    print("📊 Interface disponible dans le navigateur")
    print("⏹️  Ctrl+C pour arrêter")
    
    # Démarrer le serveur
    app.run(host='0.0.0.0', port=8080, debug=False)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    input("Appuyez sur Entrée pour fermer...")
