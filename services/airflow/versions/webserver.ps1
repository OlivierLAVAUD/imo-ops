# Créer un script webserver simple
@"
import os
import sys

# Chemin relatif - la base de données sera dans le même répertoire
os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = 'sqlite:///airflow.db'

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
"@ | Out-File -FilePath "run_webserver.py" -Encoding utf8