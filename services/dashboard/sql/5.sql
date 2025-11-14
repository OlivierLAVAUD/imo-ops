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