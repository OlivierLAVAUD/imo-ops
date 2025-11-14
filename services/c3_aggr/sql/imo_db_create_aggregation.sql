-- =============================================
-- SCRIPT SQL POUR LA STRUCTURE DES AGRÉGATS
-- =============================================

-- =============================================
-- VÉRIFICATION DE LA BASE
-- =============================================
SELECT 'Exécution dans la base: ' || current_database() as info;

-- =============================================
-- SUPPRESSION DES OBJETS EXISTANTS
-- =============================================

-- Supprimer les vues d'abord
DROP VIEW IF EXISTS v_aggregats_complets CASCADE;
DROP VIEW IF EXISTS v_stats_aggregats CASCADE;
DROP VIEW IF EXISTS v_recommandations_actives CASCADE;
DROP VIEW IF EXISTS v_biens_sous_cotes CASCADE;
DROP VIEW IF EXISTS v_biens_sur_cotes CASCADE;

-- Supprimer les fonctions
DROP FUNCTION IF EXISTS calculer_segment_marche CASCADE;
DROP FUNCTION IF EXISTS calculer_score_attractivite_avance CASCADE;
DROP FUNCTION IF EXISTS analyser_potentiel_renovation CASCADE;

-- Supprimer les tables d'agrégats
DROP TABLE IF EXISTS recommandations CASCADE;
DROP TABLE IF EXISTS analyse_marche CASCADE;
DROP TABLE IF EXISTS segmentation CASCADE;
DROP TABLE IF EXISTS scores_avances CASCADE;
DROP TABLE IF EXISTS performance_financiere CASCADE;
DROP TABLE IF EXISTS aggregats_principaux CASCADE;

-- =============================================
-- CRÉATION DES TABLES D'AGRÉGATS
-- =============================================

-- Table principale des agrégats
CREATE TABLE aggregats_principaux (
    id_aggregat SERIAL PRIMARY KEY,
    id_annonce INTEGER NOT NULL REFERENCES annonces(id_annonce) ON DELETE CASCADE,
    date_aggregation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithme_version VARCHAR(20) DEFAULT '2.0',
    score_global DECIMAL(3,1),
    segment_marche_global VARCHAR(100),
    statut_optimisation VARCHAR(50) DEFAULT 'a_analyser'
);

-- Table de performance financière
CREATE TABLE performance_financiere (
    id_performance SERIAL PRIMARY KEY,
    id_aggregat INTEGER NOT NULL REFERENCES aggregats_principaux(id_aggregat) ON DELETE CASCADE,
    prix_m2_calcule DECIMAL(10,2),
    loyer_estime_mensuel DECIMAL(10,2),
    rendement_annuel_estime DECIMAL(5,2),
    rentabilite_nette DECIMAL(5,2),
    charges_annuelles DECIMAL(8,2),
    ratio_rentabilite VARCHAR(20),
    niveau_rendement VARCHAR(30) -- 'faible', 'moyen', 'eleve'
);

-- Table des scores avancés
CREATE TABLE scores_avances (
    id_score SERIAL PRIMARY KEY,
    id_aggregat INTEGER NOT NULL REFERENCES aggregats_principaux(id_aggregat) ON DELETE CASCADE,
    score_emplacement DECIMAL(3,1),
    score_modernite DECIMAL(3,1),
    score_dpe DECIMAL(3,1),
    score_equipements DECIMAL(3,1),
    score_accessibilite DECIMAL(3,1),
    score_medias DECIMAL(3,1),
    ponderation_emplacement DECIMAL(3,2) DEFAULT 0.20,
    ponderation_modernite DECIMAL(3,2) DEFAULT 0.15,
    ponderation_dpe DECIMAL(3,2) DEFAULT 0.15,
    ponderation_equipements DECIMAL(3,2) DEFAULT 0.10
);

-- Table de segmentation
CREATE TABLE segmentation (
    id_segmentation SERIAL PRIMARY KEY,
    id_aggregat INTEGER NOT NULL REFERENCES aggregats_principaux(id_aggregat) ON DELETE CASCADE,
    segment_prix_m2 VARCHAR(50), -- 'economique', 'moyen', 'superieur', 'premium', 'luxe'
    segment_surface VARCHAR(50), -- 'studio', 'appartement', 'grand_appartement', 'maison', 'grande_maison'
    segment_age VARCHAR(50), -- 'neuf', 'recent', 'ancien', 'tres_ancien', 'patrimoine'
    segment_cible VARCHAR(100), -- 'jeunes_actifs', 'familles', 'investisseurs', 'seniors'
    segment_potentiel VARCHAR(50) -- 'standard', 'valorisation', 'renovation'
);

