-- =============================================
-- VÉRIFICATION DE LA BASE
-- =============================================
SELECT 'Exécution dans la base: ' || current_database() as info;

-- =============================================
-- SUPPRESSION DES OBJETS EXISTANTS AVEC CASCADE
-- =============================================

-- Supprimer les vues d'abord (elles dépendent des tables)
DROP VIEW IF EXISTS v_stats_performance CASCADE;
DROP VIEW IF EXISTS v_stats_segmentation CASCADE;
DROP VIEW IF EXISTS v_stats_localisation CASCADE;
DROP VIEW IF EXISTS v_stats_dpe CASCADE;
DROP VIEW IF EXISTS annonces_aggregats CASCADE;
DROP VIEW IF EXISTS annonces_preparees CASCADE;

-- Supprimer les fonctions
DROP FUNCTION IF EXISTS calculer_score_attractivite CASCADE;
DROP FUNCTION IF EXISTS calculer_rentabilite CASCADE;

-- Supprimer les tables (l'ordre est important à cause des clés étrangères)
DROP TABLE IF EXISTS aggregats CASCADE;
DROP TABLE IF EXISTS medias CASCADE;
DROP TABLE IF EXISTS caracteristiques CASCADE;
DROP TABLE IF EXISTS copropriete CASCADE;
DROP TABLE IF EXISTS diagnostics CASCADE;
DROP TABLE IF EXISTS batiment CASCADE;
DROP TABLE IF EXISTS composition CASCADE;
DROP TABLE IF EXISTS localisation CASCADE;
DROP TABLE IF EXISTS prix CASCADE;
DROP TABLE IF EXISTS annonces CASCADE;

-- =============================================
-- CRÉATION DES TABLES PRINCIPALES
-- =============================================

-- Table principale ANNONCES
CREATE TABLE annonces (
    id_annonce SERIAL PRIMARY KEY,
    reference VARCHAR(50) UNIQUE NOT NULL,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    url_annonce VARCHAR(500),
    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score_qualite DECIMAL(3,1) DEFAULT 0,
    champs_manquants TEXT[],
    etapes_traitees TEXT[]
);

-- Module PRIX
CREATE TABLE prix (
    id_prix SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    valeur DECIMAL(12,2),
    devise VARCHAR(10) DEFAULT '€',
    au_m2 DECIMAL(10,2),
    loyer_estime_mensuel DECIMAL(10,2),
    rendement_annuel_estime DECIMAL(5,2)
);

-- Module SURFACE
CREATE TABLE surface (
    id_surface SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    valeur DECIMAL(8,2),
    unite VARCHAR(10) DEFAULT 'm²',
    surface_par_piece DECIMAL(6,2)
);

-- Module COMPOSITION
CREATE TABLE composition (
    id_composition SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    pieces INTEGER,
    chambres INTEGER,
    type_bien VARCHAR(100)
);

-- Module LOCALISATION
CREATE TABLE localisation (
    id_localisation SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    ville VARCHAR(100),
    code_postal VARCHAR(10),
    quartier VARCHAR(100),
    proximite TEXT,
    score_emplacement DECIMAL(3,1) DEFAULT 0
);

-- Module BÂTIMENT
CREATE TABLE batiment (
    id_batiment SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    annee_construction INTEGER,
    age_bien INTEGER,
    etage INTEGER,
    etage_total INTEGER,
    ascenseur BOOLEAN DEFAULT FALSE,
    score_modernite DECIMAL(3,1) DEFAULT 0
);

-- Module DIAGNOSTICS
CREATE TABLE diagnostics (
    id_diagnostics SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    dpe_classe VARCHAR(1),
    dpe_score INTEGER,
    dpe_indice INTEGER,
    ges_classe VARCHAR(1),
    ges_score INTEGER,
    ges_indice INTEGER
);

-- Module COPROPRIÉTÉ
CREATE TABLE copropriete (
    id_copropriete SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    nb_lots INTEGER,
    charges_valeur DECIMAL(8,2),
    charges_unite VARCHAR(20),
    charges_periode VARCHAR(20),
    procedures_en_cours BOOLEAN DEFAULT FALSE
);

-- Module CARACTÉRISTIQUES
CREATE TABLE caracteristiques (
    id_caracteristique SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    valeur VARCHAR(255) NOT NULL,
    categorie VARCHAR(50) DEFAULT 'autres'
);

-- Module MÉDIAS
CREATE TABLE medias (
    id_media SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    type_media VARCHAR(20) DEFAULT 'image',
    ordre INTEGER DEFAULT 0
);

-- Module CONTACT
CREATE TABLE contact (
    id_contact SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    conseiller_nom VARCHAR(255),
    conseiller_telephone VARCHAR(20),
    conseiller_photo VARCHAR(500),
    conseiller_lien VARCHAR(500)
);

-- =============================================
-- TABLE DES AGRÉGATS (Phase 2)
-- =============================================

CREATE TABLE aggregats (
    id_aggregat SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    
    -- Performance
    prix_m2_calcule DECIMAL(10,2),
    loyer_estime_mensuel DECIMAL(10,2),
    rendement_annuel_estime DECIMAL(5,2),
    rentabilite_nette DECIMAL(5,2),
    
    -- Scores
    score_emplacement DECIMAL(3,1),
    score_modernite DECIMAL(3,1),
    score_global DECIMAL(3,1),
    
    -- Segmentation
    segment_prix_m2 VARCHAR(50),
    segment_surface VARCHAR(50),
    segment_age VARCHAR(50),
    segment_marche VARCHAR(100),
    
    -- Analyse Marché
    positionnement_marche VARCHAR(50),
    z_score_prix_m2 DECIMAL(5,2),
    ecart_pourcentage DECIMAL(5,2),
    prix_m2_marche_reference DECIMAL(10,2),
    
    -- Potentiel
    potentiel_renovation VARCHAR(50),
    gain_valeur_estime DECIMAL(5,3),
    investissement_estime DECIMAL(10,2),
    
    -- Recommandations (stockées en JSON)
    recommandations_prix JSONB,
    recommandations_marketing JSONB,
    recommandations_amelioration JSONB,
    recommandations_ciblage JSONB,
    
    -- Métadonnées
    date_aggregation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithme_version VARCHAR(20)
);

-- =============================================
-- INDEX POUR LES PERFORMANCES
-- =============================================

-- Index pour la table annonces
CREATE INDEX idx_annonces_reference ON annonces(reference);
CREATE INDEX idx_annonces_score_qualite ON annonces(score_qualite);
CREATE INDEX idx_annonces_date_extraction ON annonces(date_extraction);

-- Index pour le module prix
CREATE INDEX idx_prix_valeur ON prix(valeur);
CREATE INDEX idx_prix_au_m2 ON prix(au_m2);

-- Index pour le module surface
CREATE INDEX idx_surface_valeur ON surface(valeur);

-- Index pour le module localisation
CREATE INDEX idx_localisation_code_postal ON localisation(code_postal);
CREATE INDEX idx_localisation_ville ON localisation(ville);

-- Index pour le module composition
CREATE INDEX idx_composition_type_bien ON composition(type_bien);
CREATE INDEX idx_composition_pieces ON composition(pieces);

-- Index pour le module batiment
CREATE INDEX idx_batiment_age ON batiment(age_bien);
CREATE INDEX idx_batiment_ascenseur ON batiment(ascenseur);

-- Index pour le module diagnostics
CREATE INDEX idx_diagnostics_dpe_score ON diagnostics(dpe_score);
CREATE INDEX idx_diagnostics_dpe_classe ON diagnostics(dpe_classe);

-- Index pour les agrégats
CREATE INDEX idx_aggregats_score_global ON aggregats(score_global);
CREATE INDEX idx_aggregats_positionnement ON aggregats(positionnement_marche);
CREATE INDEX idx_aggregats_segment ON aggregats(segment_marche);
CREATE INDEX idx_aggregats_prix_m2 ON aggregats(prix_m2_calcule);

-- Index pour les tables de liaison
CREATE INDEX idx_caracteristiques_annonce ON caracteristiques(id_annonce);
CREATE INDEX idx_medias_annonce ON medias(id_annonce);

-- =============================================
-- CONTRAINTES D'INTÉGRITÉ
-- =============================================

-- Contraintes pour la table prix
ALTER TABLE prix ADD CONSTRAINT chk_prix_positif CHECK (valeur > 0 OR valeur IS NULL);
ALTER TABLE prix ADD CONSTRAINT chk_prix_m2_positif CHECK (au_m2 > 0 OR au_m2 IS NULL);

-- Contraintes pour la table surface
ALTER TABLE surface ADD CONSTRAINT chk_surface_positif CHECK (valeur > 0 OR valeur IS NULL);

-- Contraintes pour la table composition
ALTER TABLE composition ADD CONSTRAINT chk_pieces_positif CHECK (pieces > 0 OR pieces IS NULL);
ALTER TABLE composition ADD CONSTRAINT chk_chambres_positif CHECK (chambres >= 0 OR chambres IS NULL);

-- Contraintes pour la table batiment
ALTER TABLE batiment ADD CONSTRAINT chk_age_bien_positif CHECK (age_bien >= 0 OR age_bien IS NULL);
ALTER TABLE batiment ADD CONSTRAINT chk_etage_positif CHECK (etage >= 0 OR etage IS NULL);

-- Contraintes pour la table diagnostics
ALTER TABLE diagnostics ADD CONSTRAINT chk_dpe_classe CHECK (dpe_classe IN ('A', 'B', 'C', 'D', 'E', 'F', 'G') OR dpe_classe IS NULL);
ALTER TABLE diagnostics ADD CONSTRAINT chk_ges_classe CHECK (ges_classe IN ('A', 'B', 'C', 'D', 'E', 'F', 'G') OR ges_classe IS NULL);
ALTER TABLE diagnostics ADD CONSTRAINT chk_dpe_score CHECK (dpe_score BETWEEN 0 AND 10 OR dpe_score IS NULL);
ALTER TABLE diagnostics ADD CONSTRAINT chk_ges_score CHECK (ges_score BETWEEN 0 AND 10 OR ges_score IS NULL);

-- Contraintes pour la table aggregats
ALTER TABLE aggregats ADD CONSTRAINT chk_scores CHECK (score_global BETWEEN 0 AND 10 OR score_global IS NULL);

-- =============================================
-- FONCTIONS UTILITAIRES
-- =============================================

-- Fonction pour calculer le score d'attractivité
CREATE OR REPLACE FUNCTION calculer_score_attractivite(
    p_dpe_score INTEGER,
    p_ascenseur BOOLEAN,
    p_etage INTEGER,
    p_age_bien INTEGER,
    p_nb_photos INTEGER
) RETURNS DECIMAL(3,1) AS $$
DECLARE
    score DECIMAL(3,1) := 5.0;
BEGIN
    -- Facteurs DPE
    IF p_dpe_score >= 6 THEN score := score + 2; END IF;
    IF p_dpe_score <= 3 THEN score := score - 2; END IF;
    
    -- Facteurs confort
    IF p_ascenseur THEN score := score + 1; END IF;
    IF p_etage = 1 THEN score := score + 1; END IF;
    
    -- Facteurs âge
    IF p_age_bien < 20 THEN score := score + 1; END IF;
    IF p_age_bien > 100 THEN score := score - 1; END IF;
    
    -- Facteurs médias
    IF p_nb_photos >= 5 THEN score := score + 1; END IF;
    
    -- Normalisation entre 1 et 10
    RETURN GREATEST(1, LEAST(10, score));
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer la rentabilité
CREATE OR REPLACE FUNCTION calculer_rentabilite(
    p_prix DECIMAL,
    p_prix_m2 DECIMAL,
    p_surface DECIMAL,
    p_charges DECIMAL
) RETURNS TABLE (
    loyer_estime DECIMAL,
    rendement_annuel DECIMAL,
    rentabilite_nette DECIMAL
) AS $$
BEGIN
    -- Calcul du loyer estimé (5% de rendement annuel)
    loyer_estime := (p_prix_m2 * p_surface * 0.05 / 12);
    
    -- Rendement annuel
    rendement_annuel := (loyer_estime * 12 / p_prix) * 100;
    
    -- Rentabilité nette (déduction des charges)
    IF p_charges IS NOT NULL THEN
        rentabilite_nette := GREATEST(0, rendement_annuel - (p_charges / p_prix * 100));
    ELSE
        rentabilite_nette := rendement_annuel;
    END IF;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- VUES POUR L'ANALYSE
-- =============================================

-- Vue complète des annonces préparées
CREATE OR REPLACE VIEW annonces_preparees AS
SELECT 
    a.id_annonce,
    a.reference,
    a.titre,
    a.score_qualite,
    
    -- Prix
    p.valeur as prix,
    p.au_m2 as prix_au_m2,
    
    -- Surface
    s.valeur as surface,
    s.surface_par_piece,
    
    -- Composition
    c.pieces,
    c.chambres,
    c.type_bien,
    
    -- Localisation
    l.ville,
    l.code_postal,
    l.quartier,
    l.proximite,
    l.score_emplacement,
    
    -- Bâtiment
    b.annee_construction,
    b.age_bien,
    b.etage,
    b.etage_total,
    b.ascenseur,
    b.score_modernite,
    
    -- Diagnostics
    d.dpe_classe,
    d.dpe_score,
    d.ges_classe,
    d.ges_score,
    
    -- Copropriété
    cp.nb_lots,
    cp.charges_valeur,
    cp.charges_unite,
    
    -- Contact
    co.conseiller_nom,
    co.conseiller_telephone
    
FROM annonces a
LEFT JOIN prix p ON a.id_annonce = p.id_annonce
LEFT JOIN surface s ON a.id_annonce = s.id_annonce
LEFT JOIN composition c ON a.id_annonce = c.id_annonce
LEFT JOIN localisation l ON a.id_annonce = l.id_annonce
LEFT JOIN batiment b ON a.id_annonce = b.id_annonce
LEFT JOIN diagnostics d ON a.id_annonce = d.id_annonce
LEFT JOIN copropriete cp ON a.id_annonce = cp.id_annonce
LEFT JOIN contact co ON a.id_annonce = co.id_annonce;

-- Vue des annonces avec agrégats
CREATE OR REPLACE VIEW annonces_aggregats AS
SELECT 
    ap.*,
    ag.score_global,
    ag.positionnement_marche,
    ag.segment_marche,
    ag.potentiel_renovation,
    ag.recommandations_prix
FROM annonces_preparees ap
JOIN aggregats ag ON ap.id_annonce = ag.id_annonce;

-- Vue des statistiques de performance
CREATE OR REPLACE VIEW v_stats_performance AS
SELECT
    COUNT(*) as total_annonces,
    ROUND(AVG(prix), 2) as prix_moyen,
    ROUND(AVG(prix_au_m2), 2) as prix_m2_moyen,
    ROUND(AVG(score_global), 2) as score_moyen,
    ROUND(AVG(rendement_annuel_estime), 2) as rendement_moyen
FROM annonces_aggregats;

-- Vue des statistiques par segmentation
CREATE OR REPLACE VIEW v_stats_segmentation AS
SELECT
    segment_marche,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(prix), 2) as prix_moyen,
    ROUND(AVG(score_global), 2) as score_moyen,
    ROUND(AVG(rendement_annuel_estime), 2) as rendement_moyen
