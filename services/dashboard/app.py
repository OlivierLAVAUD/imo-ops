import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, exc

# Charger les variables d'environnement
load_dotenv()

# Connexion à la base PostgreSQL avec retry
def create_db_connection():
    DATABASE_URL = os.getenv('DATABASE_URL')
    max_retries = 5
    retry_delay = 5  # secondes
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(DATABASE_URL)
            # Test de connexion
            with engine.connect() as conn:
                print("✅ Connexion PostgreSQL réussie")
            return engine
        except exc.OperationalError as e:
            print(f"❌ Tentative {attempt + 1}/{max_retries} échouée: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
            else:
                raise Exception(f"Impossible de se connecter à PostgreSQL après {max_retries} tentatives")

# Fonction pour récupérer les données avec gestion d'erreur
def get_data(query, engine):
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de la requête: {e}")
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Création du layout (vide au début)
app.layout = html.Div([
    html.H1("Tableau de Bord - Analyse des Commandes"),
    html.Div(id="loading", children="Chargement des données..."),
    html.Div(id="graphs-container")
])

# Callback pour charger les données après le démarrage
@app.callback(
    dash.dependencies.Output('graphs-container', 'children'),
    dash.dependencies.Input('loading', 'children')
)
def load_data(_):
    try:
        # Établir la connexion
        engine = create_db_connection()
        
        # Charger les requêtes SQL
        queries = {}
        sql_dir = 'sql'
        
        if os.path.exists(sql_dir):
            for i in range(1, 9):
                file_path = os.path.join(sql_dir, f'{i}.sql')
                if os.path.exists(file_path):
                    with open(file_path, 'r') as file:
                        queries[f'query_{i}'] = file.read()
                else:
                    print(f"⚠️ Fichier {file_path} non trouvé")
                    queries[f'query_{i}'] = "SELECT 1 as test"  # Requête par défaut
        else:
            print("❌ Dossier 'sql' non trouvé")
            return html.Div("Erreur: Dossier 'sql' manquant")
        
        # Exécuter les requêtes
        df = {}
        for name, query in queries.items():
            df[name] = get_data(query, engine)
        
        # Créer les graphiques seulement si les DataFrames ne sont pas vides
        graphs = []
        
        if not df.get("query_1", pd.DataFrame()).empty:
            fig_1 = px.bar(df["query_1"], x='nom_client', y='nombre_commandes', 
                          title="Nombre de commandes par client")
            graphs.append(dcc.Graph(figure=fig_1))
        
        if not df.get("query_2", pd.DataFrame()).empty:
            fig_2 = px.pie(df["query_2"], names='nom_client', 
                          values='chiffre_affaires', 
                          title="Chiffre d'affaires par client")
            graphs.append(dcc.Graph(figure=fig_2))
        
        # Ajouter les autres graphiques de la même manière...
        
        return graphs
        
    except Exception as e:
        return html.Div(f"❌ Erreur lors du chargement des données: {str(e)}")

# Lancer l'application avec la méthode correcte
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=True)