-- =============================================
-- BASE DE DONNÉES AIRFLOW_DB - COMPLETE
-- =============================================

-- Créer la base de données si elle n'existe pas
SELECT 'CREATE DATABASE airflow_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_db')\gexec

-- Se connecter à la base airflow_db
\c airflow_db;

-- Donner tous les privilèges à l'utilisateur airflow
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow;
GRANT ALL PRIVILEGES ON SCHEMA public TO airflow;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO airflow;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO airflow;

DO $$ BEGIN 
    RAISE NOTICE 'Base de données airflow_db créée et configurée avec succès'; 
END $$;