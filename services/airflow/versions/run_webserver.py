import os
import sys

# Forcer l'utilisation du chemin relatif
os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = 'sqlite:///airflow.db'
os.environ['AIRFLOW_HOME'] = os.getcwd()

print(f"Répertoire courant: {os.getcwd()}")
print(f"Chemin DB: {os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN']}")

# Désactiver les modules problématiques pour Windows
sys.modules['daemon'] = None

print('Démarrage du serveur Airflow avec chemin relatif...')

try:
    from airflow.www.app import create_app
    app = create_app()
    print('✓ Serveur Airflow démarré sur http://localhost:8080')
    print('✓ Base de données: ./airflow.db')
    app.run(host='0.0.0.0', port=8080, debug=False)
except Exception as e:
    print(f'✗ Erreur: {e}')
    import traceback
    traceback.print_exc()
