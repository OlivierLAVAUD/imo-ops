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