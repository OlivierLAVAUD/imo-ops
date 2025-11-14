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