import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def clean_database_quick():
    """Vider rapidement toute la base"""
    
    # Configuration
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('IMO_DB') or os.getenv('DB_NAME', 'imo_db'),
        'user': os.getenv('IMO_USER') or os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('IMO_PASSWORD') or os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🧹 VIDAGE RAPIDE DE LA BASE")
    print("=" * 40)
    
    try:
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        # Désactiver les contraintes
        cur.execute("SET session_replication_role = 'replica';")
        
        # Supprimer toutes les vues
        cur.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
                
                FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
                END LOOP;
                
                FOR r IN (SELECT proname FROM pg_proc WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')) LOOP
                    EXECUTE 'DROP FUNCTION IF EXISTS ' || quote_ident(r.proname) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        
        # Réactiver les contraintes
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()
        
        print("✅ Base entièrement vidée!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    clean_database_quick()