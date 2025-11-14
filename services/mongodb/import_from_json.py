import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError, BulkWriteError

class CompleteDataToMongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.load_environment_variables()
        
    def load_environment_variables(self):
        """Charger les variables d'environnement depuis le fichier .env"""
        load_dotenv()
        
        # Configuration MongoDB
        self.mongo_config = {
            'username': os.getenv('MONGO_ROOT_USERNAME', 'admin'),
            'password': os.getenv('MONGO_ROOT_PASSWORD', 'password'),
            'database': os.getenv('MONGO_DATABASE', 'imo_db'),
            'port': os.getenv('MONGO_PORT', '27017'),
            'host': os.getenv('MONGO_HOST', 'localhost')
        }
        
        # URL de connexion pour affichage (masqué)
        mongo_url_masked = f"mongodb://{self.mongo_config['username']}:[masqué]@{self.mongo_config['host']}:{self.mongo_config['port']}/{self.mongo_config['database']}"
        print(f"🔗 URL de connexion MongoDB: {mongo_url_masked}")
        
    def test_connection(self) -> bool:
        """Tester la connexion à MongoDB"""
        print("🔍 Test de connexion à MongoDB...")
        
        try:
            test_client = MongoClient(
                host=self.mongo_config['host'],
                port=int(self.mongo_config['port']),
                username=self.mongo_config['username'],
                password=self.mongo_config['password'],
                authSource='admin'
            )
            
            # Test de connexion
            test_client.admin.command('ismaster')
            print("✅ Test de connexion MongoDB réussi")
            
            # Vérifier que la base existe ou peut être créée
            db_list = test_client.list_database_names()
            if self.mongo_config['database'] in db_list:
                print(f"✅ Base de données '{self.mongo_config['database']}' trouvée")
            else:
                print(f"⚠️  Base de données '{self.mongo_config['database']}' sera créée")
            
            test_client.close()
            return True
            
        except ConnectionFailure as e:
            print(f"❌ Erreur de connexion MongoDB: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur lors du test MongoDB: {e}")
            return False

    def connect(self) -> bool:
        """Établir la connexion à MongoDB"""
        try:
            self.client = MongoClient(
                host=self.mongo_config['host'],
                port=int(self.mongo_config['port']),
                username=self.mongo_config['username'],
                password=self.mongo_config['password'],
                authSource='admin'
            )
            
            # Sélectionner la base de données
            self.db = self.client[self.mongo_config['database']]
            
            # Tester la connexion
            self.client.admin.command('ismaster')
            print("✅ Connexion MongoDB établie")
            return True
            
        except ConnectionFailure as e:
            print(f"❌ Erreur de connexion MongoDB: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False

    def disconnect(self):
        """Fermer la connexion"""
        if self.client:
            self.client.close()
        print("✅ Connexion MongoDB fermée")

    def setup_database(self):
        """Configurer la base de données (index, validation, etc.)"""
        print("⚙️  Configuration de la base de données MongoDB...")
        
        try:
            # Collection des annonces
            annonces_collection = self.db['annonces']
            
            # Créer les index pour les annonces
            annonces_collection.create_index([("reference", ASCENDING)], unique=True, name="reference_unique")
            annonces_collection.create_index([("prix.valeur", ASCENDING)], name="prix_index")
            annonces_collection.create_index([("localisation.code_postal", ASCENDING)], name="code_postal_index")
            annonces_collection.create_index([("batiment.age_bien", ASCENDING)], name="age_bien_index")
            annonces_collection.create_index([("diagnostics.dpe.score", ASCENDING)], name="dpe_score_index")
            annonces_collection.create_index([("aggregats.scores.global", DESCENDING)], name="score_global_index")
            
            print("✅ Index créés pour la collection 'annonces'")
            
            # Collection des statistiques de marché
            stats_collection = self.db['stats_marche']
            stats_collection.create_index([("date_calcul", DESCENDING)], name="date_calcul_index")
            
            print("✅ Index créés pour la collection 'stats_marche'")
            
            # Collection des historiques
            historique_collection = self.db['historique_prix']
            historique_collection.create_index([("reference", ASCENDING), ("date_analyse", DESCENDING)], name="ref_date_index")
            
            print("✅ Index créés pour la collection 'historique_prix'")
            
        except Exception as e:
            print(f"⚠️  Erreur lors de la configuration: {e}")

    def check_existing_reference(self, reference: str) -> bool:
        """Vérifier si une référence existe déjà"""
        try:
            count = self.db['annonces'].count_documents({"reference": reference})
            return count > 0
        except Exception as e:
            print(f"❌ Erreur vérification référence {reference}: {e}")
            return False

    def transform_data_for_mongodb(self, complete_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformer les données pour l'insertion MongoDB"""
        
        # Créer une copie pour modification
        transformed_data = complete_data.copy()
        
        # Ajouter des métadonnées MongoDB
        transformed_data['_created_at'] = datetime.now()
        transformed_data['_updated_at'] = datetime.now()
        transformed_data['_version'] = 1
        
        # Structurer les données agrégées directement dans le document
        aggregats_data = transformed_data.get('aggregats', {})
        
        # Fusionner les performances dans les agrégats
        if 'performance' in aggregats_data:
            transformed_data['aggregats']['performance_financiere'] = aggregats_data['performance']
            del transformed_data['aggregats']['performance']
        
        # Ajouter un champ calculé pour la recherche
        if 'localisation' in transformed_data:
            localisation = transformed_data['localisation']
            if isinstance(localisation, dict):
                transformed_data['recherche_texte'] = ' '.join([
                    str(localisation.get('ville', '')),
                    str(localisation.get('quartier', '')),
                    str(localisation.get('code_postal', '')),
                    transformed_data.get('description', '')
                ]).strip()
        
        # Calculer un score de recherche
        score_recherche = 0
        if transformed_data.get('prix', {}).get('valeur'):
            score_recherche += 10
        if transformed_data.get('surface', {}).get('valeur'):
            score_recherche += 10
        if transformed_data.get('localisation', {}).get('code_postal'):
            score_recherche += 15
        if transformed_data.get('diagnostics', {}).get('dpe', {}).get('score'):
            score_recherche += 5
        if transformed_data.get('aggregats', {}).get('scores', {}).get('global'):
            score_recherche += 10
        
        transformed_data['score_recherche'] = score_recherche
        
        return transformed_data

    def insert_complete_annonce(self, complete_data: Dict[str, Any]) -> bool:
        """Insérer une annonce complète dans MongoDB"""
        
        reference = complete_data.get('reference', '').strip()
        if not reference:
            print("❌ Annonce sans référence, ignorée")
            return False
        
        print(f"📝 Traitement de l'annonce: {reference}")
        
        # Vérifier si la référence existe déjà
        if self.check_existing_reference(reference):
            print("⏭️  Annonce déjà existante, mise à jour...")
            return self.update_existing_annonce(reference, complete_data)
        
        # Afficher les infos principales
        prix_data = complete_data.get('prix', {})
        surface_data = complete_data.get('surface', {})
        localisation_data = complete_data.get('localisation', {})
        aggregats_data = complete_data.get('aggregats', {})
        
        if prix_data.get('valeur'):
            print(f"💰 Prix: {prix_data['valeur']:,.2f}€")
        if surface_data.get('valeur'):
            print(f"📏 Surface: {surface_data['valeur']}m²")
        if localisation_data.get('ville'):
            print(f"📍 Localisation: {localisation_data['ville']} {localisation_data.get('code_postal', '')}")
        if aggregats_data.get('scores', {}).get('global'):
            print(f"🎯 Score global: {aggregats_data['scores']['global']}/10")
        
        try:
            # Transformer les données pour MongoDB
            document = self.transform_data_for_mongodb(complete_data)
            
            # Insérer dans la collection annonces
            result = self.db['annonces'].insert_one(document)
            
            print(f"✅ Annonce {reference} insérée (ID: {result.inserted_id})")
            
            # Insérer également dans l'historique des prix
            self.insert_historique_prix(reference, prix_data, aggregats_data)
            
            return True
            
        except DuplicateKeyError:
            print(f"⏭️  Duplicata détecté pour {reference}, mise à jour...")
            return self.update_existing_annonce(reference, complete_data)
        except Exception as e:
            print(f"❌ Erreur insertion annonce {reference}: {e}")
            return False

    def update_existing_annonce(self, reference: str, new_data: Dict[str, Any]) -> bool:
        """Mettre à jour une annonce existante"""
        try:
            # Transformer les nouvelles données
            updated_document = self.transform_data_for_mongodb(new_data)
            updated_document['_updated_at'] = datetime.now()
            
            # Incrémenter la version
            result = self.db['annonces'].update_one(
                {"reference": reference},
                {
                    "$set": updated_document,
                    "$inc": {"_version": 1}
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Annonce {reference} mise à jour")
                
                # Mettre à jour l'historique des prix
                prix_data = new_data.get('prix', {})
                aggregats_data = new_data.get('aggregats', {})
                self.insert_historique_prix(reference, prix_data, aggregats_data)
                
                return True
            else:
                print(f"⚠️  Aucune modification pour {reference}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur mise à jour annonce {reference}: {e}")
            return False

    def insert_historique_prix(self, reference: str, prix_data: Dict[str, Any], aggregats_data: Dict[str, Any]):
        """Insérer un enregistrement dans l'historique des prix"""
        try:
            historique_doc = {
                "reference": reference,
                "date_analyse": datetime.now(),
                "prix": prix_data.get('valeur'),
                "prix_m2": prix_data.get('au_m2'),
                "positionnement_marche": aggregats_data.get('analyse_marche', {}).get('positionnement_marche'),
                "score_global": aggregats_data.get('scores', {}).get('global'),
                "segment_marche": aggregats_data.get('segmentation', {}).get('prix_m2')
            }
            
            self.db['historique_prix'].insert_one(historique_doc)
            
        except Exception as e:
            print(f"⚠️  Erreur insertion historique prix {reference}: {e}")

    def calculate_marche_stats(self):
        """Calculer les statistiques globales du marché"""
        try:
            print("📊 Calcul des statistiques du marché...")
            
            pipeline = [
                # Étape 1: Filtrer les documents valides
                {
                    "$match": {
                        "prix.valeur": {"$exists": True, "$gt": 0},
                        "surface.valeur": {"$exists": True, "$gt": 0}
                    }
                },
                
                # Étape 2: Calculer le prix au m²
                {
                    "$addFields": {
                        "prix_m2_calcule": {
                            "$divide": ["$prix.valeur", "$surface.valeur"]
                        }
                    }
                },
                
                # Étape 3: Regrouper pour les statistiques
                {
                    "$group": {
                        "_id": None,
                        "nombre_annonces": {"$sum": 1},
                        "prix_moyen": {"$avg": "$prix.valeur"},
                        "prix_median": {"$median": {"input": "$prix.valeur", "method": "approximate"}},
                        "prix_min": {"$min": "$prix.valeur"},
                        "prix_max": {"$max": "$prix.valeur"},
                        "surface_moyenne": {"$avg": "$surface.valeur"},
                        "prix_m2_moyen": {"$avg": "$prix_m2_calcule"},
                        "prix_m2_median": {"$median": {"input": "$prix_m2_calcule", "method": "approximate"}},
                        "arrondissements": {"$addToSet": "$localisation.code_postal"},
                        "types_biens": {"$addToSet": "$composition.type_bien"}
                    }
                },
                
                # Étape 4: Projeter le résultat final
                {
                    "$project": {
                        "_id": 0,
                        "date_calcul": datetime.now(),
                        "periode": "instantanee",
                        "nombre_annonces": 1,
                        "prix_moyen": {"$round": ["$prix_moyen", 2]},
                        "prix_median": {"$round": ["$prix_median", 2]},
                        "prix_min": 1,
                        "prix_max": 1,
                        "surface_moyenne": {"$round": ["$surface_moyenne", 2]},
                        "prix_m2_moyen": {"$round": ["$prix_m2_moyen", 2]},
                        "prix_m2_median": {"$round": ["$prix_m2_median", 2]},
                        "arrondissements_couverts": "$arrondissements",
                        "types_biens_analysees": "$types_biens"
                    }
                }
            ]
            
            result = list(self.db['annonces'].aggregate(pipeline))
            
            if result:
                stats_doc = result[0]
                
                # Calculer la distribution par segments de prix
                segments_pipeline = [
                    {
                        "$match": {
                            "aggregats.segmentation.prix_m2": {"$exists": True}
                        }
                    },
                    {
                        "$group": {
                            "_id": "$aggregats.segmentation.prix_m2",
                            "count": {"$sum": 1}
                        }
                    }
                ]
                
                segments_result = list(self.db['annonces'].aggregate(segments_pipeline))
                distribution_segments = {seg['_id']: seg['count'] for seg in segments_result if seg['_id']}
                
                stats_doc['distribution_segments'] = distribution_segments
                
                # Insérer les statistiques
                self.db['stats_marche'].insert_one(stats_doc)
                print("✅ Statistiques du marché calculées et sauvegardées")
                
                return stats_doc
            else:
                print("⚠️  Aucune donnée pour calculer les statistiques")
                return None
                
        except Exception as e:
            print(f"❌ Erreur calcul statistiques marché: {e}")
            return None

    def create_sample_queries(self):
        """Créer des exemples de requêtes utiles"""
        print("🔍 Création d'exemples de requêtes...")
        
        queries = {
            "biens_sous_cotes": {
                "collection": "annonces",
                "query": {
                    "aggregats.analyse_marche.positionnement_marche": {
                        "$in": ["tres_sous_cote", "sous_cote"]
                    }
                },
                "projection": {
                    "reference": 1,
                    "titre": 1,
                    "prix.valeur": 1,
                    "aggregats.analyse_marche.ecart_pourcentage": 1,
                    "aggregats.scores.global": 1
                },
                "sort": [("aggregats.analyse_marche.ecart_pourcentage", ASCENDING)]
            },
            "meilleurs_rendements": {
                "collection": "annonces",
                "query": {
                    "aggregats.performance_financiere.rendement_annuel_estime": {"$gt": 6}
                },
                "projection": {
                    "reference": 1,
                    "titre": 1,
                    "aggregats.performance_financiere.rendement_annuel_estime": 1,
                    "prix.valeur": 1
                },
                "sort": [("aggregats.performance_financiere.rendement_annuel_estime", DESCENDING)]
            },
            "biens_reecents_haute_qualite": {
                "collection": "annonces",
                "query": {
                    "batiment.age_bien": {"$lt": 10},
                    "aggregats.scores.global": {"$gt": 8}
                },
                "projection": {
                    "reference": 1,
                    "titre": 1,
                    "batiment.age_bien": 1,
                    "aggregats.scores.global": 1,
                    "localisation.ville": 1
                },
                "sort": [("aggregats.scores.global", DESCENDING)]
            }
        }
        
        # Sauvegarder les requêtes
        self.db['requetes_predefinies'].insert_one({
            "nom": "Requêtes d'analyse immobilière",
            "description": "Collection de requêtes utiles pour l'analyse de marché",
            "requetes": queries,
            "date_creation": datetime.now()
        })
        
        print("✅ Exemples de requêtes créés")

    def process_json_file(self, json_file_path: str, batch_size: int = 50):
        """Traiter un fichier JSON complet"""
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📁 Fichier JSON chargé: {len(data)} annonces trouvées")
            print(f"⚡ Taille des lots: {batch_size} annonces")
            
            inserted_count = 0
            updated_count = 0
            error_count = 0
            
            # Traitement par lots pour meilleures performances
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                print(f"\n--- Traitement du lot {i//batch_size + 1}/{(len(data)-1)//batch_size + 1} ---")
                
                for j, complete_data in enumerate(batch, 1):
                    annonce_num = i + j
                    print(f"\n--- Annonce {annonce_num}/{len(data)} ---")
                    
                    try:
                        success = self.insert_complete_annonce(complete_data)
                        if success:
                            if self.check_existing_reference(complete_data.get('reference', '')):
                                updated_count += 1
                            else:
                                inserted_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        print(f"❌ Erreur lors du traitement: {e}")
                        error_count += 1
            
            # Résumé final
            print(f"\n{'='*60}")
            print("🎉 IMPORTATION MONGODB TERMINÉE - RÉCAPITULATIF")
            print(f"{'='*60}")
            print(f"✅ {inserted_count} nouvelles annonces insérées")
            print(f"🔄 {updated_count} annonces mises à jour")
            print(f"❌ {error_count} annonces en erreur")
            print(f"📊 Total traité: {len(data)} annonces")
            
            # Calculer les statistiques du marché
            self.calculate_marche_stats()
            
            # Créer des exemples de requêtes
            self.create_sample_queries()
            
            # Afficher les statistiques finales
            self.show_final_stats()
            
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {json_file_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de décodage JSON: {e}")
        except Exception as e:
            print(f"❌ Erreur lors du traitement du fichier: {e}")

    def show_final_stats(self):
        """Afficher les statistiques finales"""
        try:
            # Statistiques des collections
            collections = ['annonces', 'historique_prix', 'stats_marche', 'requetes_predefinies']
            
            print(f"\n📊 STATISTIQUES DE LA BASE MONGODB:")
            for collection_name in collections:
                count = self.db[collection_name].count_documents({})
                print(f"   • {collection_name}: {count} documents")
            
            # Statistiques avancées des annonces
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "prix_moyen": {"$avg": "$prix.valeur"},
                        "surface_moyenne": {"$avg": "$surface.valeur"},
                        "score_moyen": {"$avg": "$aggregats.scores.global"},
                        "dpe_moyen": {"$avg": "$diagnostics.dpe.score"},
                        "biens_sous_cotes": {
                            "$sum": {
                                "$cond": [
                                    {"$in": ["$aggregats.analyse_marche.positionnement_marche", ["tres_sous_cote", "sous_cote"]]},
                                    1, 0
                                ]
                            }
                        },
                        "biens_sur_cotes": {
                            "$sum": {
                                "$cond": [
                                    {"$in": ["$aggregats.analyse_marche.positionnement_marche", ["tres_sur_cote", "sur_cote"]]},
                                    1, 0
                                ]
                            }
                        }
                    }
                }
            ]
            
            result = list(self.db['annonces'].aggregate(pipeline))
            if result:
                stats = result[0]
                print(f"\n📈 STATISTIQUES AVANCÉES:")
                print(f"   • Prix moyen: {stats.get('prix_moyen', 0):,.2f}€")
                print(f"   • Surface moyenne: {stats.get('surface_moyenne', 0):.1f}m²")
                print(f"   • Score global moyen: {stats.get('score_moyen', 0):.1f}/10")
                print(f"   • Score DPE moyen: {stats.get('dpe_moyen', 0):.1f}/10")
                print(f"   • Biens sous-cotés: {stats.get('biens_sous_cotes', 0)}")
                print(f"   • Biens sur-cotés: {stats.get('biens_sur_cotes', 0)}")
            
            # Top 5 des meilleurs scores
            best_annonces = list(self.db['annonces'].find(
                {"aggregats.scores.global": {"$exists": True}},
                {
                    "reference": 1,
                    "titre": 1,
                    "aggregats.scores.global": 1,
                    "prix.valeur": 1,
                    "localisation.ville": 1
                }
            ).sort("aggregats.scores.global", DESCENDING).limit(5))
            
            print(f"\n🏆 TOP 5 DES MEILLEURES ANNONCES:")
            for i, annonce in enumerate(best_annonces, 1):
                print(f"   {i}. {annonce.get('reference')} - Score: {annonce.get('aggregats', {}).get('scores', {}).get('global', 'N/A')}/10")
            
        except Exception as e:
            print(f"⚠️  Impossible de récupérer les statistiques: {e}")

def main():
    """Fonction principale"""
    
    print("🏠 IMPORTATEUR COMPLET MONGODB")
    print("=" * 60)
    print("📁 Ce script importe TOUTES les données dans MongoDB")
    print("   → Structure document optimisée pour les requêtes")
    print("   → Historique des prix et statistiques automatiques")
    print("   → Requêtes pré-définies pour l'analyse")
    print("=" * 60)
    
    # Chemin vers le fichier JSON complet
    json_file_path = 'annonces_aggregees.json'
    
    # Vérifier si le fichier existe
    if not os.path.exists(json_file_path):
        print(f"❌ Fichier {json_file_path} non trouvé")
        print("💡 Assurez-vous d'avoir exécuté le script d'agrégation d'abord")
        sys.exit(1)
    
    # Initialiser le processeur
    processor = CompleteDataToMongoDB()
    
    # Test de connexion préalable
    if not processor.test_connection():
        print("\n❌ Impossible de continuer sans connexion valide à MongoDB")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    try:
        # Établir la connexion principale
        if not processor.connect():
            sys.exit(1)
        
        # Configurer la base de données
        processor.setup_database()
        
        # Traiter le fichier JSON complet
        processor.process_json_file(json_file_path, batch_size=50)
        
    except KeyboardInterrupt:
        print("\n⏹️  Import interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    finally:
        # Fermer la connexion
        processor.disconnect()

if __name__ == "__main__":
    main()