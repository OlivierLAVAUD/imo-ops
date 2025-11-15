-- =============================================
-- BASE DE DONNÉES GRAFANA_DB - COMPLETE
-- =============================================

-- Créer la base de données si elle n'existe pas
SELECT 'CREATE DATABASE grafana_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'grafana_db')\gexec

-- Se connecter à la base grafana_db
\c grafana_db;

-- Donner tous les privilèges à l'utilisateur grafana
GRANT ALL PRIVILEGES ON DATABASE grafana_db TO grafana;
GRANT ALL PRIVILEGES ON SCHEMA public TO grafana;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO grafana;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO grafana;

DO $$ BEGIN 
    RAISE NOTICE 'Base de données grafana_db créée et configurée avec succès'; 
END $$;