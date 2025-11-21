import pandas as pd
from datetime import datetime, timedelta

class RGPDCompliance:
    def __init__(self):
        self.retention_days = 730  # 24 mois
        self.sensitive_patterns = [
            r'\b\d{10}\b',  # Numéros téléphone
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'  # Cartes bancaires
        ]
    
    def detect_sensitive_data(self, text):
        """Détection automatique des données sensibles"""
        import re
        for pattern in self.sensitive_patterns:
            if re.search(pattern, str(text)):
                return True
        return False
    
    def anonymize_personal_data(self, dataframe):
        """Anonymisation des données personnelles"""
        # Tronquage des noms complets
        if 'conseiller_nom' in dataframe.columns:
            dataframe['conseiller_nom'] = dataframe['conseiller_nom'].apply(
                lambda x: x.split()[0] + ' ' + x.split()[1][0] + '.' if pd.notna(x) and len(x.split()) > 1 else 'Anonyme'
            )
        
        # Nettoyage localisation
        if 'localisation_complete' in dataframe.columns:
            dataframe['localisation_complete'] = dataframe['localisation_complete'].apply(
                lambda x: self.clean_location(x) if pd.notna(x) else None
            )
        
        return dataframe
    
    def clean_location(self, location):
        """Nettoyage des données de localisation"""
        # Suppression adresses précises, conservation arrondissement/ville
        import re
        location = re.sub(r'\d{1,4}\s*(rue|avenue|boulevard|impasse|place)', '', location, flags=re.IGNORECASE)
        location = re.sub(r'\d{5}', '', location)  # Suppression codes postaux
        return location.strip()
    
    def delete_old_data(self, connection):
        """Suppression automatique des données dépassant la durée de conservation"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        delete_queries = [
            "DELETE FROM annonces WHERE date_extraction < %s",
            "DELETE FROM caracteristiques WHERE id_annonce NOT IN (SELECT id_annonce FROM annonces)",
            "DELETE FROM images WHERE id_annonce NOT IN (SELECT id_annonce FROM annonces)",
            "DELETE FROM conseiller WHERE id_annonce NOT IN (SELECT id_annonce FROM annonces)"
        ]
        
        for query in delete_queries:
            cursor = connection.cursor()
            cursor.execute(query, (cutoff_date,))
            connection.commit()
            print(f"✅ Nettoyage RGPD exécuté: {cursor.rowcount} enregistrements supprimés")
```
```bash
# Utilisation
rgpd = RGPDCompliance()

4.2 Planification Automatique du Nettoyage
python

# dags/rgpd_compliance_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from scripts.rgpd_compliance import RGPDCompliance
from airflow.providers.postgres.hooks.postgres import PostgresHook

def execute_rgpd_cleanup():
    """Tâche planifiée de nettoyage RGPD"""
    hook = PostgresHook(postgres_conn_id='imo_db')
    conn = hook.get_conn()
    
    rgpd = RGPDCompliance()
    
    # 1. Suppression données anciennes
    rgpd.delete_old_data(conn)
    
    # 2. Audit données sensibles
    audit_results = rgpd.audit_sensitive_data(conn)
    
    # 3. Log de conformité
    rgpd.generate_compliance_report(audit_results)
    
    conn.close()
    return "RGPD_CLEANUP_COMPLETED"

# DAG mensuel de conformité RGPD
with DAG(
    'imo_t_rgpd_compliance',
    default_args={'owner': 'airflow', 'retries': 1},
    description='Nettoyage et conformité RGPD mensuelle',
    schedule_interval='@monthly',  # Exécution mensuelle
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    rgpd_task = PythonOperator(
        task_id='execute_rgpd_cleanup',
        python_callable=execute_rgpd_cleanup,
    )

5. MESURES DE SÉCURITÉ TECHNIQUES
5.1 Chiffrement et Protection
sql

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

5.2 Contrôle d'Accès
python

# api/rgpd_middleware.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

class RGPDMiddleware(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        # Vérification des droits d'accès
        if not self.verify_rgpd_access(credentials.credentials):
            raise HTTPException(
                status_code=403,
                detail="Accès non autorisé aux données personnelles"
            )
        
        # Audit de l'accès
        self.log_access(request, credentials.credentials)
        
        return credentials.credentials
    
    def verify_rgpd_access(self, token: str) -> bool:
        """Vérification que l'utilisateur a le droit d'accéder aux données"""
        try:
            payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
            return payload.get('rgpd_authorized', False)
        except:
            return False
    
    def log_access(self, request: Request, user_id: str):
        """Journalisation des accès aux données personnelles"""
        audit_log = {
            'user_id': user_id,
            'endpoint': request.url.path,
            'timestamp': datetime.now(),
            'ip_address': request.client.host
        }
        # Sauvegarde en base de données
       self.save_audit_log(audit_log)