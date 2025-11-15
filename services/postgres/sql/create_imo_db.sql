-- Autoriser PostgreSQL à écouter sur toutes les interfaces réseau
ALTER SYSTEM SET listen_addresses = '*';

-- Ajouter une règle pour le réseau Docker dans pg_hba.conf
ALTER SYSTEM SET hba_file = '/var/lib/postgresql/data/pg_hba.conf';


-- =============================================
-- VÉRIFICATION DE LA BASE
-- =============================================
SELECT 'Exécution dans la base: ' || current_database() as info;

-- =============================================
-- SUPPRESSION DES OBJETS EXISTANTS AVEC CASCADE
-- =============================================

-- Supprimer les vues d'abord (elles dépendent des tables)
DROP VIEW IF EXISTS v_stats_pieces CASCADE;
DROP VIEW IF EXISTS v_stats_dpe CASCADE;
DROP VIEW IF EXISTS v_stats_localisation CASCADE;
DROP VIEW IF EXISTS v_stats_type_bien CASCADE;
DROP VIEW IF EXISTS annonces_complete CASCADE;

-- Supprimer les fonctions
DROP FUNCTION IF EXISTS nettoyer_prix(VARCHAR) CASCADE;

-- Supprimer les tables (l'ordre est important à cause des clés étrangères)
DROP TABLE IF EXISTS images CASCADE;
DROP TABLE IF EXISTS caracteristiques CASCADE;
DROP TABLE IF EXISTS copropriete CASCADE;
DROP TABLE IF EXISTS dpe CASCADE;
DROP TABLE IF EXISTS conseiller CASCADE;
DROP TABLE IF EXISTS annonces CASCADE;

-- =============================================
-- CRÉATION DES TABLES
-- =============================================

-- Création de la table ANNONCES
CREATE TABLE annonces (
    id_annonce SERIAL PRIMARY KEY,
    reference VARCHAR(50) UNIQUE NOT NULL,
    titre VARCHAR(255) NOT NULL,
    titre_complet VARCHAR(500),
    prix DECIMAL(12,2),
    prix_detaille VARCHAR(100),
    prix_au_m2 DECIMAL(10,2),
    localisation VARCHAR(255),
    localisation_complete VARCHAR(500),
    surface DECIMAL(8,2),
    surface_terrain DECIMAL(8,2),
    pieces INTEGER,
    type_bien VARCHAR(100),
    description TEXT,
    annee_construction INTEGER,
    honoraires VARCHAR(100),
    image_url VARCHAR(500),
    nombre_photos INTEGER DEFAULT 0,
    has_video BOOLEAN DEFAULT FALSE,
    has_visite_virtuelle BOOLEAN DEFAULT FALSE,
    media_info VARCHAR(255),
    lien VARCHAR(500),
    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dpe_classe_active VARCHAR(1),
    ges_classe_active VARCHAR(1),
    depenses_energie_min VARCHAR(50),
    depenses_energie_max VARCHAR(50),
    annee_reference INTEGER
);

-- Création de la table CARACTERISTIQUE
CREATE TABLE caracteristiques (
    id_caracteristique SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    valeur VARCHAR(255) NOT NULL
);

-- Création de la table IMAGE
CREATE TABLE images (
    id_image SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    ordre INTEGER DEFAULT 0
);

-- Création de la table COPROPRIETE
CREATE TABLE copropriete (
    id_copropriete SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    nb_lots INTEGER,
    charges_previsionnelles VARCHAR(100),
    procedures VARCHAR(255)
);

-- Création de la table CONSEILLER
CREATE TABLE conseiller (
    id_conseiller SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    nom_complet VARCHAR(255),
    telephone VARCHAR(20),
    lien VARCHAR(500),
    photo VARCHAR(500),
    note VARCHAR(50)
);

-- Création de la table DPE
CREATE TABLE dpe (
    id_dpe SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    classe_energie VARCHAR(1),
    indice_energie INTEGER,
    classe_climat VARCHAR(1),
    indice_climat INTEGER
);

-- =============================================
-- INDEX
-- =============================================

-- Index pour la table annonces
CREATE INDEX idx_annonces_prix ON annonces(prix);
CREATE INDEX idx_annonces_localisation ON annonces(localisation);
CREATE INDEX idx_annonces_surface ON annonces(surface);
CREATE INDEX idx_annonces_type ON annonces(type_bien);
CREATE INDEX idx_annonces_dpe ON annonces(dpe_classe_active);
CREATE INDEX idx_annonces_reference ON annonces(reference);
CREATE INDEX idx_annonces_date_extraction ON annonces(date_extraction);

-- Index pour les tables liées
CREATE INDEX idx_caracteristiques_annonce ON caracteristiques(id_annonce);
CREATE INDEX idx_images_annonce ON images(id_annonce);
CREATE INDEX idx_copropriete_annonce ON copropriete(id_annonce);
CREATE INDEX idx_conseiller_annonce ON conseiller(id_annonce);
CREATE INDEX idx_dpe_annonce ON dpe(id_annonce);

-- =============================================
-- CONTRAINTES
-- =============================================

-- Contraintes pour la table annonces
ALTER TABLE annonces ADD CONSTRAINT chk_prix_positif CHECK (prix > 0 OR prix IS NULL);
ALTER TABLE annonces ADD CONSTRAINT chk_surface_positif CHECK (surface > 0 OR surface IS NULL);
ALTER TABLE annonces ADD CONSTRAINT chk_surface_terrain_positif CHECK (surface_terrain > 0 OR surface_terrain IS NULL);
ALTER TABLE annonces ADD CONSTRAINT chk_pieces_positif CHECK (pieces > 0 OR pieces IS NULL);
ALTER TABLE annonces ADD CONSTRAINT chk_dpe_classe CHECK (dpe_classe_active IN ('A', 'B', 'C', 'D', 'E', 'F', 'G') OR dpe_classe_active IS NULL);
ALTER TABLE annonces ADD CONSTRAINT chk_ges_classe CHECK (ges_classe_active IN ('A', 'B', 'C', 'D', 'E', 'F', 'G') OR ges_classe_active IS NULL);

-- Contraintes pour la table DPE
ALTER TABLE dpe ADD CONSTRAINT chk_dpe_classe_energie CHECK (classe_energie IN ('A', 'B', 'C', 'D', 'E', 'F', 'G') OR classe_energie IS NULL);
ALTER TABLE dpe ADD CONSTRAINT chk_dpe_classe_climat CHECK (classe_climat IN ('A', 'B', 'C', 'D', 'E', 'F', 'G') OR classe_climat IS NULL);

-- =============================================
-- FONCTIONS
-- =============================================

CREATE OR REPLACE FUNCTION nettoyer_prix(prix_text VARCHAR)
RETURNS DECIMAL(12,2) AS $$
BEGIN
    RETURN NULLIF(REPLACE(REPLACE(REPLACE(COALESCE(prix_text, ''), '€', ''), ' ', ''), ' ', ''), '')::DECIMAL;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- VUES
-- =============================================

CREATE OR REPLACE VIEW annonces_complete AS
SELECT 
    a.*,
    c.nom_complet as conseiller_nom,
    c.telephone as conseiller_telephone,
    c.photo as conseiller_photo,
    c.note as conseiller_note,
    d.classe_energie,
    d.indice_energie,
    d.classe_climat,
    d.indice_climat,
    cp.nb_lots,
    cp.charges_previsionnelles,
    cp.procedures,
    CASE 
        WHEN a.prix_au_m2 IS NULL AND a.surface > 0 THEN ROUND(a.prix / a.surface, 2)
        ELSE a.prix_au_m2 
    END AS prix_au_m2_calcule
FROM annonces a
LEFT JOIN conseiller c ON a.id_annonce = c.id_annonce
LEFT JOIN dpe d ON a.id_annonce = d.id_annonce
LEFT JOIN copropriete cp ON a.id_annonce = cp.id_annonce
WHERE a.prix IS NOT NULL AND a.surface IS NOT NULL;

CREATE OR REPLACE VIEW v_stats_type_bien AS
SELECT
    type_bien,
    COUNT(*) AS nombre_annonces,
    ROUND(AVG(prix), 2) AS prix_moyen,
    ROUND(AVG(prix_au_m2), 2) AS prix_m2_moyen,
    ROUND(MIN(prix), 2) AS prix_min,
    ROUND(MAX(prix), 2) AS prix_max
FROM annonces
WHERE prix IS NOT NULL
GROUP BY type_bien
ORDER BY nombre_annonces DESC;

CREATE OR REPLACE VIEW v_stats_localisation AS
SELECT
    localisation,
    COUNT(*) AS nombre_annonces,
    ROUND(AVG(prix), 2) AS prix_moyen,
    ROUND(AVG(surface), 2) AS surface_moyenne
FROM annonces
GROUP BY localisation
ORDER BY prix_moyen DESC;

CREATE OR REPLACE VIEW v_stats_dpe AS
SELECT
    d.classe_energie,
    COUNT(*) AS nombre_annonces,
    ROUND(AVG(a.prix), 2) AS prix_moyen,
    ROUND(AVG(d.indice_energie), 2) AS indice_energie_moyen
FROM annonces a
JOIN dpe d ON a.id_annonce = d.id_annonce
WHERE d.classe_energie IS NOT NULL
GROUP BY d.classe_energie
ORDER BY d.classe_energie;

CREATE OR REPLACE VIEW v_stats_pieces AS
SELECT
    pieces,
    COUNT(*) AS nombre_annonces,
    ROUND(AVG(prix), 2) AS prix_moyen,
    ROUND(AVG(surface), 2) AS surface_moyenne
FROM annonces
WHERE pieces IS NOT NULL
GROUP BY pieces
ORDER BY pieces;

-- Vue pour les caractéristiques
CREATE OR REPLACE VIEW v_annonces_caracteristiques AS
SELECT 
    a.id_annonce,
    a.reference,
    a.titre,
    a.prix,
    STRING_AGG(c.valeur, ', ') AS caracteristiques
FROM annonces a
LEFT JOIN caracteristiques c ON a.id_annonce = c.id_annonce
GROUP BY a.id_annonce, a.reference, a.titre, a.prix;

SELECT '=== SCRIPT EXECUTE AVEC SUCCES ===' as final_status;