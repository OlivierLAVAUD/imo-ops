import os
import sys
import time

# Configuration
current_dir = os.getcwd()
db_path = os.path.join(current_dir, 'airflow.db')
db_uri = f'sqlite:////{db_path}'.replace('\\', '/')

os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = db_uri
os.environ['AIRFLOW_HOME'] = current_dir
os.environ['AIRFLOW__CORE__EXECUTOR'] = 'SequentialExecutor'

# Bloquer les modules problématiques
sys.modules['daemon'] = None
sys.modules['pwd'] = None
sys.modules['grp'] = None

print("🚀 DÉMARRAGE AIRFLOW")
print(f"Répertoire: {current_dir}")
print(f"Base de données: {db_path}")
print(f"URI: {db_uri}")

try:
    from airflow.www.app import create_app
    print("✓ Importation Airflow réussie")
    
    app = create_app()
    print("✅ APPLICATION AIRFLOW CRÉÉE!")
    print("🌐 Serveur démarré sur http://localhost:8080")
    print("👤 Connectez-vous avec: admin / admin")
    print("⏹️  Ctrl+C pour arrêter le serveur")
    
    # Démarrer le serveur
    app.run(host='0.0.0.0', port=8080, debug=False)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("🔄 Tentative de récupération...")
    
    # Réessayer
    try:
        from airflow.www.app import create_app
        app = create_app()
        print("✅ RÉCUPÉRATION RÉUSSIE!")
        print("🌐 http://localhost:8080")
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e2:
        print(f"💥 Échec final: {e2}")
        print("⏳ Fermeture dans 10 secondes...")
        time.sleep(10)