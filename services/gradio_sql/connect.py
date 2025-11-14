import os
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Vérifier si les variables sont bien chargées
print("DATABASE_URL:", os.getenv("DATABASE_URL"))

# Récupérer les paramètres de connexion
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    # Connexion à la base PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Exécuter une requête pour lister les tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
    """)

    tables = cursor.fetchall()

    print("Tables présentes dans la base :")
    for table in tables:
        print("-", table[0])

    # Fermer la connexion
    cursor.close()
    conn.close()

except Exception as e:
    print("Erreur de connexion :", e)