import json
import re
import psycopg2
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

class PreparedDataToPostgreSQL:
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
        db_name = os.getenv('IMOos.getenv('DB_NAME', 'imo_db')
        db_user = os.getenv('IMOnv('DB_USER', 'postgres')
        db_password = os.getenv('IMO_PASSWORD') or os.getenv('DB_PASSWORD', 'password')
        
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
            
            # Vérifier les tables principales
            try:
                test_cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('annonces', 'prix', 'surface', 'composition', 'localisation', 'batiment', 'diagnostics', 'copropriete', 'caracteristiques', 'medias', 'contact')
                """)
                tables = [row[0] for row in test_cur.fetchall()]
                
                required_tables = ['annonces', 'prix', 'surface', 'composition', 'localisation', 'batiment']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    print(f"❌ Tables manquantes: {', '.join(missing_tables)}")
                    return False
                else:
                    print("✅ Toutes les tables requises sont présentes")
                    
            except Exception as e:
                print(f"⚠️  Impossible de vérifier les tables: {e}")
                return False
            
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

    def insert_annonce_principale(self, annonce_data: Dict[str, Any]) -> Optional[int]:
        """Insérer les données principales dans la table annonces"""
        try:
            query = """
            INSERT INTO annonces (
                reference, titre, description, url_annonce, date_extraction,
                score_qualite, champs_manquants, etapes_traitees
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_annonce
            """
            
            values = (
                annonce_data.get('reference', ''),
                annonce_data.get('titre', ''),
                annonce_data.get('description', ''),
                annonce_data.get('url_annonce', ''),
                annonce_data.get('metadata', {}).get('date_extraction', datetime.now()),
                annonce_data.get('metadata', {}).get('score_qualite', 0),
                annonce_data.get('metadata', {}).get('champs_manquants', []),
                annonce_data.get('metadata', {}).get('etapes_traitees', [])
            )
            
            self.cur.execute(query, values)
            annonce_id = self.cur.fetchone()[0]
            self.conn.commit()
            
            print(f"✅ Annonce principale {annonce_data.get('reference')} insérée (ID: {annonce_id})")
            return annonce_id
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion annonce principale {annonce_data.get('reference')}: {e}")
            return None

    def insert_prix(self, annonce_id: int, prix_data: Dict[str, Any]):
        """Insérer les données de prix"""
        try:
            query = """
            INSERT INTO prix (
                id_annonce, valeur, devise, au_m2, loyer_estime_mensuel, rendement_annuel_estime
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                prix_data.get('valeur'),
                prix_data.get('devise', '€'),
                prix_data.get('au_m2'),
                None,  # loyer_estime_mensuel - à calculer plus tard
                None   # rendement_annuel_estime - à calculer plus tard
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données prix insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion prix: {e}")

    def insert_surface(self, annonce_id: int, surface_data: Dict[str, Any]):
        """Insérer les données de surface"""
        try:
            # Calcul surface par pièce
            surface_par_piece = None
            if surface_data.get('valeur') and surface_data.get('valeur') > 0:
                composition_data = surface_data.get('_composition', {})
                pieces = composition_data.get('pieces')
                if pieces and pieces > 0:
                    surface_par_piece = round(surface_data['valeur'] / pieces, 2)
            
            query = """
            INSERT INTO surface (
                id_annonce, valeur, unite, surface_par_piece
            ) VALUES (%s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                surface_data.get('valeur'),
                surface_data.get('unite', 'm²'),
                surface_par_piece
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données surface insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion surface: {e}")

    def insert_composition(self, annonce_id: int, composition_data: Dict[str, Any]):
        """Insérer les données de composition"""
        try:
            query = """
            INSERT INTO composition (
                id_annonce, pieces, chambres, type_bien
            ) VALUES (%s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                composition_data.get('pieces'),
                composition_data.get('chambres'),
                composition_data.get('type_bien')
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données composition insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion composition: {e}")

    def insert_localisation(self, annonce_id: int, localisation_data: Dict[str, Any]):
        """Insérer les données de localisation"""
        try:
            query = """
            INSERT INTO localisation (
                id_annonce, ville, code_postal, quartier, proximite, score_emplacement
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                localisation_data.get('ville'),
                localisation_data.get('code_postal'),
                localisation_data.get('quartier'),
                localisation_data.get('proximite'),
                None  # score_emplacement - à calculer plus tard
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données localisation insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion localisation: {e}")

    def insert_batiment(self, annonce_id: int, batiment_data: Dict[str, Any]):
        """Insérer les données du bâtiment"""
        try:
            query = """
            INSERT INTO batiment (
                id_annonce, annee_construction, age_bien, etage, etage_total, 
                ascenseur, score_modernite
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                batiment_data.get('annee_construction'),
                batiment_data.get('age_bien'),
                batiment_data.get('etage'),
                batiment_data.get('etage_total'),
                batiment_data.get('ascenseur', False),
                None  # score_modernite - à calculer plus tard
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données bâtiment insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion bâtiment: {e}")

    def insert_diagnostics(self, annonce_id: int, diagnostics_data: Dict[str, Any]):
        """Insérer les données de diagnostics"""
        try:
            dpe_data = diagnostics_data.get('dpe', {})
            ges_data = diagnostics_data.get('ges', {})
            
            query = """
            INSERT INTO diagnostics (
                id_annonce, dpe_classe, dpe_score, dpe_indice, 
                ges_classe, ges_score, ges_indice
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                dpe_data.get('classe'),
                dpe_data.get('score'),
                dpe_data.get('indice'),
                ges_data.get('classe'),
                ges_data.get('score'),
                ges_data.get('indice')
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données diagnostics insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion diagnostics: {e}")

    def insert_copropriete(self, annonce_id: int, copropriete_data: Dict[str, Any]):
        """Insérer les données de copropriété"""
        try:
            charges_data = copropriete_data.get('charges', {})
            
            query = """
            INSERT INTO copropriete (
                id_annonce, nb_lots, charges_valeur, charges_unite, 
                charges_periode, procedures_en_cours
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                copropriete_data.get('nb_lots'),
                charges_data.get('valeur'),
                charges_data.get('unite'),
                charges_data.get('periode'),
                copropriete_data.get('procedures_en_cours', False)
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données copropriété insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion copropriété: {e}")

    def insert_caracteristiques(self, annonce_id: int, caracteristiques: List[str]):
        """Insérer les caractéristiques"""
        try:
            query = "INSERT INTO caracteristiques (id_annonce, valeur, categorie) VALUES (%s, %s, %s)"
            
            inserted_count = 0
            for caracteristique in caracteristiques:
                if caracteristique and caracteristique.strip():
                    # Déterminer la catégorie basée sur le contenu
                    categorie = 'autres'
                    carac_lower = caracteristique.lower()
                    
                    if any(mot in carac_lower for mot in ['chauffage', 'climatisation']):
                        categorie = 'chauffage'
                    elif any(mot in carac_lower for mot in ['cuisine', 'salle de bain', 'salle d\'eau']):
                        categorie = 'equipements'
                    elif any(mot in carac_lower for mot in ['parking', 'garage', 'cave']):
                        categorie = 'dependances'
                    elif any(mot in carac_lower for mot in ['terrasse', 'balcon', 'jardin']):
                        categorie = 'exterieur'
                    elif any(mot in carac_lower for mot in ['digicode', 'interphone', 'alarme']):
                        categorie = 'securite'
                    
                    self.cur.execute(query, (annonce_id, caracteristique.strip(), categorie))
                    inserted_count += 1
            
            self.conn.commit()
            if inserted_count > 0:
                print(f"✅ {inserted_count} caractéristiques insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion caractéristiques: {e}")

    def insert_medias(self, annonce_id: int, medias_data: Dict[str, Any]):
        """Insérer les données médias"""
        try:
            # Insérer les images
            images = medias_data.get('images', [])
            query = "INSERT INTO medias (id_annonce, url, type_media, ordre) VALUES (%s, %s, %s, %s)"
            
            inserted_count = 0
            for order, image_url in enumerate(images, 1):
                if image_url and image_url.strip():
                    self.cur.execute(query, (annonce_id, image_url.strip(), 'image', order))
                    inserted_count += 1
            
            # Insérer les informations sur les vidéos/visites virtuelles
            if medias_data.get('has_video'):
                self.cur.execute(
                    "INSERT INTO medias (id_annonce, url, type_media) VALUES (%s, %s, %s)",
                    (annonce_id, 'video_presente', 'video')
                )
                inserted_count += 1
            
            if medias_data.get('has_visite_virtuelle'):
                self.cur.execute(
                    "INSERT INTO medias (id_annonce, url, type_media) VALUES (%s, %s, %s)",
                    (annonce_id, 'visite_virtuelle_presente', 'visite_virtuelle')
                )
                inserted_count += 1
            
            self.conn.commit()
            if inserted_count > 0:
                print(f"✅ {inserted_count} médias insérés")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion médias: {e}")

    def insert_contact(self, annonce_id: int, contact_data: Dict[str, Any]):
        """Insérer les données de contact"""
        try:
            # Vérifier si on a au moins un champ rempli
            if not any([contact_data.get('conseiller'), 
                       contact_data.get('telephone'),
                       contact_data.get('lien')]):
                return
            
            query = """
            INSERT INTO contact (
                id_annonce, conseiller_nom, conseiller_telephone, 
                conseiller_photo, conseiller_lien
            ) VALUES (%s, %s, %s, %s, %s)
            """
            
            values = (
                annonce_id,
                contact_data.get('conseiller'),
                contact_data.get('telephone'),
                contact_data.get('photo'),
                contact_data.get('lien')
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Données contact insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion contact: {e}")

    def process_prepared_data(self, prepared_data: Dict[str, Any]) -> bool:
        """Traiter une annonce préparée et l'insérer en base"""
        
        reference = prepared_data.get('reference', '').strip()
        if not reference:
            print("❌ Annonce sans référence, ignorée")
            return False
        
        print(f"📝 Traitement de l'annonce: {reference}")
        
        # Vérifier si la référence existe déjà
        if self.check_existing_reference(reference):
            print("⏭️  Déjà existante, ignorée")
            return False
        
        # Afficher les infos principales
        prix_data = prepared_data.get('prix', {})
        surface_data = prepared_data.get('surface', {})
        localisation_data = prepared_data.get('localisation', {})
        
        if prix_data.get('valeur'):
            print(f"💰 Prix: {prix_data['valeur']:,.2f}€")
        if surface_data.get('valeur'):
            print(f"📏 Surface: {surface_data['valeur']}m²")
        if localisation_data.get('ville'):
            print(f"📍 Localisation: {localisation_data['ville']} {localisation_data.get('code_postal', '')}")
        
        # Insérer l'annonce principale
        annonce_id = self.insert_annonce_principale(prepared_data)
        if not annonce_id:
            return False
        
        try:
            # Insérer les données modulaires
            self.insert_prix(annonce_id, prix_data)
            
            # Ajouter les données de composition aux données de surface pour le calcul
            surface_data['_composition'] = prepared_data.get('composition', {})
            self.insert_surface(annonce_id, surface_data)
            
            self.insert_composition(annonce_id, prepared_data.get('composition', {}))
            self.insert_localisation(annonce_id, localisation_data)
            self.insert_batiment(annonce_id, prepared_data.get('batiment', {}))
            self.insert_diagnostics(annonce_id, prepared_data.get('diagnostics', {}))
            self.insert_copropriete(annonce_id, prepared_data.get('copropriete', {}))
            
            # Insérer les caractéristiques
            caracteristiques = prepared_data.get('caracteristiques', [])
            if caracteristiques:
                self.insert_caracteristiques(annonce_id, caracteristiques)
            
            # Insérer les médias
            medias_data = prepared_data.get('medias', {})
            if medias_data:
                self.insert_medias(annonce_id, medias_data)
            
            # Insérer le contact
            contact_data = prepared_data.get('contact', {})
            if contact_data:
                self.insert_contact(annonce_id, contact_data)
            
            print(f"✅ Annonce {reference} complètement insérée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion des données modulaires: {e}")
            # Optionnel: supprimer l'annonce principale en cas d'erreur
            try:
                self.cur.execute("DELETE FROM annonces WHERE id_annonce = %s", (annonce_id,))
                self.conn.commit()
            except:
                pass
            return False

    def process_json_file(self, json_file_path: str):
        """Traiter un fichier JSON de données préparées"""
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📁 Fichier JSON chargé: {len(data)} annonces préparées trouvées")
            
            inserted_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, prepared_data in enumerate(data, 1):
                print(f"\n--- Traitement annonce {i}/{len(data)} ---")
                
                try:
                    success = self.process_prepared_data(prepared_data)
                    if success:
                        inserted_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    print(f"❌ Erreur lors du traitement: {e}")
                    error_count += 1
            
            # Résumé final
            print(f"\n{'='*50}")
            print("🎉 IMPORTATION TERMINÉE - RÉCAPITULATIF")
            print(f"{'='*50}")
            print(f"✅ {inserted_count} nouvelles annonces insérées")
            print(f"⏭️  {skipped_count} annonces ignorées (déjà existantes ou erreurs)")
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
            # Statistiques par table
            tables = [
                'annonces', 'prix', 'surface', 'composition', 'localisation',
                'batiment', 'diagnostics', 'copropriete', 'caracteristiques', 
                'medias', 'contact'
            ]
            
            print(f"\n📊 STATISTIQUES FINALES DE LA BASE:")
            for table in tables:
                self.cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cur.fetchone()[0]
                print(f"   • {table}: {count}")
            
            # Statistiques supplémentaires
            self.cur.execute("""
                SELECT 
                    COUNT(*) as total_annonces,
                    ROUND(AVG(p.valeur), 2) as prix_moyen,
                    ROUND(AVG(s.valeur), 2) as surface_moyenne,
                    ROUND(AVG(a.score_qualite), 2) as score_qualite_moyen
                FROM annonces a
                LEFT JOIN prix p ON a.id_annonce = p.id_annonce
                LEFT JOIN surface s ON a.id_annonce = s.id_annonce
            """)
            stats = self.cur.fetchone()
            print(f"\n📈 STATISTIQUES GLOBALES:")
            print(f"   • Prix moyen: {stats[1] or 0:,.2f}€")
            print(f"   • Surface moyenne: {stats[2] or 0:.1f}m²")
            print(f"   • Score qualité moyen: {stats[3] or 0:.1f}/10")
            
        except Exception as e:
            print(f"⚠️  Impossible de récupérer les statistiques: {e}")

def main():
    """Fonction principale"""
    
    print("🏠 IMPORTATEUR DE DONNÉES PRÉPARÉES")
    print("=" * 50)
    
    # Chemin vers le fichier JSON préparé
    json_file_path = 'annonces_preparees.json'
    
    # Vérifier si le fichier existe
    if not os.path.exists(json_file_path):
        print(f"❌ Fichier {json_file_path} non trouvé")
        print("💡 Assurez-vous d'avoir exécuté le script de préparation d'abord")
        sys.exit(1)
    
    # Initialiser le processeur
    processor = PreparedDataToPostgreSQL()
    
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
        processor.process_json_file(json_file_path)
        
    except KeyboardInterrupt:
        print("\n⏹️  Import interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    finally:
        # Fermer la connexion
        processor.disconnect()

if __name__ == "__main__":
    main()