SELECT
    TO_CHAR(co.date_commande, 'Day') AS jour_semaine,
    COUNT(co.id_commande) AS nombre_commandes
FROM
    COMMANDES co
GROUP BY
    TO_CHAR(co.date_commande, 'Day')
ORDER BY
    nombre_commandes DESC;