import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

class MongoDBImporterAggrege:
    def __init__(self, config_file: str = None):
        self.client = None
        self.db = None
        self.config = None
        self.load_environment_variables()
        
        # Utiliser le chemin du .env ou valeur par défaut
        if config_file is None:
            config_file = self.config_path
            
        self.load_config(config_file)
        
    def load_environment_variables(self):
        """Charger les variables d'environnement depuis .env"""
        load_dotenv()
        
        # Chemins des fichiers depuis .env
        self.config_path = os.getenv('CONFIG_FILE_PATH', 'config/config_aggreges.json')
        self.data_path = os.getenv('DATA_FILE_PATH', 'data/annonces_agregees.json')
        self.logs_dir = os.getenv('LOGS_DIRECTORY', 'logs')
        
        # Configuration MongoDB depuis .env
        mongo_host = os.getenv('MONGO_HOST', 'mongodb')  # 'mongodb' = nom du service
        mongo_port = os.getenv('MONGO_PORT', '27017')
        mongo_db = os.getenv('MONGO_DB', os.getenv('MONGO_DATABASE', 'imo_agrege'))  # Fallback
        mongo_user = os.getenv('MONGO_USER', os.getenv('MONGO_ROOT_USERNAME'))  # Fallback
        mongo_password = os.getenv('MONGO_PASSWORD', os.getenv('MONGO_ROOT_PASSWORD'))  # Fallback
        
        # Validation critique
        if not mongo_db or mongo_db.strip() == "":
            print("❌ ERREUR CRITIQUE: Le nom de la base de données est vide!")
            sys.exit(1)
        
        if not mongo_user or not mongo_password:
            print("❌ ERREUR CRITIQUE: Identifiants MongoDB manquants!")
            sys.exit(1)
        
        # Construction de l'URL de connexion avec authSource
        self.connection_string = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin"
        db_url_masked = f"mongodb://{mongo_user}:[masqué]@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin"
            
        print(f"🔗 URL de connexion MongoDB: {db_url_masked}")
        print(f"📊 Base de données: {mongo_db}")
        self.db_name = mongo_db
        
        # Affichage des chemins configurés
        print(f"📁 Chemin configuration: {self.config_path}")
        print(f"📁 Chemin données: {self.data_path}")
        print(f"📁 Répertoire logs: {self.logs_dir}")
        
        # Création du répertoire de logs si nécessaire
        os.makedirs(self.logs_dir, exist_ok=True)
        
    def load_config(self, config_file: str):
        """Charger la configuration depuis le fichier JSON"""
        try:
            # Vérifier si le chemin est absolu ou relatif
            if not os.path.isabs(config_file):
                config_file = os.path.join(os.getcwd(), config_file)
                
            print(f"🔍 Recherche du fichier de configuration: {config_file}")
                
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✅ Configuration chargée: {config_file}")
        except FileNotFoundError:
            print(f"❌ Fichier de configuration non trouvé: {config_file}")
            print("💡 Vérifiez la variable CONFIG_FILE_PATH dans votre .env")
            print("💡 Structure attendue:")
            print("   - /app/config/config_aggreges.json (dans conteneur)")
            print("   - ./config/config_aggreges.json (sur l'hôte)")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON dans {config_file}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur lors du chargement de la configuration: {e}")
            sys.exit(1)

    def setup_logging(self):
        """Configurer le système de logging"""
        import logging
        
        log_file = os.path.join(self.logs_dir, f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        print(f"📝 Logs enregistrés dans: {log_file}")

    def test_connection(self) -> bool:
        """Tester la connexion à MongoDB"""
        print("🔍 Test de connexion à MongoDB...")
        
        try:
            # Timeout réduit pour les tests
            test_client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            test_client.admin.command('ping')
            print("✅ Test de connexion réussi")
            
            # Vérifier la version MongoDB
            server_info = test_client.server_info()
            print(f"✅ MongoDB version {server_info.get('version', 'Inconnue')}")
            
            # Vérifier que la base existe ou peut être créée
            db_list = test_client.list_database_names()
            if self.db_name in db_list:
                print(f"✅ Base de données '{self.db_name}' existe")
            else:
                print(f"ℹ️  Base de données '{self.db_name}' sera créée à la première insertion")
            
            test_client.close()
            return True
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            print("💡 Vérifiez que:")
            print("   - MongoDB est démarré")
            print("   - Les identifiants sont corrects")
            print("   - Le réseau est accessible")
            return False

    def connect(self) -> bool:
        """Établir la connexion à MongoDB"""
        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=10000)
            self.db = self.client[self.db_name]
            
            # Tester l'accès à la base
            self.db.command('ping')
            
            self.create_indexes()
            print("✅ Connexion à MongoDB établie")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False

    def create_indexes(self):
        """Créer les index basés sur la configuration"""
        try:
            # Vérifier que la configuration des index existe
            if 'indexes' not in self.config:
                print("⚠️ Aucune configuration d'index trouvée")
                return
                
            # Index unique sur la référence
            if 'unique' in self.config['indexes'] and 'reference' in self.config['indexes']['unique']:
                self.db.annonces.create_index("reference", unique=True)
                print("✅ Index unique créé sur 'reference'")
            
            # Index de recherche
            if 'searchable' in self.config['indexes']:
                for field in self.config['indexes']['searchable']:
                    self.db.annonces.create_index(field)
                    print(f"✅ Index créé sur '{field}'")
            
            # Index de range pour les champs numériques
            if 'range' in self.config['indexes']:
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
        # Vérifier que les règles de validation existent
        if 'validation_rules' not in self.config:
            print("⚠️ Aucune règle de validation trouvée dans la configuration")
            return True
            
        # Vérifier les champs requis
        required_fields = self.config['validation_rules'].get('required_fields', [])
        for field in required_fields:
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
        
        # Vérifier que les champs de date sont configurés
        if 'validation_rules' not in self.config or 'date_fields' not in self.config['validation_rules']:
            return transformed
            
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
                except (ValueError, AttributeError) as e:
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
        
        # Ajouter des métadonnées si elles n'existent pas
        if 'metadata' not in processed_data:
            processed_data['metadata'] = {}
        processed_data['metadata']['imported_at'] = datetime.now()
        
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

    def process_json_file(self, json_file_path: str = None):
        """Traiter un fichier JSON complet"""
        
        # Utiliser le chemin du .env si non spécifié
        if json_file_path is None:
            json_file_path = self.data_path
            
        try:
            # Vérifier si le chemin est absolu ou relatif
            if not os.path.isabs(json_file_path):
                json_file_path = os.path.join(os.getcwd(), json_file_path)
                
            print(f"📁 Chargement du fichier: {json_file_path}")
            
            # Vérifier que le fichier existe
            if not os.path.exists(json_file_path):
                raise FileNotFoundError(f"Fichier non trouvé: {json_file_path}")
            
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
                
                success = self.insert_annonce(annonce_data)
                if success:
                    inserted_count += 1
                else:
                    error_count += 1
            
            # Résumé final
            self.show_final_summary(inserted_count, skipped_count, error_count, len(data))
            
        except FileNotFoundError as e:
            print(f"❌ Fichier non trouvé: {e}")
            print("💡 Vérifiez la variable DATA_FILE_PATH dans votre .env")
            print("💡 Structure attendue:")
            print("   - /app/data/annonces_agregees.json (dans conteneur)")
            print("   - ./data/annonces_agregees.json (sur l'hôte)")
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
    
    # Initialiser l'importateur avec configuration depuis .env
    importer = MongoDBImporterAggrege()
    
    # Test de connexion
    if not importer.test_connection():
        print("\n❌ Impossible de continuer sans connexion valide")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    try:
        # Établir la connexion
        if not importer.connect():
            sys.exit(1)
        
        # Traiter le fichier (chemin automatique depuis .env)
        importer.process_json_file()
        
    except KeyboardInterrupt:
        print("\n⏹️  Import interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    finally:
        importer.disconnect()

if __name__ == "__main__":
    main()