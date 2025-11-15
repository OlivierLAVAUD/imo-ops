import json
import re
import psycopg2
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

class AggregatedDataToPostgreSQL:
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
        db_name = os.getenv('IMO_DB') or os.getenv('DB_NAME', 'imo_db')
        db_user = os.getenv('IMOtgres')
        db_password = os.getenv('IMOD', 'password')
        
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
            
            # Vérifier les tables d'agrégats
            try:
                test_cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('aggregats_principaux', 'performance_financiere', 'scores_avances', 
                                     'segmentation', 'analyse_marche', 'recommandations')
                """)
                tables = [row[0] for row in test_cur.fetchall()]
                
                required_tables = ['aggregats_principaux', 'performance_financiere', 'scores_avances', 
                                 'segmentation', 'analyse_marche', 'recommandations']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    print(f"❌ Tables d'agrégats manquantes: {', '.join(missing_tables)}")
                    return False
                else:
                    print("✅ Toutes les tables d'agrégats sont présentes")
                    
            except Exception as e:
                print(f"⚠️  Impossible de vérifier les tables d'agrégats: {e}")
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

    def get_annonce_id_by_reference(self, reference: str) -> Optional[int]:
        """Récupérer l'ID d'une annonce par sa référence"""
        try:
            query = "SELECT id_annonce FROM annonces WHERE reference = %s"
            self.cur.execute(query, (reference,))
            result = self.cur.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Erreur récupération ID annonce {reference}: {e}")
            return None

    def check_existing_aggregat(self, annonce_id: int) -> bool:
        """Vérifier si un agrégat existe déjà pour cette annonce"""
        try:
            query = "SELECT 1 FROM aggregats_principaux WHERE id_annonce = %s"
            self.cur.execute(query, (annonce_id,))
            exists = self.cur.fetchone() is not None
            return exists
        except Exception as e:
            print(f"❌ Erreur vérification agrégat annonce {annonce_id}: {e}")
            return False

    def determiner_niveau_rendement(self, rendement: float) -> str:
        """Déterminer le niveau de rendement"""
        if rendement >= 8:
            return "eleve"
        elif rendement >= 5:
            return "moyen"
        else:
            return "faible"

    def determiner_ratio_rentabilite(self, rentabilite_nette: float) -> str:
        """Déterminer le ratio de rentabilité"""
        if rentabilite_nette >= 6:
            return "excellent"
        elif rentabilite_nette >= 4:
            return "bon"
        elif rentabilite_nette >= 2:
            return "acceptable"
        else:
            return "faible"

    def determiner_segment_cible(self, segment_data: Dict[str, Any], batiment_data: Dict[str, Any]) -> str:
        """Déterminer le segment cible"""
        age_bien = batiment_data.get('age_bien')
        ascenseur = batiment_data.get('ascenseur', False)
        etage = batiment_data.get('etage')
        
        if age_bien and age_bien < 10:
            return "investisseurs_neuf"
        elif segment_data.get('segment_prix_m2') in ['premium', 'luxe']:
            return "investisseurs_haut_gamme"
        elif not ascenseur and etage and etage >= 3:
            return "jeunes_actifs"
        else:
            return "familles"

    def determiner_segment_potentiel(self, dpe_score: int, age_bien: int) -> str:
        """Déterminer le segment de potentiel"""
        if dpe_score <= 3 and age_bien > 30:
            return "renovation"
        elif dpe_score >= 7 and age_bien < 20:
            return "valorisation"
        else:
            return "standard"

    def determiner_priorite_recommandation(self, type_rec: str, impact: str) -> str:
        """Déterminer la priorité d'une recommandation"""
        if type_rec == 'amelioration' and impact == 'important':
            return 'haute'
        elif type_rec == 'prix' and impact == 'important':
            return 'haute'
        elif type_rec == 'ciblage':
            return 'moyenne'
        else:
            return 'basse'

    def determiner_impact_estime(self, type_rec: str) -> str:
        """Déterminer l'impact estimé d'une recommandation"""
        if type_rec == 'amelioration':
            return 'important'
        elif type_rec == 'prix':
            return 'important'
        elif type_rec == 'marketing':
            return 'moyen'
        else:
            return 'faible'

    def determiner_delai_recommandation(self, type_rec: str) -> str:
        """Déterminer le délai de recommandation"""
        if type_rec == 'prix':
            return 'immediat'
        elif type_rec == 'marketing':
            return 'court_terme'
        else:
            return 'moyen_terme'

    def insert_aggregat_principal(self, annonce_id: int, aggregat_data: Dict[str, Any]) -> Optional[int]:
        """Insérer l'agrégat principal"""
        try:
            scores = aggregat_data.get('scores', {})
            segmentation = aggregat_data.get('segmentation', {})
            
            query = """
            INSERT INTO aggregats_principaux (
                id_annonce, date_aggregation, algorithme_version, 
                score_global, segment_marche_global, statut_optimisation
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_aggregat
            """
            
            # Construire le segment marché global
            segment_global_parts = []
            if segmentation.get('prix_m2'):
                segment_global_parts.append(segmentation['prix_m2'])
            if segmentation.get('surface'):
                segment_global_parts.append(segmentation['surface'])
            if segmentation.get('age'):
                segment_global_parts.append(segmentation['age'])
            
            segment_marche_global = '_'.join(segment_global_parts) if segment_global_parts else None
            
            values = (
                annonce_id,
                aggregat_data.get('metadata_aggregation', {}).get('date_aggregation', datetime.now()),
                aggregat_data.get('metadata_aggregation', {}).get('algorithme_version', '2.0'),
                scores.get('global'),
                segment_marche_global,
                'a_analyser'
            )
            
            self.cur.execute(query, values)
            aggregat_id = self.cur.fetchone()[0]
            self.conn.commit()
            
            print(f"✅ Agrégat principal inséré (ID: {aggregat_id})")
            return aggregat_id
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion agrégat principal: {e}")
            return None

    def insert_performance_financiere(self, aggregat_id: int, performance_data: Dict[str, Any]):
        """Insérer les données de performance financière"""
        try:
            # Déterminer le niveau de rendement et ratio
            rendement = performance_data.get('rendement_annuel_estime', 0)
            rentabilite_nette = performance_data.get('rentabilite_nette', 0)
            
            niveau_rendement = self.determiner_niveau_rendement(rendement)
            ratio_rentabilite = self.determiner_ratio_rentabilite(rentabilite_nette)
            
            query = """
            INSERT INTO performance_financiere (
                id_aggregat, prix_m2_calcule, loyer_estime_mensuel, 
                rendement_annuel_estime, rentabilite_nette, charges_annuelles,
                ratio_rentabilite, niveau_rendement
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                aggregat_id,
                performance_data.get('prix_m2'),
                performance_data.get('loyer_estime_mensuel'),
                rendement,
                rentabilite_nette,
                performance_data.get('charges_annuelles'),
                ratio_rentabilite,
                niveau_rendement
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Performance financière insérée")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion performance financière: {e}")

    def insert_scores_avances(self, aggregat_id: int, scores_data: Dict[str, Any], annonce_data: Dict[str, Any]):
        """Insérer les scores avancés"""
        try:
            # Calculer des scores supplémentaires basés sur les données de l'annonce
            batiment_data = annonce_data.get('batiment', {})
            medias_data = annonce_data.get('medias', {})
            
            # Score accessibilité (basé sur étage et ascenseur)
            score_accessibilite = 5.0
            if batiment_data.get('ascenseur'):
                score_accessibilite += 2
            if batiment_data.get('etage', 0) <= 1:
                score_accessibilite += 1
            elif batiment_data.get('etage', 0) >= 4 and not batiment_data.get('ascenseur'):
                score_accessibilite -= 2
            
            # Score médias (basé sur le nombre de photos et présence de vidéo)
            score_medias = 5.0
            if medias_data.get('nombre_photos', 0) >= 5:
                score_medias += 2
            if medias_data.get('has_video'):
                score_medias += 1
            if medias_data.get('has_visite_virtuelle'):
                score_medias += 2
            
            query = """
            INSERT INTO scores_avances (
                id_aggregat, score_emplacement, score_modernite, score_dpe,
                score_equipements, score_accessibilite, score_medias,
                ponderation_emplacement, ponderation_modernite, ponderation_dpe, ponderation_equipements
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                aggregat_id,
                scores_data.get('emplacement'),
                scores_data.get('modernite'),
                scores_data.get('dpe', scores_data.get('modernite')),  # Fallback
                6.0,  # score_equipements par défaut
                max(1, min(10, score_accessibilite)),
                max(1, min(10, score_medias)),
                0.20, 0.15, 0.15, 0.10
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Scores avancés insérés")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion scores avancés: {e}")

    def insert_segmentation(self, aggregat_id: int, segmentation_data: Dict[str, Any], annonce_data: Dict[str, Any]):
        """Insérer les données de segmentation"""
        try:
            batiment_data = annonce_data.get('batiment', {})
            diagnostics_data = annonce_data.get('diagnostics', {})
            
            segment_cible = self.determiner_segment_cible(segmentation_data, batiment_data)
            segment_potentiel = self.determiner_segment_potentiel(
                diagnostics_data.get('dpe', {}).get('score', 5),
                batiment_data.get('age_bien', 0)
            )
            
            query = """
            INSERT INTO segmentation (
                id_aggregat, segment_prix_m2, segment_surface, segment_age,
                segment_cible, segment_potentiel
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                aggregat_id,
                segmentation_data.get('prix_m2'),
                segmentation_data.get('surface'),
                segmentation_data.get('age'),
                segment_cible,
                segment_potentiel
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Segmentation insérée")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion segmentation: {e}")

    def insert_analyse_marche(self, aggregat_id: int, analyse_marche_data: Dict[str, Any]):
        """Insérer l'analyse de marché"""
        try:
            query = """
            INSERT INTO analyse_marche (
                id_aggregat, positionnement_marche, z_score_prix_m2,
                ecart_pourcentage, prix_m2_marche_reference, nombre_biens_reference,
                ecart_type_marche, rang_percentile
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Calculer le rang percentile basé sur le z-score
            z_score = analyse_marche_data.get('z_score_prix_m2', 0)
            rang_percentile = 50 + int(z_score * 20)  # Approximation simple
            rang_percentile = max(1, min(99, rang_percentile))
            
            values = (
                aggregat_id,
                analyse_marche_data.get('positionnement_marche'),
                z_score,
                analyse_marche_data.get('ecart_pourcentage'),
                analyse_marche_data.get('prix_m2_marche_reference'),
                analyse_marche_data.get('metadata_aggregation', {}).get('marche_reference', {}).get('nombre_biens_reference'),
                None,  # ecart_type_marche - non fourni dans les données
                rang_percentile
            )
            
            self.cur.execute(query, values)
            self.conn.commit()
            print(f"✅ Analyse marché insérée")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion analyse marché: {e}")

    def insert_recommandations(self, aggregat_id: int, recommandations_data: Dict[str, Any]):
        """Insérer les recommandations"""
        try:
            query = """
            INSERT INTO recommandations (
                id_aggregat, type_recommandation, priorite, description,
                action_concrete, impact_estime, delai_recommandation
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            inserted_count = 0
            
            # Traiter chaque type de recommandation
            for type_rec, recommandations in recommandations_data.items():
                if type_rec in ['prix', 'marketing', 'amelioration', 'ciblage']:
                    for recommandation in recommandations:
                        if recommandation:  # Vérifier que la recommandation n'est pas vide
                            priorite = self.determiner_priorite_recommandation(type_rec, 'important')
                            impact_estime = self.determiner_impact_estime(type_rec)
                            delai_recommandation = self.determiner_delai_recommandation(type_rec)
                            
                            # Générer une action concrète basée sur la recommandation
                            action_concrete = self.generer_action_concrete(type_rec, recommandation)
                            
                            values = (
                                aggregat_id,
                                type_rec,
                                priorite,
                                recommandation,
                                action_concrete,
                                impact_estime,
                                delai_recommandation
                            )
                            
                            self.cur.execute(query, values)
                            inserted_count += 1
            
            self.conn.commit()
            if inserted_count > 0:
                print(f"✅ {inserted_count} recommandations insérées")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erreur insertion recommandations: {e}")

    def generer_action_concrete(self, type_rec: str, recommandation: str) -> str:
        """Générer une action concrète basée sur le type de recommandation"""
        if type_rec == 'prix':
            if 'révision' in recommandation.lower():
                return "Analyser les prix du marché local et ajuster le prix de 5 à 10%"
            else:
                return "Maintenir le prix actuel et surveiller la concurrence"
        
        elif type_rec == 'marketing':
            if 'photos' in recommandation.lower():
                return "Organiser une séance photo professionnelle avec au moins 10 clichés"
            elif 'visite virtuelle' in recommandation.lower():
                return "Contacter un prestataire pour réaliser une visite virtuelle 3D"
            else:
                return "Réviser la description et les arguments de vente"
        
        elif type_rec == 'amelioration':
            return "Établir un devis pour les travaux de rénovation énergétique"
        
        elif type_rec == 'ciblage':
            return "Adapter la communication marketing pour la cible identifiée"
        
        else:
            return "Mettre en œuvre la recommandation dans les 15 jours"

    def process_aggregated_data(self, aggregated_data: Dict[str, Any]) -> bool:
        """Traiter une annonce agrégée et l'insérer en base"""
        
        reference = aggregated_data.get('reference', '').strip()
        if not reference:
            print("❌ Annonce agrégée sans référence, ignorée")
            return False
        
        print(f"📊 Traitement des agrégats pour: {reference}")
        
        # Récupérer l'ID de l'annonce
        annonce_id = self.get_annonce_id_by_reference(reference)
        if not annonce_id:
            print(f"❌ Annonce {reference} non trouvée en base, ignorée")
            return False
        
        # Vérifier si un agrégat existe déjà
        if self.check_existing_aggregat(annonce_id):
            print("⏭️  Agrégat déjà existant, ignoré")
            return False
        
        # Récupérer les données d'agrégat
        aggregat_data = aggregated_data.get('aggregats', {})
        if not aggregat_data:
            print("❌ Aucune donnée d'agrégat trouvée")
            return False
        
        # Afficher les infos principales
        performance_data = aggregat_data.get('performance', {})
        scores_data = aggregat_data.get('scores', {})
        analyse_marche_data = aggregat_data.get('analyse_marche', {})
        
        if scores_data.get('global'):
            print(f"🎯 Score global: {scores_data['global']}/10")
        if performance_data.get('prix_m2'):
            print(f"💰 Prix m²: {performance_data['prix_m2']:,.2f}€")
        if analyse_marche_data.get('positionnement_marche'):
            print(f"📊 Positionnement: {analyse_marche_data['positionnement_marche']}")
        
        # Insérer l'agrégat principal
        aggregat_id = self.insert_aggregat_principal(annonce_id, aggregat_data)
        if not aggregat_id:
            return False
        
        try:
            # Insérer les données détaillées
            self.insert_performance_financiere(aggregat_id, performance_data)
            self.insert_scores_avances(aggregat_id, scores_data, aggregated_data)
            self.insert_segmentation(aggregat_id, aggregat_data.get('segmentation', {}), aggregated_data)
            self.insert_analyse_marche(aggregat_id, analyse_marche_data)
            
            # Insérer les recommandations
            recommandations_data = aggregat_data.get('recommandations', {})
            if recommandations_data:
                self.insert_recommandations(aggregat_id, recommandations_data)
            
            print(f"✅ Agrégats pour {reference} complètement insérés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion des données d'agrégat: {e}")
            # Optionnel: supprimer l'agrégat principal en cas d'erreur
            try:
                self.cur.execute("DELETE FROM aggregats_principaux WHERE id_aggregat = %s", (aggregat_id,))
                self.conn.commit()
            except:
                pass
            return False

    def process_json_file(self, json_file_path: str):
        """Traiter un fichier JSON de données agrégées"""
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📁 Fichier JSON chargé: {len(data)} annonces agrégées trouvées")
            
            inserted_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, aggregated_data in enumerate(data, 1):
                print(f"\n--- Traitement agrégats {i}/{len(data)} ---")
                
                try:
                    success = self.process_aggregated_data(aggregated_data)
                    if success:
                        inserted_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    print(f"❌ Erreur lors du traitement: {e}")
                    error_count += 1
            
            # Résumé final
            print(f"\n{'='*50}")
            print("🎉 IMPORTATION DES AGRÉGATS TERMINÉE - RÉCAPITULATIF")
            print(f"{'='*50}")
            print(f"✅ {inserted_count} nouveaux agrégats insérés")
            print(f"⏭️  {skipped_count} agrégats ignorés (déjà existants ou erreurs)")
            print(f"❌ {error_count} agrégats en erreur")
            print(f"📊 Total traité: {len(data)} annonces agrégées")
            
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
        """Afficher les statistiques finales des agrégats"""
        try:
            # Statistiques par table d'agrégats
            tables = [
                'aggregats_principaux', 'performance_financiere', 'scores_avances',
                'segmentation', 'analyse_marche', 'recommandations'
            ]
            
            print(f"\n📊 STATISTIQUES DES AGRÉGATS:")
            for table in tables:
                self.cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cur.fetchone()[0]
                print(f"   • {table}: {count}")
            
            # Statistiques avancées
            self.cur.execute("""
                SELECT 
                    COUNT(*) as total_aggregats,
                    ROUND(AVG(ap.score_global), 2) as score_global_moyen,
                    ROUND(AVG(pf.prix_m2_calcule), 2) as prix_m2_moyen,
                    ROUND(AVG(pf.rendement_annuel_estime), 2) as rendement_moyen,
                    COUNT(CASE WHEN am.positionnement_marche IN ('tres_sous_cote', 'sous_cote') THEN 1 END) as biens_sous_cotes,
                    COUNT(CASE WHEN am.positionnement_marche IN ('tres_sur_cote', 'sur_cote') THEN 1 END) as biens_sur_cotes
                FROM aggregats_principaux ap
                LEFT JOIN performance_financiere pf ON ap.id_aggregat = pf.id_aggregat
                LEFT JOIN analyse_marche am ON ap.id_aggregat = am.id_aggregat
            """)
            stats = self.cur.fetchone()
            
            print(f"\n📈 STATISTIQUES GLOBALES DES AGRÉGATS:")
            print(f"   • Score global moyen: {stats[1] or 0:.1f}/10")
            print(f"   • Prix m² moyen: {stats[2] or 0:,.2f}€")
            print(f"   • Rendement moyen: {stats[3] or 0:.2f}%")
            print(f"   • Biens sous-cotés: {stats[4] or 0}")
            print(f"   • Biens sur-cotés: {stats[5] or 0}")
            
            # Distribution des segments
            self.cur.execute("""
                SELECT segment_prix_m2, COUNT(*) 
                FROM segmentation 
                WHERE segment_prix_m2 IS NOT NULL 
                GROUP BY segment_prix_m2 
                ORDER BY COUNT(*) DESC
            """)
            segments = self.cur.fetchall()
            
            print(f"\n🏷️  DISTRIBUTION DES SEGMENTS:")
            for segment, count in segments:
                print(f"   • {segment}: {count}")
            
        except Exception as e:
            print(f"⚠️  Impossible de récupérer les statistiques: {e}")

def main():
    """Fonction principale"""
    
    print("📊 IMPORTATEUR DE DONNÉES AGRÉGÉES")
    print("=" * 50)
    
    # Chemin vers le fichier JSON agrégé
    json_file_path = 'annonces_aggregees.json'
    
    # Vérifier si le fichier existe
    if not os.path.exists(json_file_path):
        print(f"❌ Fichier {json_file_path} non trouvé")
        print("💡 Assurez-vous d'avoir exécuté le script d'agrégation d'abord")
        sys.exit(1)
    
    # Initialiser le processeur
    processor = AggregatedDataToPostgreSQL()
    
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