-- Table d'analyse de marché
CREATE TABLE analyse_marche (
    id_analyse SERIAL PRIMARY KEY,
    id_aggregat INTEGER NOT NULL REFERENCES aggregats_principaux(id_aggregat) ON DELETE CASCADE,
    positionnement_marche VARCHAR(50), -- 'tres_sous_cote', 'sous_cote', 'dans_la_moyenne', 'sur_cote', 'tres_sur_cote'
    z_score_prix_m2 DECIMAL(5,2),
    ecart_pourcentage DECIMAL(5,2),
    prix_m2_marche_reference DECIMAL(10,2),
    nombre_biens_reference INTEGER,
    ecart_type_marche DECIMAL(10,2),
    rang_percentile INTEGER
);

-- Table des recommandations
CREATE TABLE recommandations (
    id_recommandation SERIAL PRIMARY KEY,
    id_aggregat INTEGER NOT NULL REFERENCES aggregats_principaux(id_aggregat) ON DELETE CASCADE,
    type_recommandation VARCHAR(50), -- 'prix', 'marketing', 'amelioration', 'ciblage'
    priorite VARCHAR(20), -- 'basse', 'moyenne', 'haute', 'critique'
    description TEXT,
    action_concrete TEXT,
    impact_estime VARCHAR(30), -- 'faible', 'moyen', 'important'
    delai_recommandation VARCHAR(30) -- 'immediat', 'court_terme', 'moyen_terme'
);

-- =============================================
-- TABLE DES STATISTIQUES DE MARCHÉ (GLOBALES)
-- =============================================

CREATE TABLE stats_marche_globales (
    id_stats SERIAL PRIMARY KEY,
    date_calcul TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    periode VARCHAR(20) DEFAULT 'mensuel',
    nombre_total_annonces INTEGER,
    prix_m2_moyen DECIMAL(10,2),
    prix_m2_median DECIMAL(10,2),
    prix_m2_min DECIMAL(10,2),
    prix_m2_max DECIMAL(10,2),
    ecart_type_prix_m2 DECIMAL(10,2),
    surface_moyenne DECIMAL(8,2),
    prix_moyen DECIMAL(12,2),
    
    -- Distribution par segments
    distribution_economique INTEGER,
    distribution_moyen INTEGER,
    distribution_superieur INTEGER,
    distribution_premium INTEGER,
    distribution_luxe INTEGER,
    
    -- Métadonnées
    arrondissements_couverts TEXT[],
    types_biens_analysees TEXT[]
);

-- =============================================
-- INDEX POUR LES PERFORMANCES
-- =============================================

-- Index pour la table aggregats_principaux
CREATE INDEX idx_aggregats_score_global ON aggregats_principaux(score_global);
CREATE INDEX idx_aggregats_segment ON aggregats_principaux(segment_marche_global);
CREATE INDEX idx_aggregats_date ON aggregats_principaux(date_aggregation);
CREATE INDEX idx_aggregats_annonce ON aggregats_principaux(id_annonce);

-- Index pour la table performance_financiere
CREATE INDEX idx_performance_prix_m2 ON performance_financiere(prix_m2_calcule);
CREATE INDEX idx_performance_rendement ON performance_financiere(rendement_annuel_estime);
CREATE INDEX idx_performance_aggregat ON performance_financiere(id_aggregat);

-- Index pour la table scores_avances
CREATE INDEX idx_scores_emplacement ON scores_avances(score_emplacement);
CREATE INDEX idx_scores_modernite ON scores_avances(score_modernite);
CREATE INDEX idx_scores_aggregat ON scores_avances(id_aggregat);

-- Index pour la table segmentation
CREATE INDEX idx_segmentation_prix ON segmentation(segment_prix_m2);
CREATE INDEX idx_segmentation_surface ON segmentation(segment_surface);
CREATE INDEX idx_segmentation_cible ON segmentation(segment_cible);
CREATE INDEX idx_segmentation_aggregat ON segmentation(id_aggregat);

