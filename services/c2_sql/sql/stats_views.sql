-- =============================================
-- VUES STATISTIQUES POUR LA BASE IMMOBILIÈRE
-- =============================================

-- 1. STATISTIQUES GÉNÉRALES PAR TYPE DE BIEN
CREATE OR REPLACE VIEW v_stats_type_bien AS
SELECT
    type_bien,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    ROUND(AVG(prix_au_m2)::numeric, 2) as prix_m2_moyen,
    ROUND(MIN(prix)::numeric, 2) as prix_min,
    ROUND(MAX(prix)::numeric, 2) as prix_max,
    ROUND(AVG(surface)::numeric, 2) as surface_moyenne,
    ROUND(AVG(pieces)::numeric, 1) as pieces_moyennes
FROM annonces
WHERE prix IS NOT NULL AND surface IS NOT NULL
GROUP BY type_bien
ORDER BY nombre_annonces DESC;

-- 2. ÉVOLUTION DES PRIX AU M² PAR MOIS
CREATE OR REPLACE VIEW v_stats_prix_m2_par_mois AS
SELECT
    DATE_TRUNC('month', date_extraction) as mois,
    type_bien,
    ROUND(AVG(prix_au_m2)::numeric, 2) as prix_m2_moyen,
    COUNT(*) as nombre_annonces
FROM annonces
WHERE prix_au_m2 IS NOT NULL
GROUP BY DATE_TRUNC('month', date_extraction), type_bien
ORDER BY mois DESC, type_bien;

-- 3. TOP 10 DES COMMUNES LES PLUS CHÈRES
CREATE OR REPLACE VIEW v_stats_communes_cheres AS
SELECT
    localisation,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    ROUND(AVG(prix_au_m2)::numeric, 2) as prix_m2_moyen,
    ROUND(AVG(surface)::numeric, 2) as surface_moyenne
FROM annonces
WHERE prix IS NOT NULL AND localisation IS NOT NULL
GROUP BY localisation
HAVING COUNT(*) >= 5
ORDER BY prix_m2_moyen DESC
LIMIT 10;

-- 4. DISTRIBUTION DES SURFACES PAR TYPE DE BIEN
CREATE OR REPLACE VIEW v_stats_distribution_surfaces AS
SELECT
    type_bien,
    COUNT(*) as total,
    ROUND(AVG(surface)::numeric, 2) as moyenne,
    ROUND(MIN(surface)::numeric, 2) as minimum,
    ROUND(MAX(surface)::numeric, 2) as maximum,
    ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY surface))::numeric, 2) as mediane
FROM annonces
WHERE surface IS NOT NULL AND surface > 0
GROUP BY type_bien
ORDER BY total DESC;

-- 5. PERFORMANCE ÉNERGÉTIQUE (DPE) DES BIENS
CREATE OR REPLACE VIEW v_stats_performance_energetique AS
SELECT
    d.classe_energie,
    COUNT(*) as nombre_biens,
    ROUND(AVG(a.prix)::numeric, 2) as prix_moyen,
    ROUND(AVG(a.prix_au_m2)::numeric, 2) as prix_m2_moyen,
    ROUND(AVG(a.surface)::numeric, 2) as surface_moyenne
FROM annonces a
JOIN dpe d ON a.id_annonce = d.id_annonce
WHERE d.classe_energie IS NOT NULL
GROUP BY d.classe_energie
ORDER BY 
    CASE d.classe_energie
        WHEN 'A' THEN 1
        WHEN 'B' THEN 2
        WHEN 'C' THEN 3
        WHEN 'D' THEN 4
        WHEN 'E' THEN 5
        WHEN 'F' THEN 6
        WHEN 'G' THEN 7
        ELSE 8
    END;

-- 6. STATISTIQUES PAR NOMBRE DE PIÈCES
CREATE OR REPLACE VIEW v_stats_par_pieces AS
SELECT
    pieces,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    ROUND(AVG(surface)::numeric, 2) as surface_moyenne,
    ROUND(AVG(prix_au_m2)::numeric, 2) as prix_m2_moyen
FROM annonces
WHERE pieces IS NOT NULL AND pieces > 0
GROUP BY pieces
HAVING COUNT(*) >= 3
ORDER BY pieces;

