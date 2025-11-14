import json
import re
import psycopg2
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

class JSONToPostgreSQL:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.load_environment_variables()
        
    def load_environment_variables(self):
        """Charger les variables d'environnement depuis le fichier .env"""
        load_dotenv()
        
        # Construire l'URL de connexion pour l'affichage
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('POSTGRES_IMO_DB') or os.getenv('DB_NAME', 'imo_db')
        db_user = os.getenv('POSTGRES_IMO_USER') or os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('POSTGRES_IMO_PASSWORD') or os.getenv('DB_PASSWORD', 'password')
        
        # URL pour affichage (masqué)
        db_url_masked = f"postgresql://{db_user}:[masqué]@{db_host}:{db_port}/{db_name}"
        print(f"🔗 URL de connexion: {db_url_masked}")
        
        self.db_config = {
            'host': db_host,
            'database': db_name,
            'user': db_user,
            'password': db_password,
            'port': db_port,
            'client_encoding': 'utf-8'
        }
        
    def test_connection(self) -> bool:
        """Tester la connexion à la base de données"""
        print("🔍 Test de connexion à la base de données...")
        
        try:
            test_conn = psycopg2.connect(**self.db_config)
            test_cur = test_conn.cursor()
            
            # Test de connexion basique
            test_cur.execute("SELECT 1 as test_connection;")
            connection_ok = test_cur.fetchone()[0] == 1
            
            if not connection_ok:
                print("❌ Test de connexion de base échoué")
                return False
            
            print("✅ Test de connexion de base réussi")
            
            # Vérifier les tables
            try:
                test_cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('annonces', 'caracteristiques', 'images', 'conseiller', 'dpe', 'copropriete')
                """)
                tables = [row[0] for row in test_cur.fetchall()]
                
                required_tables = ['annonces', 'caracteristiques', 'images', 'conseiller', 'dpe', 'copropriete']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    print(f"❌ Tables manquantes: {', '.join(missing_tables)}")
                    return False
                else:
                    print("✅ Toutes les tables requises sont présentes")
                    
            except Exception as e:
                print(f"⚠️  Impossible de vérifier les tables: {e}")
                return False
            
            # Vérifier la version PostgreSQL
            try:
                test_cur.execute("SELECT version();")
                version_result = test_cur.fetchone()[0]
                version_match = re.search(r'PostgreSQL (\d+\.\d+)', version_result)
                if version_match:
                    print(f"✅ PostgreSQL version {version_match.group(1)}")
                    
            except Exception as e:
                print(f"⚠️  Impossible de récupérer la version: {e}")
            
            test_cur.close()
            test_conn.close()
            return True
                
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            return False

    def connect(self) -> bool:
        """Établir la connexion à la base de données"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cur = self.conn.cursor()
            print("✅ Connexion à la base de données établie")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False

    def disconnect(self):
        """Fermer la connexion"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        print("✅ Connexion fermée")

    def check_existing_reference(self, reference: str) -> bool:
        """Vérifier si une référence existe déjà dans la base"""
        try:
            query = "SELECT 1 FROM annonces WHERE reference = %s"
            self.cur.execute(query, (reference,))
            exists = self.cur.fetchone() is not None
            return exists
        except Exception as e:
            print(f"❌ Erreur vérification référence {reference}: {e}")
            return False

    def clean_price(self, price_str: str) -> Optional[float]:
        """Nettoyer et convertir un prix string en float"""
        if not price_str or price_str.strip() == "":
            return None
        
        # Nettoyer le texte
        clean_text = price_str.replace(' ', '').replace(' ', '').replace('€', '').strip()
        match = re.search(r'^([\d]+[,.]?\d*)$', clean_text)
        if match:
            clean_number = match.group(1).replace(',', '.')
            try:
                return float(clean_number)
            except ValueError:
                return None
        return None

    def extract_number(self, text: str) -> Optional[int]:
        """Extraire un nombre d'une chaîne de caractères"""
        if not text or text.strip() == "":
            return None
        
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else None

    def extract_surface(self, surface_str: str) -> Optional[float]:
        """Extraire la surface d'une chaîne"""
        if not surface_str or surface_str.strip() == "":
            return None
        
        match = re.search(r'(\d+[,.]?\d*)', surface_str)
        if match:
            clean_number = match.group(1).replace(',', '.')
            try:
                surface = float(clean_number)
                if surface > 0:
                    return surface
            except ValueError:
                pass
        return None

    def extract_year(self, year_str: str) -> Optional[int]:
        """Extraire l'année de construction"""
        if not year_str or year_str.strip() == "":
            return None
        
        match = re.search(r'(19\d{2}|20\d{2})', year_str)
        if match:
            year = int(match.group(1))
            current_year = datetime.now().year
            if 1500 <= year <= current_year:
                return year
        return None

    def extract_dpe_class(self, dpe_str: str) -> Optional[str]:
        """Extraire la classe DPE (A-G)"""
        if not dpe_str or dpe_str.strip() == "":
            return None
        
        match = re.search(r'([A-G])', dpe_str.upper())
        return match.group(1) if match else None

    def extract_boolean(self, value: Any) -> bool:
        """Extraire une valeur booléenne"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'oui', 'vrai')
        if isinstance(value, int):
            return value == 1
        return False

    def extract_charges(self, charges_str: str) -> Optional[float]:
        """Extraire le montant des charges d'une chaîne"""
        if not charges_str or charges_str.strip() == "":
            return None
        
        # Chercher un nombre dans la chaîne (ex: "1 176 € / an" -> 1176)
        match = re.search(r'(\d+[ \s]?\d*[,.]?\d*)', charges_str.replace(' ', '').replace(' ', ''))
        if match:
            clean_number = match.group(1).replace(',', '.')
            try:
                return float(clean_number)
            except ValueError:
                pass
        return None

    def process_annonce_data(self, annonce_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter et nettoyer les données d'une annonce"""
        
        # Conversion des prix
        prix = self.clean_price(annonce_data.get('prix', ''))
        prix_au_m2 = self.clean_price(annonce_data.get('prix_au_m2', ''))
        
        # Si prix_au_m2 n'est pas fourni mais prix et surface le sont, le calculer
        surface = self.extract_surface(annonce_data.get('surface', ''))
        if not prix_au_m2 and prix and surface and surface > 0:
            prix_au_m2 = round(prix / surface, 2)
        
        # Traitement de la date d'extraction
        date_extraction = annonce_data.get('date_extraction')
        if date_extraction:
            try:
                date_extraction = datetime.fromisoformat(date_extraction.replace('Z', '+00:00'))
            except ValueError:
                date_extraction = datetime.now()
        else:
            date_extraction = datetime.now()
        
        return {
            # Données principales
            'reference': annonce_data.get('reference', '').strip(),
            'titre': annonce_data.get('titre', '').strip(),
            'titre_complet': annonce_data.get('titre_complet', '').strip(),
            'prix': prix,
            'prix_detaille': annonce_data.get('prix_detaille', '').strip(),
            'prix_au_m2': prix_au_m2,
            'localisation': annonce_data.get('localisation', '').strip(),
            'localisation_complete': annonce_data.get('localisation_complete', '').strip(),
            'surface': surface,
            'surface_terrain': self.extract_surface(annonce_data.get('surface_terrain', '')),
            'pieces': self.extract_number(annonce_data.get('pieces', '')),
            'type_bien': annonce_data.get('type_bien', '').strip(),
            'description': annonce_data.get('description', '').strip(),
            'annee_construction': self.extract_year(annonce_data.get('annee_construction', '')),
            'honoraires': annonce_data.get('honoraires', '').strip(),
            'image_url': annonce_data.get('image_url', '').strip(),
            'nombre_photos': self.extract_number(annonce_data.get('nombre_photos', '')),
            'has_video': self.extract_boolean(annonce_data.get('has_video', '')),
            'has_visite_virtuelle': self.extract_boolean(annonce_data.get('has_visite_virtuelle', '')),
            'media_info': annonce_data.get('media_info', '').strip(),
            'lien': annonce_data.get('lien', '').strip(),
            'date_extraction': date_extraction,
            
            # DPE
            'dpe_classe_active': self.extract_dpe_class(annonce_data.get('dpe_classe_active', '')),
            'ges_classe_active': self.extract_dpe_class(annonce_data.get('ges_classe_active', '')),
            'depenses_energie_min': annonce_data.get('depenses_energie_min', '').strip(),
            'depenses_energie_max': annonce_data.get('depenses_energie_max', '').strip(),
            'annee_reference': self.extract_year(annonce_data.get('annee_reference', '')),
            
            # Données pour les tables liées
            'caracteristiques': annonce_data.get('caracteristiques_detaillees', []),
            'images': annonce_data.get('images', []),
            
            # Données conseiller (préfixe conseiller_)
            'conseiller_nom_complet': annonce_data.get('conseiller_nom_complet', '').strip(),
            'conseiller_telephone': annonce_data.get('conseiller_telephone', '').strip(),
            'conseiller_lien': annonce_data.get('conseiller_lien', '').strip(),
            'conseiller_photo': annonce_data.get('conseiller_photo', '').strip(),
            'conseiller_note': annonce_data.get('conseiller_note', '').strip(),
            
            # Données copropriété (préfixe copropriete_)
            'copropriete_nb_lots': self.extract_number(annonce_data.get('copropriete_nb_lots', '')),
            'copropriete_charges_previsionnelles': annonce_data.get('copropriete_charges_previsionnelles', '').strip(),
            'copropriete_procedures': annonce_data.get('copropriete_procedures', '').strip(),
            
            # Données DPE détaillées (à extraire de la description si nécessaire)
            'dpe_classe_energie': self.extract_dpe_class(annonce_data.get('dpe_classe_active', '')),
            'dpe_indice_energie': None,  # À extraire de la description si disponible
            'dpe_classe_climat': self.extract_dpe_class(annonce_data.get('ges_classe_active', '')),
            'dpe_indice_climat': None   # À extraire de la description si disponible
        }

    def insert_annonce(self, annonce_data: Dict[str, Any]) -> Optional[int]:
        """Insérer une annonce dans la base et retourner son ID"""
        
        try:
            query = """
            INSERT INTO annonces (
                reference, titre, titre_complet, prix, prix_detaille, prix_au_m2, 
                localisation, localisation_complete, surface, surface_terrain, pieces,
                type_bien, description, annee_construction, honoraires, image_url,
                nombre_photos, has_video, has_visite_virtuelle, media_info, lien,
                date_extraction, dpe_classe_active, ges_classe_active, 
                depenses_energie_min, depenses_energie_max, annee_reference
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_annonce
            """
            
            values = (
                annonce_data['reference'],
                annonce_data['titre'],
                annonce_data['titre_complet'],
                annonce_data['prix'],
                annonce_data['prix_detaille'],
                annonce_data['prix_au_m2'],
                annonce_data['localisation'],
                annonce_data['localisation_complete'],
                annonce_data['surface'],
                annonce_data['surface_terrain'],
                annonce_data['pieces'],
                annonce_data['type_bien'],
                annonce_data['description'],
                annonce_data['annee_construction'],
                annonce_data['honoraires'],
                annonce_data['image_url'],
                annonce_data['nombre_photos'],
                annonce_data['has_video'],
                annonce_data['has_visite_virtuelle'],
                annonce_data['media_info'],
                annonce_data['lien'],
                annonce_data['date_extraction'],
                annonce_data['dpe_classe_active'],
                annonce_data['ges_classe_active'],
                annonce_data['depenses_energie_min'],
                annonce_data['depenses_energie_max'],
                annonce_data['annee_reference']
            )
            
            self.cur.execute(query, values)
            annonce_id = self.cur.fetchone()[0]
            self.conn.commit()
            
            print(f"✅ Annonce {annonce_data['reference']} insérée (ID: {annonce_id})")
            return annonce_id
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion annonce {annonce_data['reference']}: {e}")
            return None

    def insert_caracteristiques(self, annonce_id: int, caracteristiques: List[str]):
        """Insérer les caractéristiques d'une annonce"""
        
        try:
            query = "INSERT INTO caracteristiques (id_annonce, valeur) VALUES (%s, %s)"
            
            inserted_count = 0
            for caracteristique in caracteristiques:
                if caracteristique and caracteristique.strip():
                    self.cur.execute(query, (annonce_id, caracteristique.strip()))
                    inserted_count += 1
            
            self.conn.commit()
            if inserted_count > 0:
                print(f"✅ {inserted_count} caractéristiques insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion caractéristiques: {e}")

    def insert_images(self, annonce_id: int, images: List[str]):
        """Insérer les images d'une annonce"""
        
        try:
            query = "INSERT INTO images (id_annonce, url, ordre) VALUES (%s, %s, %s)"
            
            inserted_count = 0
            for order, image_url in enumerate(images, 1):
                if image_url and image_url.strip():
                    self.cur.execute(query, (annonce_id, image_url.strip(), order))
                    inserted_count += 1
            
            self.conn.commit()
            if inserted_count > 0:
                print(f"✅ {inserted_count} images insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion images: {e}")

    def insert_conseiller(self, annonce_id: int, conseiller_data: Dict[str, Any]):
        """Insérer les données du conseiller"""
        
        # Vérifier si on a au moins un champ rempli
        if not any([conseiller_data.get('conseiller_nom_complet'), 
                   conseiller_data.get('conseiller_telephone'),
                   conseiller_data.get('conseiller_lien')]):
            return
            
        try:
            query = """
            INSERT INTO conseiller (
                id_annonce, nom_complet, telephone, lien, photo, note
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                conseiller_data.get('conseiller_nom_complet', '').strip(),
                conseiller_data.get('conseiller_telephone', '').strip(),
                conseiller_data.get('conseiller_lien', '').strip(),
                conseiller_data.get('conseiller_photo', '').strip(),
                conseiller_data.get('conseiller_note', '').strip()
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Conseiller inséré: {conseiller_data.get('conseiller_nom_complet', 'N/A')}")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion conseiller: {e}")

    def insert_dpe(self, annonce_id: int, dpe_data: Dict[str, Any]):
        """Insérer les données DPE"""
        
        # Vérifier si on a des données DPE
        if not any([dpe_data.get('dpe_classe_energie'), 
                   dpe_data.get('dpe_classe_climat')]):
            return
            
        try:
            query = """
            INSERT INTO dpe (
                id_annonce, classe_energie, indice_energie, classe_climat, indice_climat
            ) VALUES (%s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                dpe_data.get('dpe_classe_energie'),
                dpe_data.get('dpe_indice_energie'),
                dpe_data.get('dpe_classe_climat'),
                dpe_data.get('dpe_indice_climat')
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ DPE inséré: {dpe_data.get('dpe_classe_energie', 'N/A')}")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion DPE: {e}")

    def insert_copropriete(self, annonce_id: int, copropriete_data: Dict[str, Any]):
        """Insérer les données de copropriété"""
        
        # Vérifier si on a des données de copropriété
        if not any([copropriete_data.get('copropriete_nb_lots'), 
                   copropriete_data.get('copropriete_charges_previsionnelles'),
                   copropriete_data.get('copropriete_procedures')]):
            return
            
        try:
            query = """
            INSERT INTO copropriete (
                id_annonce, nb_lots, charges_previsionnelles, procedures
            ) VALUES (%s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                copropriete_data.get('copropriete_nb_lots'),
                copropriete_data.get('copropriete_charges_previsionnelles', '').strip(),
                copropriete_data.get('copropriete_procedures', '').strip()
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            nb_lots = copropriete_data.get('copropriete_nb_lots', 'N/A')
            print(f"✅ Copropriété insérée: {nb_lots} lots")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion copropriété: {e}")

    def process_json_file(self, json_file_path: str, skip_existing: bool = True):
        """Traiter un fichier JSON complet et insérer les données"""
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📁 Fichier JSON chargé: {len(data)} annonces trouvées")
            
            inserted_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, annonce_data in enumerate(data, 1):
                print(f"\n--- Traitement annonce {i}/{len(data)} ---")
                
                # Vérifier la référence
                reference = annonce_data.get('reference', '').strip()
                if not reference:
                    print("❌ Annonce sans référence, ignorée")
                    error_count += 1
                    continue
                
                print(f"📝 Référence: {reference}")
                
                # Vérifier si la référence existe déjà
                if skip_existing and self.check_existing_reference(reference):
                    print("⏭️  Déjà existante, ignorée")
                    skipped_count += 1
                    continue
                
                # Traiter les données
                processed_data = self.process_annonce_data(annonce_data)
                
                # Afficher les infos principales
                if processed_data['prix']:
                    print(f"💰 Prix: {processed_data['prix']:,.2f}€")
                if processed_data['surface']:
                    print(f"📏 Surface: {processed_data['surface']}m²")
                if processed_data['localisation']:
                    print(f"📍 Localisation: {processed_data['localisation']}")
                if processed_data['conseiller_nom_complet']:
                    print(f"👤 Conseiller: {processed_data['conseiller_nom_complet']}")
                
                # Insérer l'annonce
                annonce_id = self.insert_annonce(processed_data)
                
                if annonce_id:
                    # Insérer les caractéristiques
                    if processed_data['caracteristiques']:
                        self.insert_caracteristiques(annonce_id, processed_data['caracteristiques'])
                    
                    # Insérer les images
                    if processed_data['images']:
                        self.insert_images(annonce_id, processed_data['images'])
                    
                    # Insérer le conseiller
                    self.insert_conseiller(annonce_id, processed_data)
                    
                    # Insérer le DPE
                    self.insert_dpe(annonce_id, processed_data)
                    
                    # Insérer la copropriété
                    self.insert_copropriete(annonce_id, processed_data)
                    
                    inserted_count += 1
                else:
                    error_count += 1
            
            # Résumé final
            print(f"\n{'='*50}")
            print("🎉 TRAITEMENT TERMINÉ - RÉCAPITULATIF")
            print(f"{'='*50}")
            print(f"✅ {inserted_count} nouvelles annonces insérées")
            print(f"⏭️  {skipped_count} annonces déjà existantes (ignorées)")
            print(f"❌ {error_count} annonces en erreur")
            print(f"📊 Total traité: {len(data)} annonces")
            
            # Afficher les statistiques finales
            if self.conn:
                self.show_final_stats()
            
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {json_file_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON: {e}")
        except Exception as e:
            print(f"❌ Erreur lors du traitement du fichier: {e}")

    def show_final_stats(self):
        """Afficher les statistiques finales de la base"""
        try:
            self.cur.execute("SELECT COUNT(*) FROM annonces")
            total_annonces = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM caracteristiques")
            total_caracteristiques = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM images")
            total_images = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM conseiller")
            total_conseillers = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM dpe")
            total_dpe = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM copropriete")
            total_copropriete = self.cur.fetchone()[0]
            
            print(f"\n📊 STATISTIQUES FINALES DE LA BASE:")
            print(f"   • Annonces: {total_annonces}")
            print(f"   • Caractéristiques: {total_caracteristiques}")
            print(f"   • Images: {total_images}")
            print(f"   • Conseillers: {total_conseillers}")
            print(f"   • DPE: {total_dpe}")
            print(f"   • Copropriétés: {total_copropriete}")
            
        except Exception as e:
            print(f"⚠️  Impossible de récupérer les statistiques: {e}")

def main():
    """Fonction principale"""
    
    print("🏠 IMPORTATEUR D'ANNONCES IMMOBILIÈRES")
    print("=" * 50)
    
    # Chemin vers le fichier JSON
    json_file_path = 'annonces.json'
    
    # Vérifier si le fichier existe
    if not os.path.exists(json_file_path):
        print(f"❌ Fichier {json_file_path} non trouvé")
        print("💡 Placez votre fichier JSON dans le même dossier que ce script")
        sys.exit(1)
    
    # Initialiser le processeur
    processor = JSONToPostgreSQL()
    
    # Test de connexion préalable
    if not processor.test_connection():
        print("\n❌ Impossible de continuer sans connexion valide à la base de données")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    try:
        # Établir la connexion principale
        if not processor.connect():
            sys.exit(1)
        
        # Traiter le fichier JSON
        processor.process_json_file(json_file_path, skip_existing=True)
        
    except KeyboardInterrupt:
        print("\n⏹️  Import interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    finally:
        # Fermer la connexion
        processor.disconnect()

if __name__ == "__main__":
    main()