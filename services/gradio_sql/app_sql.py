import gradio as gr
import psycopg2
import os

# Database connection parameters
DATABASE_URL = os.getenv('DATABASE_URL')
#DATABASE_URL="postgres://admin:password@db:5432/databox_db"

print(DATABASE_URL)
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

# Define the Gradio interface
iface = gr.Interface(
    fn=query_database,
    inputs=gr.Textbox(lines=5, placeholder="Entrez votre requête SQL ici..."),
    outputs=gr.Textbox(),
    title="DATABOX - SQL Query Interface",
    description="Enter your SQL query and get the results."
)

# Launch the Gradio interface
# iface.launch(server_name="0.0.0.0", server_port=7860) # for Docker
iface.launch(server_name="localhost", server_port=7860) # for localhost