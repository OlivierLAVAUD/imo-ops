-- =============================================
-- CONFIGURATION DES BASES DE DONNÉES
-- =============================================

-- Vérifier que la base imo_db existe et configurer les permissions
DO $$ 
BEGIN
    -- Vérifier si la base imo_db existe
    IF EXISTS (SELECT FROM pg_database WHERE datname = 'imo_db') THEN
        RAISE NOTICE 'Base de données imo_db existe déjà';
        
        -- 🔥 S'assurer que imo_user est bien le propriétaire
        IF NOT EXISTS (
            SELECT 1 FROM pg_database 
            WHERE datname = 'imo_db' AND datdba = (SELECT oid FROM pg_roles WHERE rolname = 'imo_user')
        ) THEN
            -- Changer le propriétaire si nécessaire
            EXECUTE 'ALTER DATABASE imo_db OWNER TO imo_user';
            RAISE NOTICE 'Propriétaire de imo_db défini sur imo_user';
        END IF;
        
    ELSE
        RAISE NOTICE 'Base de données imo_db non trouvée - création par le script système';
    END IF;
END $$;

-- 🔥 CORRECTION : Configurer les permissions même si la base existe déjà
GRANT ALL PRIVILEGES ON DATABASE imo_db TO imo_user;
GRANT CONNECT, TEMPORARY ON DATABASE imo_db TO airflow, grafana, readonly;

-- 🔥 CORRECTION : Configurer les permissions pour la base airflow aussi
GRANT CONNECT, TEMPORARY ON DATABASE airflow TO imo_user, grafana, readonly;

-- Message de confirmation
DO $$ BEGIN 
    RAISE NOTICE 'Configuration des bases de données terminée avec succès';
    RAISE NOTICE 'Permissions accordées sur imo_db : imo_user, airflow, grafana, readonly';
    RAISE NOTICE 'Permissions accordées sur airflow : imo_user, grafana, readonly';
END $$;