-- 7. CARACTÉRISTIQUES LES PLUS FRÉQUENTES
CREATE OR REPLACE VIEW v_stats_caracteristiques_populaires AS
SELECT
    valeur as caracteristique,
    COUNT(*) as frequence,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(DISTINCT id_annonce) FROM caracteristiques))::numeric, 2) as pourcentage
FROM caracteristiques
GROUP BY valeur
ORDER BY frequence DESC
LIMIT 20;

-- 8. CORRÉLATION ENTRE ANNÉE DE CONSTRUCTION ET PRIX
CREATE OR REPLACE VIEW v_stats_annee_construction AS
SELECT
    periode_construction,
    COUNT(*) as nombre_biens,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    ROUND(AVG(prix_au_m2)::numeric, 2) as prix_m2_moyen
FROM (
    SELECT 
        prix,
        prix_au_m2,
        CASE 
            WHEN annee_construction < 1900 THEN 'Avant 1900'
            WHEN annee_construction BETWEEN 1900 AND 1945 THEN '1900-1945'
            WHEN annee_construction BETWEEN 1946 AND 1970 THEN '1946-1970'
            WHEN annee_construction BETWEEN 1971 AND 1990 THEN '1971-1990'
            WHEN annee_construction BETWEEN 1991 AND 2010 THEN '1991-2010'
            WHEN annee_construction > 2010 THEN 'Après 2010'
            ELSE 'Non renseigné'
        END as periode_construction
    FROM annonces
    WHERE prix IS NOT NULL
) as subquery
GROUP BY periode_construction
ORDER BY 
    CASE periode_construction
        WHEN 'Avant 1900' THEN 1
        WHEN '1900-1945' THEN 2
        WHEN '1946-1970' THEN 3
        WHEN '1971-1990' THEN 4
        WHEN '1991-2010' THEN 5
        WHEN 'Après 2010' THEN 6
        ELSE 7
    END;

-- 9. STATISTIQUES DES COPROPRIÉTÉS
CREATE OR REPLACE VIEW v_stats_coproprietes AS
SELECT
    taille_copropriete,
    COUNT(*) as nombre_biens,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    ROUND(AVG(lots_moyens)::numeric, 1) as lots_moyens
FROM (
    SELECT 
        a.prix,
        cp.nb_lots,
        CASE 
            WHEN cp.nb_lots < 10 THEN 'Petite (1-9 lots)'
            WHEN cp.nb_lots BETWEEN 10 AND 50 THEN 'Moyenne (10-50 lots)'
            WHEN cp.nb_lots > 50 THEN 'Grande (>50 lots)'
            ELSE 'Non renseigné'
        END as taille_copropriete,
        cp.nb_lots as lots_moyens
    FROM annonces a
    JOIN copropriete cp ON a.id_annonce = cp.id_annonce
    WHERE cp.nb_lots IS NOT NULL
) as subquery
GROUP BY taille_copropriete
ORDER BY nombre_biens DESC;

-- 10. QUALITÉ DES ANNONCES (PHOTOS, DESCRIPTIONS)
CREATE OR REPLACE VIEW v_stats_qualite_annonces AS
SELECT
    nb_photos,
    longueur_description,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen
FROM (
    SELECT
        prix,
        CASE 
            WHEN nombre_photos = 0 THEN 'Aucune photo'
            WHEN nombre_photos BETWEEN 1 AND 5 THEN '1-5 photos'
            WHEN nombre_photos BETWEEN 6 AND 10 THEN '6-10 photos'
            WHEN nombre_photos > 10 THEN 'Plus de 10 photos'
            ELSE 'Non renseigné'
        END as nb_photos,
        CASE 
            WHEN LENGTH(description) < 100 THEN 'Description courte'
            WHEN LENGTH(description) BETWEEN 100 AND 500 THEN 'Description moyenne'
            WHEN LENGTH(description) > 500 THEN 'Description détaillée'
            ELSE 'Pas de description'
        END as longueur_description
    FROM annonces
) as subquery
GROUP BY nb_photos, longueur_description
ORDER BY nombre_annonces DESC;

-- 11. RAPPORT SURFACE/PRIX PAR LOCALISATION
CREATE OR REPLACE VIEW v_stats_rapport_surface_prix AS
SELECT
    localisation,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(surface)::numeric, 2) as surface_moyenne,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    ROUND((AVG(prix) / NULLIF(AVG(surface), 0))::numeric, 2) as prix_m2_moyen,
    ROUND(MIN(prix_au_m2)::numeric, 2) as prix_m2_min,
    ROUND(MAX(prix_au_m2)::numeric, 2) as prix_m2_max
