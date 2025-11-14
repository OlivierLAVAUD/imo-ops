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