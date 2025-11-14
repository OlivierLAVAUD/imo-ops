#📊 Tableau de Bord Statistique Immobilier


# Installation

```bash
# Création des vues dans la base
psql -d imo_db -f stats_views.sql
```

# 📈 Vues Statistiques Disponibles

Le projet inclut 15 vues statistiques :
| Vue | Description |
|-----|-------------|
| v_stats_type_bien | Stats par type de bien (maison, appartement...) |
| v_stats_prix_m2_par_mois | Évolution temporelle des prix |
| v_stats_communes_cheres | Top 10 des communes les plus chères |
| v_stats_distribution_surfaces | Distribution des surfaces |
| v_stats_performance_energetique | Analyse DPE |
| v_stats_par_pieces | Stats par nombre de pièces |
| v_stats_caracteristiques_populaires | Caractéristiques les plus fréquentes |
| v_stats_annee_construction | Corrélation année/prix |
| v_stats_coproprietes | Analyse des copropriétés |
| v_stats_qualite_annonces | Qualité des annonces (photos, descriptions) |
| v_stats_rapport_surface_prix | Rapport surface/prix par localisation |
| v_stats_conseillers | Performance des conseillers |
| v_stats_saisonnalite | Saisonnalité des mises en ligne |
| v_stats_visites_virtuelles | Analyse des visites virtuelles |
| v_stats_comparaison_dpe | Comparaison DPE énergie/climat |

# 📈 Scripts Sql
Voici les requêtes pour visualiser chaque vue statistique :


```bash
# 1. Vue d'ensemble générale

SELECT * FROM v_synthese_generale;

# 2. Statistiques par type de bien
SELECT * FROM v_stats_type_bien;
-- Ou avec filtrage
SELECT * FROM v_stats_type_bien WHERE nombre_annonces > 10;

# 3. Évolution des prix au m²
SELECT * FROM v_stats_prix_m2_par_mois 
WHERE type_bien = 'Appartement' 
ORDER BY mois DESC;

-- Tous les types de biens
SELECT * FROM v_stats_prix_m2_par_mois 
ORDER BY mois DESC, type_bien;

# 4. Communes les plus chères
SELECT * FROM v_stats_communes_cheres;

# 5. Distribution des surfaces
SELECT * FROM v_stats_distribution_surfaces;

# 6. Performance énergétique (DPE)
SELECT * FROM v_stats_performance_energetique;

# 7. Statistiques par nombre de pièces
SELECT * FROM v_stats_par_pieces 
WHERE pieces BETWEEN 1 AND 5;

# 8. Caractéristiques populaires
SELECT * FROM v_stats_caracteristiques_populaires;
-- Top 10 seulement
SELECT * FROM v_stats_caracteristiques_populaires LIMIT 10;

# 9. Corrélation année construction / prix
SELECT * FROM v_stats_annee_construction;

# 10. Statistiques copropriétés
SELECT * FROM v_stats_coproprietes;

# 11. Qualité des annonces
SELECT * FROM v_stats_qualite_annonces 
WHERE nombre_annonces > 5
ORDER BY nb_photos, longueur_description;

# 12. Rapport surface/prix par localisation
SELECT * FROM v_stats_rapport_surface_prix 
WHERE nombre_annonces > 10
ORDER BY prix_m2_moyen DESC;

#  13. Statistiques conseillers
SELECT * FROM v_stats_conseillers 
WHERE nombre_annonces > 5
ORDER BY nombre_annonces DESC;

#  14. Saisonnalité
SELECT * FROM v_stats_saisonnalite;

#  15. Visites virtuelles
SELECT * FROM v_stats_visites_virtuelles;

#  16. Comparaison DPE énergie/climat
SELECT * FROM v_stats_comparaison_dpe;

# Requêtes combinées
# Prix moyens par type et localisation

SELECT 
    type_bien,
    localisation,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen,
    COUNT(*) as nb_annonces
FROM annonces 
WHERE prix IS NOT NULL 
GROUP BY type_bien, localisation
HAVING COUNT(*) >= 5
ORDER BY type_bien, prix_moyen DESC;

# Top 5 des caractéristiques par type de bien

SELECT 
    a.type_bien,
    c.valeur as caracteristique,
    COUNT(*) as frequence
FROM caracteristiques c
JOIN annonces a ON c.id_annonce = a.id_annonce
GROUP BY a.type_bien, c.valeur
ORDER BY a.type_bien, frequence DESC;

# Évolution mensuelle du nombre d'annonces
SELECT 
    DATE_TRUNC('month', date_extraction) as mois,
    COUNT(*) as nouvelles_annonces,
    ROUND(AVG(prix)::numeric, 2) as prix_moyen
FROM annonces
GROUP BY DATE_TRUNC('month', date_extraction)
ORDER BY mois DESC;


# Performance des conseillers (top 10)
SELECT 
    nom_complet,
    nombre_annonces,
    prix_moyen_geres,
    surface_moyenne_geres
FROM v_stats_conseillers 
ORDER BY nombre_annonces DESC 
LIMIT 10;

# Comparaison DPE détaillée

SELECT 
    classe_energie,
    classe_climat,
    nombre_biens,
    prix_m2_moyen
FROM v_stats_comparaison_dpe
WHERE nombre_biens >= 10
ORDER BY classe_energie, classe_climat;

# Pour lister toutes les vues disponibles

SELECT table_name as nom_vue
FROM information_schema.views 
WHERE table_schema = 'public' 
ORDER BY table_name;
```