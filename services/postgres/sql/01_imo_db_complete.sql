-- =============================================
-- BASE DE DONNÉES IMO_DB - COMPLETE
-- =============================================

-- Créer la base de données si elle n'existe pas
SELECT 'CREATE DATABASE imo_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'imo_db')\gexec

-- Se connecter à la base imo_db
\c imo_db;

-- Activer les extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ==================== TABLES PRINCIPALES ====================

-- Table annonces
CREATE TABLE IF NOT EXISTS annonces (
    id_annonce SERIAL PRIMARY KEY,
    reference VARCHAR(50) UNIQUE NOT NULL,
    titre VARCHAR(255) NOT NULL,
    titre_complet VARCHAR(500),
    prix NUMERIC(15,2),
    prix_detaille VARCHAR(100),
    prix_au_m2 NUMERIC(10,2),
    localisation VARCHAR(255),
    localisation_complete VARCHAR(500),
    surface NUMERIC(8,2),
    surface_terrain NUMERIC(10,2),
    pieces INTEGER,
    type_bien VARCHAR(100),
    description TEXT,
    annee_construction INTEGER,
    honoraires VARCHAR(100),
    image_url VARCHAR(500),
    nombre_photos INTEGER,
    has_video BOOLEAN DEFAULT false,
    has_visite_virtuelle BOOLEAN DEFAULT false,
    media_info VARCHAR(255),
    lien VARCHAR(500),
    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dpe_classe_active VARCHAR(1),
    ges_classe_active VARCHAR(1),
    depenses_energie_min VARCHAR(50),
    depenses_energie_max VARCHAR(50),
    annee_reference INTEGER
);

-- Table caractéristiques
CREATE TABLE IF NOT EXISTS caracteristiques (
    id_caracteristique SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    valeur VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table images
CREATE TABLE IF NOT EXISTS images (
    id_image SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    ordre INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table DPE
CREATE TABLE IF NOT EXISTS dpe (
    id_dpe SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    classe_energie VARCHAR(1),
    indice_energie INTEGER,
    classe_climat VARCHAR(1),
    indice_climat INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table copropriété
CREATE TABLE IF NOT EXISTS copropriete (
    id_copropriete SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    nb_lots INTEGER,
    charges_previsionnelles VARCHAR(100),
    procedures VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table conseiller
CREATE TABLE IF NOT EXISTS conseiller (
    id_conseiller SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    nom_complet VARCHAR(255),
    telephone VARCHAR(20),
    lien VARCHAR(500),
    photo VARCHAR(500),
    note VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== INDEXES ====================

CREATE INDEX IF NOT EXISTS idx_annonces_reference ON annonces(reference);
CREATE INDEX IF NOT EXISTS idx_annonces_localisation ON annonces(localisation);
CREATE INDEX IF NOT EXISTS idx_annonces_type_bien ON annonces(type_bien);
CREATE INDEX IF NOT EXISTS idx_annonces_prix ON annonces(prix);
CREATE INDEX IF NOT EXISTS idx_annonces_surface ON annonces(surface);
CREATE INDEX IF NOT EXISTS idx_annonces_date_extraction ON annonces(date_extraction);

CREATE INDEX IF NOT EXISTS idx_caracteristiques_annonce ON caracteristiques(id_annonce);
CREATE INDEX IF NOT EXISTS idx_images_annonce ON images(id_annonce);
CREATE INDEX IF NOT EXISTS idx_dpe_annonce ON dpe(id_annonce);
CREATE INDEX IF NOT EXISTS idx_copropriete_annonce ON copropriete(id_annonce);
CREATE INDEX IF NOT EXISTS idx_conseiller_annonce ON conseiller(id_annonce);

-- ==================== FONCTIONS ====================

CREATE OR REPLACE FUNCTION nettoyer_prix(prix_text VARCHAR) 
RETURNS NUMERIC AS $$
BEGIN
    RETURN NULLIF(REGEXP_REPLACE(prix_text, '[^0-9]', '', 'g'), '')::NUMERIC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculer_prix_au_m2(prix NUMERIC, surface NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    IF surface > 0 AND prix > 0 THEN
        RETURN ROUND(prix / surface, 2);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ==================== VUES ====================

CREATE OR REPLACE VIEW annonces_complete AS
SELECT 
    a.*,
    c.nom_complet as conseiller_nom,
    c.telephone as conseiller_telephone,
    d.classe_energie,
    d.classe_climat,
    cp.nb_lots as copropriete_nb_lots,
    COUNT(DISTINCT i.id_image) as total_images,
    COUNT(DISTINCT car.id_caracteristique) as total_caracteristiques
FROM annonces a
LEFT JOIN conseiller c ON a.id_annonce = c.id_annonce
LEFT JOIN dpe d ON a.id_annonce = d.id_annonce
LEFT JOIN copropriete cp ON a.id_annonce = cp.id_annonce
LEFT JOIN images i ON a.id_annonce = i.id_annonce
LEFT JOIN caracteristiques car ON a.id_annonce = car.id_annonce
GROUP BY a.id_annonce, c.id_conseiller, d.id_dpe, cp.id_copropriete;

CREATE OR REPLACE VIEW v_stats_type_bien AS
SELECT 
    type_bien,
    COUNT(*) as nombre_annonces,
    AVG(prix) as prix_moyen,
    AVG(surface) as surface_moyenne,
    MIN(prix) as prix_min,
    MAX(prix) as prix_max
FROM annonces 
WHERE type_bien IS NOT NULL 
GROUP BY type_bien
ORDER BY nombre_annonces DESC;

CREATE OR REPLACE VIEW v_stats_localisation AS
SELECT 
    localisation,
    COUNT(*) as nombre_annonces,
    AVG(prix) as prix_moyen,
    AVG(prix_au_m2) as prix_m2_moyen
FROM annonces 
WHERE localisation IS NOT NULL 
GROUP BY localisation
ORDER BY nombre_annonces DESC;

CREATE OR REPLACE VIEW v_stats_dpe AS
SELECT 
    dpe_classe_active,
    COUNT(*) as nombre_annonces,
    AVG(prix) as prix_moyen,
    AVG(surface) as surface_moyenne
FROM annonces 
WHERE dpe_classe_active IS NOT NULL 
GROUP BY dpe_classe_active
ORDER BY dpe_classe_active;

-- ==================== PERMISSIONS ====================

-- Donner les permissions à l'utilisateur imo_user
GRANT CONNECT ON DATABASE imo_db TO imo_user;
GRANT USAGE ON SCHEMA public TO imo_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO imo_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO imo_user;

-- Permissions en lecture seule
GRANT CONNECT ON DATABASE imo_db TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
GRANT SELECT ON annonces_complete, v_stats_type_bien, v_stats_localisation, v_stats_dpe TO readonly;

-- Permissions pour Grafana
GRANT CONNECT ON DATABASE imo_db TO grafana;
GRANT USAGE ON SCHEMA public TO grafana;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana;
GRANT SELECT ON annonces_complete, v_stats_type_bien, v_stats_localisation, v_stats_dpe TO grafana;

-- ==================== FINALISATION ====================

DO $$ BEGIN 
    RAISE NOTICE 'Base de données imo_db créée et configurée avec succès'; 
END $$;