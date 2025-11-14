import gradio as gr
import psycopg2
import os
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy import create_engine

# Load environment variables from .env file
load_dotenv()

# Database connection parameters
DATABASE_URL = os.getenv('DATABASE_URL')

# Analyze the database URL
parsed_url = urlparse(DATABASE_URL)
dbname = parsed_url.path[1:]
user = parsed_url.username
password = parsed_url.password
host = parsed_url.hostname
port = parsed_url.port

# Connect to the PostgreSQL database with SQLAlchemy
engine = create_engine(DATABASE_URL)

def query_database(query):
    try:
        # Connect to the PostgreSQL database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                # Execute the query
                cursor.execute(query)

                # Fetch all results
                results = cursor.fetchall()

        return str(results)
    except psycopg2.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

def get_data(query):
    df = pd.read_sql(query, engine)
    return df

def generate_graphs():
    df_boites = get_data("SELECT nom_matiere, COUNT(*) as nb_boites FROM boites_details GROUP BY nom_matiere;")
    df_couleurs = get_data("SELECT nom_couleur, COUNT(*) as nb_boites FROM boites_details GROUP BY nom_couleur;")
    df_commandes = get_data("SELECT date_commande, COUNT(*) as nb_commandes FROM COMMANDES GROUP BY date_commande ORDER BY date_commande;")
    df_clients = get_data("SELECT c.nom_client, SUM(l.quantite) as total_boites FROM LIGNES_COMMANDE l JOIN COMMANDES cmd ON l.id_commande = cmd.id_commande JOIN CLIENTS c ON cmd.id_client = c.id_client GROUP BY c.nom_client ORDER BY total_boites DESC;")
    df_ventes = get_data("SELECT date_commande, SUM(quantite * prix_unitaire * (1 - taux_remise)) as total_ventes FROM LIGNES_COMMANDE l JOIN COMMANDES c ON l.id_commande = c.id_commande GROUP BY date_commande ORDER BY date_commande;")

    # Create the graphs
    fig_matiere = px.bar(df_boites, x='nom_matiere', y='nb_boites', title="Répartition des boîtes par matière")
    fig_couleur = px.pie(df_couleurs, names='nom_couleur', values='nb_boites', title="Répartition des boîtes par couleur")
    fig_commandes = px.line(df_commandes, x='date_commande', y='nb_commandes', title="Évolution des commandes")
    fig_clients = px.bar(df_clients, x='nom_client', y='total_boites', title="Quantité de boîtes commandées par client")
    fig_ventes = px.line(df_ventes, x='date_commande', y='total_ventes', title="Valeur totale des ventes par jour")

    return fig_matiere, fig_couleur, fig_commandes, fig_clients, fig_ventes

# Define the Gradio interface
iface = gr.Interface(
    fn=query_database,
    inputs=gr.Textbox(lines=5, placeholder="Entrez votre requête SQL ici..."),
    outputs=[
        gr.Textbox(),
        gr.Plot(),
        gr.Plot(),
        gr.Plot(),
        gr.Plot(),
        gr.Plot()
    ],
    title="DATABOX - SQL Query Interface",
    description="Enter your SQL query and get the results."
)

# Launch the Gradio interface
iface.launch(server_name="0.0.0.0", server_port=7860)