-- Index pour la table analyse_marche
CREATE INDEX idx_analyse_positionnement ON analyse_marche(positionnement_marche);
CREATE INDEX idx_analyse_zscore ON analyse_marche(z_score_prix_m2);
CREATE INDEX idx_analyse_aggregat ON analyse_marche(id_aggregat);

-- Index pour la table recommandations
CREATE INDEX idx_recommandations_type ON recommandations(type_recommandation);
CREATE INDEX idx_recommandations_priorite ON recommandations(priorite);
CREATE INDEX idx_recommandations_aggregat ON recommandations(id_aggregat);

-- Index pour les stats globales
CREATE INDEX idx_stats_date ON stats_marche_globales(date_calcul);

-- =============================================
-- CONTRAINTES D'INTÉGRITÉ
-- =============================================

-- Contraintes pour aggregats_principaux
ALTER TABLE aggregats_principaux ADD CONSTRAINT chk_score_global CHECK (score_global BETWEEN 0 AND 10 OR score_global IS NULL);

-- Contraintes pour performance_financiere
ALTER TABLE performance_financiere ADD CONSTRAINT chk_prix_m2_positif CHECK (prix_m2_calcule > 0 OR prix_m2_calcule IS NULL);
ALTER TABLE performance_financiere ADD CONSTRAINT chk_rendement_positif CHECK (rendement_annuel_estime >= 0 OR rendement_annuel_estime IS NULL);

-- Contraintes pour scores_avances
ALTER TABLE scores_avances ADD CONSTRAINT chk_scores_range CHECK (
    score_emplacement BETWEEN 0 AND 10 AND
    score_modernite BETWEEN 0 AND 10 AND
    score_dpe BETWEEN 0 AND 10 AND
    score_equipements BETWEEN 0 AND 10 AND
    score_accessibilite BETWEEN 0 AND 10 AND
    score_medias BETWEEN 0 AND 10
);

-- Contraintes pour segmentation
ALTER TABLE segmentation ADD CONSTRAINT chk_segment_prix CHECK (segment_prix_m2 IN ('economique', 'moyen', 'superieur', 'premium', 'luxe') OR segment_prix_m2 IS NULL);
ALTER TABLE segmentation ADD CONSTRAINT chk_segment_surface CHECK (segment_surface IN ('studio', 'appartement', 'grand_appartement', 'maison', 'grande_maison') OR segment_surface IS NULL);
ALTER TABLE segmentation ADD CONSTRAINT chk_segment_age CHECK (segment_age IN ('neuf', 'recent', 'ancien', 'tres_ancien', 'patrimoine') OR segment_age IS NULL);

-- Contraintes pour analyse_marche
ALTER TABLE analyse_marche ADD CONSTRAINT chk_positionnement CHECK (
    positionnement_marche IN ('tres_sous_cote', 'sous_cote', 'dans_la_moyenne', 'sur_cote', 'tres_sur_cote', 'non_determine') 
    OR positionnement_marche IS NULL
);

-- Contraintes pour recommandations
ALTER TABLE recommandations ADD CONSTRAINT chk_priorite CHECK (priorite IN ('basse', 'moyenne', 'haute', 'critique'));
ALTER TABLE recommandations ADD CONSTRAINT chk_type_recommandation CHECK (type_recommandation IN ('prix', 'marketing', 'amelioration', 'ciblage'));

-- =============================================
-- FONCTIONS AVANCÉES POUR L'ANALYSE
-- =============================================

-- Fonction pour calculer le segment de marché global
CREATE OR REPLACE FUNCTION calculer_segment_marche(
    p_prix_m2 DECIMAL,
    p_surface DECIMAL,
    p_age INTEGER,
    p_dpe_score INTEGER
) RETURNS VARCHAR(100) AS $$
DECLARE
    segment_prix VARCHAR(50);
    segment_surface VARCHAR(50);
    segment_final VARCHAR(100);
