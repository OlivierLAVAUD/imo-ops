import psycopg2
from psycopg2 import OperationalError
import sys
from dotenv import load_dotenv
import os

def get_db_config():
    """
    Configuration de connexion à la base
    """
    load_dotenv()
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('POSTGRES_IMO_DB') or os.getenv('DB_NAME', 'imo_db'),
        'user': os.getenv('POSTGRES_IMO_USER') or os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('POSTGRES_IMO_PASSWORD') or os.getenv('DB_PASSWORD', 'password'),
    }

def explore_database():
    """
    Explore complètement la structure de la base de données
    """
    config = get_db_config()
    
    print("🔍 Exploration de la base de données imo_db")
    print("=" * 60)
    
    try:
        connection = psycopg2.connect(**config)
        cursor = connection.cursor()
        
        # 1. Informations générales
        print("\n📊 INFORMATIONS GÉNÉRALES")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                current_database() as db_name,
                current_user as db_user,
                version() as db_version,
                pg_size_pretty(pg_database_size(current_database())) as db_size
        """)
        db_info = cursor.fetchone()
        
        print(f"🗄️  Base de données: {db_info[0]}")
        print(f"👤 Utilisateur: {db_info[1]}")
        print(f"📊 Version: {db_info[2].split(',')[0]}")
        print(f"💾 Taille: {db_info[3]}")
        
        # 2. Liste des tables avec statistiques (REQUÊTE CORRIGÉE)
        print("\n📦 STRUCTURE DES TABLES")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                t.table_name,
                COUNT(c.column_name) as column_count,
                pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name))) as table_size
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c ON t.table_name = c.table_name AND t.table_schema = c.table_schema
            WHERE t.table_schema = 'public'
            GROUP BY t.table_name
            ORDER BY t.table_name
        """)
        
        tables = cursor.fetchall()
        print(f"Nombre total de tables: {len(tables)}")
        
        for table_name, column_count, table_size in tables:
            print(f"\n📋 Table: {table_name}")
            print(f"   📏 Colonnes: {column_count}")
            print(f"   💾 Taille: {table_size}")
            
            # Détails des colonnes pour chaque table
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            for col_name, data_type, nullable, default_val in columns:
                nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
                default_str = f" DEFAULT {default_val}" if default_val else ""
                print(f"   └─ {col_name} ({data_type}) {nullable_str}{default_str}")
        
        # 3. Données d'exemple pour chaque table
        print("\n📝 DONNÉES D'EXEMPLE")
        print("-" * 30)
        
        for table_name, _, _ in tables:
            print(f"\n📊 Table: {table_name}")
            
            try:
                # Compter les lignes
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                print(f"   📈 Nombre d'enregistrements: {row_count}")
                
                # Afficher quelques données si la table n'est pas vide
                if row_count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
                    sample_data = cursor.fetchall()
                    
                    # Récupérer les noms de colonnes
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = %s 
                        ORDER BY ordinal_position
                    """, (table_name,))
                    column_names = [col[0] for col in cursor.fetchall()]
                    
                    print(f"   🔍 Exemple de données (2 premières lignes):")
                    for i, row in enumerate(sample_data):
                        print(f"      Ligne {i+1}:")
                        for j, value in enumerate(row):
                            if j < len(column_names):  # Éviter les index out of range
                                col_name = column_names[j]
                                # Tronquer les valeurs longues pour l'affichage
                                if value is not None:
                                    display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
                                else:
                                    display_value = "NULL"
                                print(f"         {col_name}: {display_value}")
                            
            except Exception as e:
                print(f"   ⚠️  Impossible de lire les données: {e}")
        
        # 4. Vues et fonctions
        print("\n👁️ VUES DISPONIBLES")
        print("-" * 30)
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        views = cursor.fetchall()
        
        if views:
            for view in views:
                print(f"   👁️  {view[0]}")
        else:
            print("   Aucune vue trouvée")
        
        # 5. Index
        print("\n📑 INDEX DISPONIBLES")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                indexname,
                tablename,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        indexes = cursor.fetchall()
        
        if indexes:
            for index_name, table_name, index_def in indexes:
                print(f"   📑 {index_name} sur {table_name}")
                # Afficher seulement les premiers caractères de la définition
                short_def = index_def[:80] + "..." if len(index_def) > 80 else index_def
                print(f"      └─ {short_def}")
        else:
            print("   Aucun index trouvé")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("🎉 Exploration terminée avec succès!")
        return True
        
    except OperationalError as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        print(f"🔍 Détails de l'erreur: {traceback.format_exc()}")
        return False

def test_specific_queries():
    """
    Teste des requêtes spécifiques sur les tables principales
    """
    print("\n🧪 REQUÊTES SPÉCIFIQUES")
    print("=" * 50)
    
    config = get_db_config()
    
    try:
        connection = psycopg2.connect(**config)
        cursor = connection.cursor()
        
        # Vérifier si la table annonces existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'annonces'
            )
        """)
        annonces_exists = cursor.fetchone()[0]
        
        if not annonces_exists:
            print("❌ La table 'annonces' n'existe pas")
            return
        
        # Test 1: Statistiques des annonces
        print("\n📊 STATISTIQUES DES ANNONCES")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_annonces,
                ROUND(AVG(prix), 2) as prix_moyen,
                ROUND(AVG(surface), 2) as surface_moyenne,
                ROUND(MIN(prix), 2) as prix_min,
                ROUND(MAX(prix), 2) as prix_max
            FROM annonces
            WHERE prix IS NOT NULL AND surface IS NOT NULL
        """)
        stats = cursor.fetchone()
        print(f"   📈 Total annonces: {stats[0]}")
        print(f"   💰 Prix moyen: {stats[1]:,.2f}€")
        print(f"   📏 Surface moyenne: {stats[2]:,.2f}m²")
        print(f"   📉 Prix minimum: {stats[3]:,.2f}€")
        print(f"   📈 Prix maximum: {stats[4]:,.2f}€")
        
        # Test 2: Répartition par type de bien
        print("\n🏠 RÉPARTITION PAR TYPE DE BIEN")
        cursor.execute("""
            SELECT 
                type_bien,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM annonces), 2) as percentage
            FROM annonces
            WHERE type_bien IS NOT NULL
            GROUP BY type_bien
            ORDER BY count DESC
        """)
        types = cursor.fetchall()
        for type_bien, count, percentage in types:
            print(f"   🏠 {type_bien}: {count} annonces ({percentage}%)")
        
        # Test 3: Dernières annonces ajoutées
        print("\n🆕 DERNIÈRES ANNONCES")
        cursor.execute("""
            SELECT reference, titre, prix, localisation, date_extraction
            FROM annonces
            ORDER BY date_extraction DESC
            LIMIT 3
        """)
        recent_annonces = cursor.fetchall()
        for ref, titre, prix, localisation, date_ext in recent_annonces:
            print(f"   📍 {localisation}: {titre}")
            print(f"      💰 {prix:,.2f}€ - Ref: {ref}")
            print(f"      🕒 {date_ext}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Erreur lors des requêtes spécifiques: {e}")
        import traceback
        print(f"🔍 Détails: {traceback.format_exc()}")

def simple_table_check():
    """
    Vérification simple des tables
    """
    print("\n🔍 VÉRIFICATION SIMPLE DES TABLES")
    print("=" * 50)
    
    config = get_db_config()
    
    try:
        connection = psycopg2.connect(**config)
        cursor = connection.cursor()
        
        # Liste simple des tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print("📋 Tables trouvées dans le schéma public:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    # D'abord une vérification simple
    simple_table_check()
    
    # Ensuite exploration complète
    success = explore_database()
    
    # Requêtes spécifiques si l'exploration a réussi
    if success:
        test_specific_queries()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ La base imo_db est parfaitement configurée et opérationnelle!")
        sys.exit(0)
    else:
        print("❌ Il y a des problèmes avec la base de données")
        sys.exit(1)