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