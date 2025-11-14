-- Créer l'utilisateur et la base pour Airflow
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow_db;
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow;
