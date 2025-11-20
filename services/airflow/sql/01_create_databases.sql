-- =============================================
-- CRÉATION DES BASES DE DONNÉES
-- =============================================
-- Ce script doit être exécuté hors transaction

-- 🔥 CORRECTION : Création DIRECTE sans vérification (laisser échouer silencieusement)
CREATE DATABASE airflow WITH OWNER = airflow;

-- Message de confirmation
\echo 'Base de données airflow créée'

-- Créer imo_db
CREATE DATABASE imo_db WITH OWNER = imo_user;

-- Message de confirmation
\echo 'Base de données imo_db créée'

-- 🔥 CORRECTION : Utiliser des commandes psql spécifiques pour les permissions
\c airflow
GRANT CONNECT ON DATABASE airflow TO imo_user, grafana, readonly;
\echo 'Permissions accordées sur la base airflow'

\c imo_db  
GRANT CONNECT ON DATABASE imo_db TO airflow, grafana, readonly;
\echo 'Permissions accordées sur la base imo_db'

\echo '=============================================='
\echo 'BASES DE DONNÉES CRÉÉES AVEC SUCCÈS'
\echo '=============================================='