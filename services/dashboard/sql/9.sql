SELECT
    b.id_boite,
    m.nom_matiere,
    c.nom_couleur,
    AVG(lc.quantite) AS moyenne_quantite
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
    moyenne_quantite DESC;