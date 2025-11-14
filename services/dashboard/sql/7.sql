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