BEGIN
    -- Segmentation par prix
    IF p_prix_m2 < 5000 THEN segment_prix := 'economique';
    ELSIF p_prix_m2 < 7000 THEN segment_prix := 'moyen';
    ELSIF p_prix_m2 < 10000 THEN segment_prix := 'superieur';
    ELSIF p_prix_m2 < 15000 THEN segment_prix := 'premium';
    ELSE segment_prix := 'luxe';
    END IF;
    
    -- Segmentation par surface
    IF p_surface < 30 THEN segment_surface := 'studio';
    ELSIF p_surface < 50 THEN segment_surface := 'appartement';
    ELSIF p_surface < 80 THEN segment_surface := 'grand_appartement';
    ELSIF p_surface < 120 THEN segment_surface := 'maison';
    ELSE segment_surface := 'grande_maison';
    END IF;
    
    -- Détermination du segment final
    IF p_dpe_score <= 3 THEN
        segment_final := segment_prix || '_' || segment_surface || '_renovation';
    ELSIF p_age > 50 THEN
        segment_final := segment_prix || '_' || segment_surface || '_ancien';
    ELSE
        segment_final := segment_prix || '_' || segment_surface || '_standard';
    END IF;
    
    RETURN segment_final;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer le score d'attractivité avancé
CREATE OR REPLACE FUNCTION calculer_score_attractivite_avance(
    p_score_emplacement DECIMAL,
    p_score_modernite DECIMAL,
    p_score_dpe DECIMAL,
    p_score_equipements DECIMAL,
    p_ponderation_emplacement DECIMAL DEFAULT 0.20,
    p_ponderation_modernite DECIMAL DEFAULT 0.15,
    p_ponderation_dpe DECIMAL DEFAULT 0.15,
    p_ponderation_equipements DECIMAL DEFAULT 0.10
) RETURNS DECIMAL(3,1) AS $$
DECLARE
    score_calcule DECIMAL(5,2);
BEGIN
    score_calcule := 
        (p_score_emplacement * p_ponderation_emplacement) +
        (p_score_modernite * p_ponderation_modernite) +
        (p_score_dpe * p_ponderation_dpe) +
        (p_score_equipements * p_ponderation_equipements);
    
    -- Normalisation sur 10
    score_calcule := (score_calcule / (p_ponderation_emplacement + p_ponderation_modernite + p_ponderation_dpe + p_ponderation_equipements)) * 10;
    
    RETURN ROUND(GREATEST(0, LEAST(10, score_calcule)), 1);
END;
$$ LANGUAGE plpgsql;

-- Fonction pour analyser le potentiel de rénovation
CREATE OR REPLACE FUNCTION analyser_potentiel_renovation(
    p_dpe_classe VARCHAR,
    p_age_bien INTEGER,
    p_prix DECIMAL
) RETURNS TABLE (
    potentiel VARCHAR(50),
    gain_valeur_estime DECIMAL(5,3),
    investissement_estime DECIMAL(10,2)
) AS $$
BEGIN
    IF p_dpe_classe IN ('F', 'G') AND p_age_bien > 30 THEN
        potentiel := 'eleve';
        gain_valeur_estime := 0.15; -- +15% de valeur potentielle
        investissement_estime := p_prix * 0.10; -- 10% du prix
    ELSIF p_dpe_classe = 'E' THEN
        potentiel := 'moyen';
        gain_valeur_estime := 0.08;
        investissement_estime := p_prix * 0.06;
    ELSE
        potentiel := 'faible';
        gain_valeur_estime := 0.02;
        investissement_estime := p_prix * 0.02;
    END IF;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- VUES POUR L'ANALYSE DES AGRÉGATS
-- =============================================

-- Vue complète des agrégats
CREATE OR REPLACE VIEW v_aggregats_complets AS
SELECT 
    a.reference,
    a.titre,
    ap.score_global,
    ap.segment_marche_global,
    ap.statut_optimisation,
    
    -- Performance financière
    pf.prix_m2_calcule,
    pf.loyer_estime_mensuel,
    pf.rendement_annuel_estime,
    pf.niveau_rendement,
    
    -- Scores
    sa.score_emplacement,
    sa.score_modernite,
    sa.score_dpe,
    
    -- Segmentation
    s.segment_prix_m2,
    s.segment_surface,
    s.segment_cible,
    
    -- Analyse marché
    am.positionnement_marche,
    am.ecart_pourcentage,
    am.z_score_prix_m2,
    
    -- Localisation
    l.ville,
    l.code_postal,
    l.quartier
    
