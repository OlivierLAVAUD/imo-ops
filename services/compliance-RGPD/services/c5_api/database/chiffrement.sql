-- Configuration PostgreSQL pour la protection des données
-- Activation du chiffrement SSL
ALTER SYSTEM SET ssl = on;

-- Audit des accès
CREATE TABLE audit_access (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100),
    action_type VARCHAR(50),
    table_name VARCHAR(100),
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vues sécurisées pour l'accès aux données
CREATE VIEW v_annonces_anonymisees AS
SELECT 
    id_annonce,
    reference,
    titre,
    prix,
    surface,
    LEFT(localisation, 3) || '***' as localisation_secure,
    type_bien
FROM annonces
WHERE date_extraction >= CURRENT_DATE - INTERVAL '24 months';
