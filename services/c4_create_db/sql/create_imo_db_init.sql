-- Script pour créer la base de données imo_db
-- Supprime la base si elle existe déjà et la recrée

DROP DATABASE IF EXISTS imo_db;

CREATE DATABASE imo_db 
    ENCODING 'UTF8'
    LC_COLLATE 'fr_FR.UTF-8'
    LC_CTYPE 'fr_FR.UTF-8'
    TEMPLATE template0;

-- Message de confirmation
SELECT 'Base de donnees imo_db creee avec succes' as status;