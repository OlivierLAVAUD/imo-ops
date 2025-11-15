-- =============================================
-- CONFIGURATION SYSTÈME ET UTILISATEURS
-- =============================================

-- Autoriser PostgreSQL à écouter sur toutes les interfaces
ALTER SYSTEM SET listen_addresses = '*';

-- Recharger la configuration
SELECT pg_reload_conf();

-- Créer les utilisateurs
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE USER imo_user WITH PASSWORD 'password';
CREATE USER grafana WITH PASSWORD 'grafana';
CREATE USER readonly WITH PASSWORD 'readonly';


-- Message de confirmation
DO $$ BEGIN 
    RAISE NOTICE 'Configuration système et utilisateurs créés avec succès'; 
END $$;