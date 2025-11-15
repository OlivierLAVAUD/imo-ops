import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

class MongoDBImporterAggrege:
    def __init__(self, config_file: str = "config_aggreges.json"):
        self.client = None
        self.db = None
        self.config = None
        self.load_config(config_file)
        self.load_environment_variables()
        
    def load_config(self, config_file: str):
        """Charger la configuration depuis le fichier JSON"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✅ Configuration chargée: {config_file}")
        except FileNotFoundError:
            print(f"❌ Fichier de configuration non trouvé: {config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON: {e}")
            sys.exit(1)
            
    def load_environment_variables(self):
        """Charger les variables d'environnement"""
        load_dotenv()
        
        mongo_host = os.getenv('MONGO_HOST', 'localhost')
        mongo_port = os.getenv('MONGO_PORT', '27017')
        mongo_db = os.getenv('MONGO_DB', 'imo_agrege')
        mongo_user = os.getenv('MONGO_USER')
        mongo_password = os.getenv('MONGO_PASSWORD')
        
        if mongo_user and mongo_password:
            self.connection_string = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}"
            db_url_masked = f"mongodb://{mongo_user}:[masqué]@{mongo_host}:{mongo_port}/{mongo_db}"
        else:
            self.connection_string = f"mongodb://{mongo_host}:{mongo_port}/{mongo_db}"
            db_url_masked = f"mongodb://{mongo_host}:{mongo_port}/{mongo_db}"
            
        print(f"🔗 URL de connexion MongoDB: {db_url_masked}")
        self.db_name = mongo_db
        
    def test_connection(self) -> bool:
        """Tester la connexion à MongoDB"""
        print("🔍 Test de connexion à MongoDB...")
        
        try:
            test_client = MongoClient(self.connection_string)
            test_client.admin.command('ping')
            print("✅ Test de connexion réussi")
            
            # Vérifier la version MongoDB
            server_info = test_client.server_info()
            print(f"✅ MongoDB version {server_info.get('version', 'Inconnue')}")
            
            test_client.close()
            return True
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False

    def connect(self) -> bool:
        """Établir la connexion à MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
            self.create_indexes()
            print("✅ Connexion à MongoDB établie")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False

    def create_indexes(self):
        """Créer les index basés sur la configuration"""
        try:
            # Index unique sur la référence
            if 'reference' in self.config['indexes']['unique']:
                self.db.annonces.create_index("reference", unique=True)
                print("✅ Index unique créé sur 'reference'")
            
            # Index de recherche
            for field in self.config['indexes']['searchable']:
                self.db.annonces.create_index(field)
                print(f"✅ Index créé sur '{field}'")
            
            # Index de range pour les champs numériques
            for field in self.config['indexes']['range']:
                self.db.annonces.create_index(field)
                print(f"✅ Index de range créé sur '{field}'")
                
            # Index sur la date d'extraction pour les requêtes temporelles
            self.db.annonces.create_index([("metadata.date_extraction", -1)])
            print("✅ Index temporel créé sur 'metadata.date_extraction'")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la création des index: {e}")

    def disconnect(self):
        """Fermer la connexion"""
        if self.client:
            self.client.close()
        print("✅ Connexion fermée")

    def validate_annonce(self, annonce_data: Dict[str, Any]) -> bool:
        """Valider une annonce selon les règles de configuration"""
        
        # Vérifier les champs requis
        for field in self.config['validation_rules']['required_fields']:
            if not self.get_nested_value(annonce_data, field):
                print(f"❌ Champ requis manquant: {field}")
                return False
        
        # Vérifier la référence
        reference = annonce_data.get('reference', '').strip()
        if not reference:
            print("❌ Référence manquante")
            return False
            
        return True

    def get_nested_value(self, data: Dict, path: str) -> Any:
        """Obtenir une valeur imbriquée à partir d'un chemin"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def transform_dates(self, annonce_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformer les champs de date en objets datetime"""
        transformed = annonce_data.copy()
        
        for date_field in self.config['validation_rules']['date_fields']:
            date_value = self.get_nested_value(annonce_data, date_field)
            if date_value:
                try:
                    # Mettre à jour la valeur dans la structure imbriquée
                    keys = date_field.split('.')
                    current = transformed
                    for key in keys[:-1]:
                        current = current.setdefault(key, {})
                    current[keys[-1]] = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except ValueError as e:
                    print(f"⚠️ Erreur conversion date {date_field}: {e}")
        
        return transformed

    def process_annonce(self, annonce_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter une annonce pour l'insertion"""
        
        if not self.validate_annonce(annonce_data):
            raise ValueError("Annonce invalide")
        
        # Transformer les dates
        processed_data = self.transform_dates(annonce_data)
        
        # Ajouter la date d'import
        processed_data['date_import'] = datetime.now()
        
        return processed_data

    def insert_annonce(self, annonce_data: Dict[str, Any]) -> bool:
        """Insérer une annonce dans MongoDB"""
        
        try:
            reference = annonce_data.get('reference', '').strip()
            print(f"📝 Traitement annonce: {reference}")
            
            # Traiter l'annonce
            processed_data = self.process_annonce(annonce_data)
            
            # Insérer dans MongoDB
            result = self.db.annonces.insert_one(processed_data)
            
            # Afficher les informations principales
            prix = self.get_nested_value(annonce_data, 'prix.valeur')
            surface = self.get_nested_value(annonce_data, 'surface.valeur')
            localisation = self.get_nested_value(annonce_data, 'localisation.ville')
            type_bien = self.get_nested_value(annonce_data, 'composition.type_bien')
            
            if prix:
                print(f"   💰 Prix: {prix:,.0f}€")
            if surface:
                print(f"   📏 Surface: {surface}m²")
            if localisation:
                print(f"   📍 Localisation: {localisation}")
            if type_bien:
                print(f"   🏠 Type: {type_bien}")
            
            print(f"   ✅ Insertion réussie (ID: {result.inserted_id})")
            return True
            
        except DuplicateKeyError:
            print(f"   ⏭️  Annonce {reference} déjà existante, ignorée")
            return False
        except ValueError as e:
            print(f"   ❌ Erreur validation: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Erreur insertion: {e}")
            return False

    def process_json_file(self, json_file_path: str):
        """Traiter un fichier JSON complet"""
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if not isinstance(data, list):
                print("❌ Le fichier JSON doit contenir un tableau d'annonces")
                return
            
            print(f"📁 Fichier JSON chargé: {len(data)} annonces trouvées")
            
            inserted_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, annonce_data in enumerate(data, 1):
                print(f"\n--- Annonce {i}/{len(data)} ---")
                
                if self.insert_annonce(annonce_data):
                    inserted_count += 1
                else:
                    error_count += 1
            
            # Résumé final
            self.show_final_summary(inserted_count, skipped_count, error_count, len(data))
            
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {json_file_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON: {e}")
        except Exception as e:
            print(f"❌ Erreur lors du traitement: {e}")

    def show_final_summary(self, inserted: int, skipped: int, errors: int, total: int):
        """Afficher le résumé final"""
        print(f"\n{'='*60}")
        print("🎉 IMPORT TERMINÉ - RÉCAPITULATIF")
        print(f"{'='*60}")
        print(f"✅ {inserted} nouvelles annonces insérées")
        print(f"⏭️  {skipped} annonces déjà existantes")
        print(f"❌ {errors} annonces en erreur")
        print(f"📊 Total traité: {total} annonces")
        
        # Afficher les statistiques de la base
        self.show_database_stats()

    def show_database_stats(self):
        """Afficher les statistiques de la base de données"""
        try:
            total_annonces = self.db.annonces.count_documents({})
            
            print(f"\n📊 STATISTIQUES DE LA BASE:")
            print(f"   • Total annonces: {total_annonces}")
            
            # Statistiques par type de bien
            pipeline_type = [
                {"$group": {"_id": "$composition.type_bien", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            types_biens = list(self.db.annonces.aggregate(pipeline_type))
            if types_biens:
                print(f"\n🏠 RÉPARTITION PAR TYPE DE BIEN:")
                for type_bien in types_biens[:5]:
                    type_name = type_bien['_id'] or 'Non spécifié'
                    print(f"   • {type_name}: {type_bien['count']}")
            
            # Statistiques par ville
            pipeline_ville = [
                {"$group": {"_id": "$localisation.ville", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            villes = list(self.db.annonces.aggregate(pipeline_ville))
            if villes:
                print(f"\n📍 TOP 5 VILLES:")
                for ville in villes:
                    ville_name = ville['_id'] or 'Non spécifié'
                    print(f"   • {ville_name}: {ville['count']}")
            
            # Prix moyen
            pipeline_prix = [
                {"$match": {"prix.valeur": {"$ne": None}}},
                {"$group": {"_id": None, "prix_moyen": {"$avg": "$prix.valeur"}}}
            ]
            prix_moyen = list(self.db.annonces.aggregate(pipeline_prix))
            if prix_moyen and prix_moyen[0]['prix_moyen']:
                print(f"\n💰 Prix moyen: {prix_moyen[0]['prix_moyen']:,.0f}€")
                
        except Exception as e:
            print(f"⚠️ Impossible de récupérer les statistiques: {e}")

def main():
    """Fonction principale"""
    
    print("🏠 IMPORTATEUR D'ANNONCES AGRÉGÉES - MONGODB")
    print("=" * 60)
    
    # Fichiers
    config_file = "config_aggreges.json"
    json_file_path = "annonces_agregees.json"
    
    # Vérifications
    if not os.path.exists(config_file):
        print(f"❌ Fichier de configuration non trouvé: {config_file}")
        sys.exit(1)
        
    if not os.path.exists(json_file_path):
        print(f"❌ Fichier de données non trouvé: {json_file_path}")
        print("💡 Placez votre fichier JSON dans le même dossier")
        sys.exit(1)
    
    # Initialiser l'importateur
    importer = MongoDBImporterAggrege(config_file)
    
    # Test de connexion
    if not importer.test_connection():
        print("\n❌ Impossible de continuer sans connexion valide")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    try:
        # Établir la connexion
        if not importer.connect():
            sys.exit(1)
        
        # Traiter le fichier
        importer.process_json_file(json_file_path)
        
    except KeyboardInterrupt:
        print("\n⏹️  Import interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    finally:
        importer.disconnect()

if __name__ == "__main__":
    main()