FROM annonces
WHERE prix IS NOT NULL AND surface IS NOT NULL AND localisation IS NOT NULL
GROUP BY localisation
HAVING COUNT(*) >= 3
ORDER BY prix_m2_moyen DESC;

-- 12. STATISTIQUES DES CONSEILLERS
CREATE OR REPLACE VIEW v_stats_conseillers AS
SELECT
    c.nom_complet,
    COUNT(*) as nombre_annonces,
    ROUND(AVG(a.prix)::numeric, 2) as prix_moyen_geres,
    ROUND(AVG(a.surface)::numeric, 2) as surface_moyenne_geres,
    MIN(a.date_extraction) as premiere_annonce,
    MAX(a.date_extraction) as derniere_annonce
FROM conseiller c
JOIN annonces a ON c.id_annonce = a.id_annonce
GROUP BY c.nom_complet
HAVING COUNT(*) >= 2
ORDER BY nombre_annonces DESC;

-- 13. SAISONNALITÉ DES MISE EN LIGNE
CREATE OR REPLACE VIEW v_stats_saisonnalite AS
SELECT
    EXTRACT(MONTH FROM date_extraction) as mois,
    TO_CHAR(date_extraction, 'Month') as nom_mois,
    COUNT(*) as nombre_nouvelles_annonces,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen
FROM annonces
GROUP BY EXTRACT(MONTH FROM date_extraction), TO_CHAR(date_extraction, 'Month')
ORDER BY mois;

-- 14. BIENS AVEC VISITES VIRTUELLES
CREATE OR REPLACE VIEW v_stats_visites_virtuelles AS
SELECT
    has_visite_virtuelle as visite_virtuelle_disponible,
    COUNT(*) as nombre_annonces,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM annonces))::numeric, 2) as pourcentage_total,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    ROUND(AVG(nombre_photos)::numeric, 1) as photos_moyennes
FROM annonces
GROUP BY has_visite_virtuelle
ORDER BY nombre_annonces DESC;

-- 15. COMPARAISON DPE ÉNERGIE/CLIMAT
CREATE OR REPLACE VIEW v_stats_comparaison_dpe AS
SELECT
    d.classe_energie,
    d.classe_climat,
    COUNT(*) as nombre_biens,
    ROUND(AVG(a.prix_au_m2)::numeric, 2) as prix_m2_moyen,
    ROUND(AVG(a.surface)::numeric, 2) as surface_moyenne
FROM annonces a
JOIN dpe d ON a.id_annonce = d.id_annonce
WHERE d.classe_energie IS NOT NULL AND d.classe_climat IS NOT NULL
GROUP BY d.classe_energie, d.classe_climat
ORDER BY d.classe_energie, d.classe_climat;

-- =============================================
-- VUE SYNTHÈSE GÉNÉRALE
-- =============================================

CREATE OR REPLACE VIEW v_synthese_generale AS
SELECT
    (SELECT COUNT(*) FROM annonces) as total_annonces,
    (SELECT COUNT(DISTINCT localisation) FROM annonces WHERE localisation IS NOT NULL) as communes_couvertes,
    (SELECT ROUND(AVG(prix)::numeric, 2) FROM annonces WHERE prix IS NOT NULL) as prix_moyen_general,
    (SELECT ROUND(AVG(prix_au_m2)::numeric, 2) FROM annonces WHERE prix_au_m2 IS NOT NULL) as prix_m2_moyen_general,
    (SELECT ROUND(AVG(surface)::numeric, 2) FROM annonces WHERE surface IS NOT NULL) as surface_moyenne_generale,
    (SELECT COUNT(*) FROM images) as total_photos,
    (SELECT COUNT(*) FROM conseiller) as total_conseillers,
    (SELECT MAX(date_extraction) FROM annonces) as derniere_mise_a_jour;

-- =============================================
-- AFFICHAGE DES VUES CRÉÉES
-- =============================================

SELECT 'Vues statistiques créées avec succès:' as statut;

SELECT table_name as vue_creee
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name LIKE 'v_stats%' OR table_name = 'v_synthese_generale'
ORDER BY table_name;