FROM aggregats_principaux ap
JOIN annonces a ON ap.id_annonce = a.id_annonce
LEFT JOIN performance_financiere pf ON ap.id_aggregat = pf.id_aggregat
LEFT JOIN scores_avances sa ON ap.id_aggregat = sa.id_aggregat
LEFT JOIN segmentation s ON ap.id_aggregat = s.id_aggregat
LEFT JOIN analyse_marche am ON ap.id_aggregat = am.id_aggregat
LEFT JOIN localisation l ON a.id_annonce = l.id_annonce;

-- Vue des statistiques des agrégats
CREATE OR REPLACE VIEW v_stats_aggregats AS
SELECT
    COUNT(*) as total_aggregats,
    ROUND(AVG(score_global), 2) as score_global_moyen,
    ROUND(AVG(prix_m2_calcule), 2) as prix_m2_moyen,
    ROUND(AVG(rendement_annuel_estime), 2) as rendement_moyen,
    
    -- Distribution des segments
    COUNT(CASE WHEN segment_prix_m2 = 'economique' THEN 1 END) as nb_economique,
    COUNT(CASE WHEN segment_prix_m2 = 'moyen' THEN 1 END) as nb_moyen,
    COUNT(CASE WHEN segment_prix_m2 = 'superieur' THEN 1 END) as nb_superieur,
    COUNT(CASE WHEN segment_prix_m2 = 'premium' THEN 1 END) as nb_premium,
    COUNT(CASE WHEN segment_prix_m2 = 'luxe' THEN 1 END) as nb_luxe,
    
    -- Distribution positionnement
    COUNT(CASE WHEN positionnement_marche = 'tres_sous_cote' THEN 1 END) as nb_tres_sous_cote,
    COUNT(CASE WHEN positionnement_marche = 'sous_cote' THEN 1 END) as nb_sous_cote,
    COUNT(CASE WHEN positionnement_marche = 'dans_la_moyenne' THEN 1 END) as nb_moyenne,
    COUNT(CASE WHEN positionnement_marche = 'sur_cote' THEN 1 END) as nb_sur_cote,
    COUNT(CASE WHEN positionnement_marche = 'tres_sur_cote' THEN 1 END) as nb_tres_sur_cote
    
FROM v_aggregats_complets;

-- Vue des recommandations actives
CREATE OR REPLACE VIEW v_recommandations_actives AS
SELECT 
    a.reference,
    a.titre,
    r.type_recommandation,
    r.priorite,
    r.description,
    r.action_concrete,
    ap.score_global
FROM recommandations r
JOIN aggregats_principaux ap ON r.id_aggregat = ap.id_aggregat
JOIN annonces a ON ap.id_annonce = a.id_annonce
WHERE r.priorite IN ('haute', 'critique')
ORDER BY r.priorite DESC, ap.score_global DESC;

-- Vue des biens sous-cotés
CREATE OR REPLACE VIEW v_biens_sous_cotes AS
SELECT 
    reference,
    titre,
    prix_m2_calcule,
    prix_m2_marche_reference,
    ecart_pourcentage,
    score_global,
    segment_marche_global
FROM v_aggregats_complets
WHERE positionnement_marche IN ('tres_sous_cote', 'sous_cote')
ORDER BY ecart_pourcentage ASC;

-- Vue des biens sur-cotés
CREATE OR REPLACE VIEW v_biens_sur_cotes AS
SELECT 
    reference,
    titre,
    prix_m2_calcule,
    prix_m2_marche_reference,
    ecart_pourcentage,
    score_global,
    segment_marche_global
FROM v_aggregats_complets
WHERE positionnement_marche IN ('tres_sur_cote', 'sur_cote')
ORDER BY ecart_pourcentage DESC;

-- =============================================
-- FIN DU SCRIPT
-- =============================================

SELECT '=== STRUCTURE DES AGRÉGATS CRÉÉE AVEC SUCCÈS ===' as final_status;
SELECT 'Tables créées: aggregats_principaux, performance_financiere, scores_avances, segmentation, analyse_marche, recommandations, stats_marche_globales' as tables_created;
SELECT 'Vues créées: v_aggregats_complets, v_stats_aggregats, v_recommandations_actives, v_biens_sous_cotes, v_biens_sur_cotes' as views_created;
SELECT 'Fonctions créées: calculer_segment_marche, calculer_score_attractivite_avance, analyser_potentiel_renovation' as functions_created;