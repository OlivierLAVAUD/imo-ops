import os
import sys

# Chemin ABSOLU correct pour SQLite sur Windows
current_dir = os.getcwd()
db_path = os.path.join(current_dir, 'airflow.db')

# Format SQLite Windows avec 4 slashes
db_uri = f'sqlite:///{db_path}'.replace('\\', '/')

os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = db_uri
os.environ['AIRFLOW_HOME'] = current_dir
os.environ['AIRFLOW__CORE__EXECUTOR'] = 'SequentialExecutor'

# Bloquer les modules problématiques
sys.modules['daemon'] = None
sys.modules['pwd'] = None
sys.modules['grp'] = None

print("🚀 DÉMARRAGE FINAL AIRFLOW")
print(f"Répertoire: {current_dir}")
print(f"Base de données: {db_path}")
print(f"URI: {db_uri}")

try:
    from airflow.www.app import create_app
    app = create_app()
    print("✅ SERVEUR AIRFLOW DÉMARRÉ!")
    print("🌐 http://localhost:8080")
    print("👤 admin / admin")
    print("⏹️  Ctrl+C pour arrêter")
    
    # Démarrer le serveur
    app.run(host='0.0.0.0', port=8080, debug=False)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
