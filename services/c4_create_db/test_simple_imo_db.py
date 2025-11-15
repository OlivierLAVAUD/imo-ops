import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def test_simple_with_url():
    """
    Test simple qui affiche l'URL de connexion
    """
    print("🔗 TEST SIMPLE DE CONNEXION")
    print("=" * 40)
    
    # Construire l'URL de connexion
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('IMO_DB') or os.getenv('DB_NAME', 'imo_db')
    db_user = os.getenv('IMO_USER') or os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('IMO_PASSWORD') or os.getenv('DB_PASSWORD', 'password')
    
    # URL complète (avec mot de passe masqué pour l'affichage)
    db_url_full = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    db_url_masked = f"postgresql://{db_user}:[masqué]@{db_host}:{db_port}/{db_name}"
    
    print(f"📡 URL de connexion: {db_url_full}")
    print(f"🔧 Host: {db_host}")
    print(f"🚪 Port: {db_port}")
    print(f"🗄️  Database: {db_name}")
    print(f"👤 User: {db_user}")
    print(f"🔑 Password: {'*' * len(db_password) if db_password else 'non défini'}")
    
    try:
        # Connexion avec paramètres individuels
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        cur = conn.cursor()
        
        # Test basique
        cur.execute("SELECT current_database(), current_user, version()")
        db_name, db_user, db_version = cur.fetchone()
        
        print(f"\n✅ CONNEXION RÉUSSIE!")
        print(f"📊 Base connectée: {db_name}")
        print(f"👤 Utilisateur: {db_user}")
        print(f"🔄 Version: {db_version.split(',')[0]}")
        
        # Lister les tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        print(f"\n📦 Tables trouvées ({len(tables)}):")
        for table in tables:
            # Compter les lignes pour chaque table
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"   - {table} ({count} enregistrements)")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_with_url()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Test réussi - La base est accessible!")
    else:
        print("💥 Test échoué - Vérifiez la configuration")