import os
import sys
import logging

# Désactiver les logs bruyants
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Bloquer les modules problématiques
sys.modules['daemon'] = None
sys.modules['pwd'] = None
sys.modules['grp'] = None

# Configuration
os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = 'sqlite:////D:/dev/imo-ops/services/airflow/airflow.db'
os.environ['AIRFLOW_HOME'] = 'D:/dev/imo-ops/services/airflow'
os.environ['AIRFLOW__WEBSERVER__EXPOSE_CONFIG'] = 'False'

print("🚀 Initialisation d'Airflow...")

try:
    from airflow.www.app import create_app
    from airflow.utils.db import check_and_run_migrations
    
    print("✓ Importations réussies")
    
    # Forcer les migrations de base de données
    print("Vérification de la base de données...")
    check_and_run_migrations()
    print("✓ Base de données OK")
    
    # Créer l'application
    app = create_app()
    print("✅ Application Airflow créée avec succès!")
    print("🌐 Serveur démarré sur http://localhost:8080")
    print("📊 Ouvrez votre navigateur et connectez-vous")
    print("⏹️  Ctrl+C pour arrêter le serveur")
    
    # Démarrer le serveur
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    
except Exception as e:
    print(f"❌ Erreur critique: {e}")
    print("Tentative de récupération...")
    
    # Deuxième tentative avec gestion d'erreur plus permissive
    try:
        from airflow.www.app import create_app
        app = create_app()
        print("✅ Récupération réussie! Serveur démarré sur http://localhost:8080")
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except:
        print("Échec complet. Appuyez sur Entrée pour fermer...")
        input()