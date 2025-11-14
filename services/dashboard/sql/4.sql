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