FROM annonces_aggregats
WHERE segment_marche IS NOT NULL
GROUP BY segment_marche
ORDER BY nombre_annonces DESC;

-- Vue des statistiques DPE
CREATE OR REPLACE VIEW v_stats_dpe AS
SELECT
    dpe_classe,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(prix), 2) as prix_moyen,
    ROUND(AVG(prix_au_m2), 2) as prix_m2_moyen
FROM annonces_preparees
WHERE dpe_classe IS NOT NULL
GROUP BY dpe_classe
ORDER BY dpe_classe;

-- Vue des statistiques géographiques
CREATE OR REPLACE VIEW v_stats_localisation AS
SELECT
    code_postal,
    ville,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(prix), 2) as prix_moyen,
    ROUND(AVG(prix_au_m2), 2) as prix_m2_moyen
FROM annonces_preparees
WHERE code_postal IS NOT NULL
GROUP BY code_postal, ville
ORDER BY prix_m2_moyen DESC;

-- =============================================
-- FIN DU SCRIPT
-- =============================================

SELECT '=== STRUCTURE DE BASE DE DONNÉES CRÉÉE AVEC SUCCÈS ===' as final_status;
SELECT 'Tables créées: annonces, prix, surface, composition, localisation, batiment, diagnostics, copropriete, caracteristiques, medias, contact, aggregats' as tables_created;
SELECT 'Vues créées: annonces_preparees, annonces_aggregats, v_stats_performance, v_stats_segmentation, v_stats_dpe, v_stats_localisation' as views_created;