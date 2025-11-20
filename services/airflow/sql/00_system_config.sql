-- =============================================
-- CONFIGURATION SYSTÈME ET UTILISATEURS
-- =============================================

-- Autoriser PostgreSQL à écouter sur toutes les interfaces
ALTER SYSTEM SET listen_addresses = '*';

-- Recharger la configuration
SELECT pg_reload_conf();

-- Vérifier et créer les utilisateurs s'ils n'existent pas
DO $$ 
BEGIN
    -- 🔥 CORRECTION : Création EXPLICITE de l'utilisateur airflow
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'airflow') THEN
        CREATE USER airflow WITH PASSWORD 'airflow';
        RAISE NOTICE 'Utilisateur airflow créé';
    ELSE
        -- S'assurer que le mot de passe est correct
        ALTER USER airflow WITH PASSWORD 'airflow';
        RAISE NOTICE 'Utilisateur airflow existe déjà - mot de passe mis à jour';
    END IF;

    -- Utilisateur imo_user
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'imo_user') THEN
        CREATE USER imo_user WITH PASSWORD 'password';
        RAISE NOTICE 'Utilisateur imo_user créé';
    ELSE
        RAISE NOTICE 'Utilisateur imo_user existe déjà';
    END IF;

    -- Utilisateur grafana
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'grafana') THEN
        CREATE USER grafana WITH PASSWORD 'grafana';
        RAISE NOTICE 'Utilisateur grafana créé';
    ELSE
        RAISE NOTICE 'Utilisateur grafana existe déjà';
    END IF;

    -- Utilisateur readonly
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly') THEN
        CREATE USER readonly WITH PASSWORD 'readonly';
        RAISE NOTICE 'Utilisateur readonly créé';
    ELSE
        RAISE NOTICE 'Utilisateur readonly existe déjà';
    END IF;

END $$;

-- 🔥 CORRECTION : Accorder les privilèges nécessaires à airflow
ALTER USER airflow WITH CREATEDB CREATEROLE;

-- Message de confirmation final
DO $$ BEGIN 
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'CONFIGURATION SYSTÈME TERMINÉE AVEC SUCCÈS';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Utilisateurs créés : airflow, imo_user, grafana, readonly';
    RAISE NOTICE 'Les bases de données seront créées dans le script suivant';
END $$;