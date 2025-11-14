-- 1. Nombre total de commandes par client
CREATE OR REPLACE VIEW v1 AS
SELECT
    c.id_client,
    c.nom_client,
    COUNT(co.id_commande) AS nombre_commandes
FROM
    CLIENTS c
LEFT JOIN
    COMMANDES co ON c.id_client = co.id_client
GROUP BY
    c.id_client, c.nom_client
ORDER BY
    nombre_commandes DESC;

-- 2. Chiffre d'affaires total par client
CREATE OR REPLACE VIEW v2 AS
SELECT
    c.id_client,
    c.nom_client,
    SUM(lc.quantite * lc.prix_unitaire * (1 - lc.taux_remise)) AS chiffre_affaires
FROM
    CLIENTS c
JOIN
    COMMANDES co ON c.id_client = co.id_client
JOIN
    LIGNES_COMMANDE lc ON co.id_commande = lc.id_commande
GROUP BY
    c.id_client, c.nom_client
ORDER BY
    chiffre_affaires DESC;

-- 3. Chiffre d'affaires total par mois en 2024
CREATE OR REPLACE VIEW v3 AS
SELECT
    TO_CHAR(co.date_commande, 'YYYY-MM') AS mois,
    SUM(lc.quantite * lc.prix_unitaire * (1 - lc.taux_remise)) AS chiffre_affaires
FROM
    COMMANDES co
JOIN
    LIGNES_COMMANDE lc ON co.id_commande = lc.id_commande
WHERE
    EXTRACT(YEAR FROM co.date_commande) = 2024
GROUP BY
    TO_CHAR(co.date_commande, 'YYYY-MM')
ORDER BY
    mois;

-- 4 Top 5 des boîtes les plus vendues
CREATE OR REPLACE VIEW v4 AS
SELECT
    b.id_boite,
    m.nom_matiere,
    c.nom_couleur,
    SUM(lc.quantite) AS quantite_vendue
FROM
    LIGNES_COMMANDE lc
JOIN
    BOITES b ON lc.id_boite = b.id_boite    
JOIN
    MATIERES m ON b.id_matiere = m.id_matiere
JOIN
    COULEURS c ON b.id_couleur = c.id_couleur
GROUP BY
    b.id_boite, m.nom_matiere, c.nom_couleur
ORDER BY
    quantite_vendue DESC
LIMIT 5;

-- 5. Top 5 des boîtes les plus rentables

CREATE OR REPLACE VIEW v5 AS
SELECT
    b.id_boite,
    m.nom_matiere,
    c.nom_couleur,
    SUM(lc.quantite * lc.prix_unitaire * (1 - lc.taux_remise)) AS chiffre_affaires
FROM
    LIGNES_COMMANDE lc
JOIN
    BOITES b ON lc.id_boite = b.id_boite
JOIN
    MATIERES m ON b.id_matiere = m.id_matiere
JOIN
    COULEURS c ON b.id_couleur = c.id_couleur
GROUP BY
    b.id_boite, m.nom_matiere, c.nom_couleur
ORDER BY
    chiffre_affaires DESC
LIMIT 5;


-- 6. Nombre total de commandes et chiffre d'affaires par matière

CREATE OR REPLACE VIEW v6 AS
SELECT
    m.nom_matiere,
    COUNT(DISTINCT co.id_commande) AS nombre_commandes,
    SUM(lc.quantite * lc.prix_unitaire * (1 - lc.taux_remise)) AS chiffre_affaires
FROM
    MATIERES m
JOIN
    BOITES b ON m.id_matiere = b.id_matiere
JOIN
    LIGNES_COMMANDE lc ON b.id_boite = lc.id_boite
JOIN
    COMMANDES co ON lc.id_commande = co.id_commande
GROUP BY
    m.nom_matiere
ORDER BY
    chiffre_affaires DESC;

-- 7. Nombre total de commandes et chiffre d'affaires par couleur

CREATE OR REPLACE VIEW v7 AS
SELECT
    c.nom_couleur,
    COUNT(DISTINCT co.id_commande) AS nombre_commandes,
    SUM(lc.quantite * lc.prix_unitaire * (1 - lc.taux_remise)) AS chiffre_affaires
FROM
    COULEURS c
JOIN
    BOITES b ON c.id_couleur = b.id_couleur
JOIN
    LIGNES_COMMANDE lc ON b.id_boite = lc.id_boite
JOIN
    COMMANDES co ON lc.id_commande = co.id_commande
GROUP BY
    c.nom_couleur
ORDER BY
    chiffre_affaires DESC;

-- 8. Répartition des commandes par jour de la semaine

CREATE OR REPLACE VIEW v8 AS
SELECT
    TO_CHAR(co.date_commande, 'Day') AS jour_semaine,
    COUNT(co.id_commande) AS nombre_commandes
FROM
    COMMANDES co
GROUP BY
    TO_CHAR(co.date_commande, 'Day')
ORDER BY
    nombre_commandes DESC;

