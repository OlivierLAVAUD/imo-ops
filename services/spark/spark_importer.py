import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, current_timestamp, when, regexp_replace
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType, MapType

class SparkDataProcessor:
    def __init__(self, config_file: str = "config_aggreges.json"):
        self.spark = None
        self.config = None
        self.df_annonces = None
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
        print("✅ Variables d'environnement chargées")
        
    def initialize_spark(self):
        """Initialiser la session Spark"""
        try:
            self.spark = SparkSession.builder \
                .appName("IMO-Data-Processor") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                .getOrCreate()
            
            print("✅ Session Spark initialisée")
            print(f"🔗 Spark Master: {self.spark.conf.get('spark.master')}")
            print(f"📊 Spark Version: {self.spark.version}")
            
        except Exception as e:
            print(f"❌ Erreur d'initialisation Spark: {e}")
            sys.exit(1)

    def create_schema(self) -> StructType:
        """Créer le schéma Spark basé sur la configuration"""
        schema = StructType([
            StructField("reference", StringType(), True),
            StructField("date_import", TimestampType(), True),
            
            # Champs de composition
            StructField("composition_type_bien", StringType(), True),
            StructField("composition_nb_pieces", IntegerType(), True),
            StructField("composition_nb_chambres", IntegerType(), True),
            
            # Champs de prix
            StructField("prix_valeur", DoubleType(), True),
            StructField("prix_devise", StringType(), True),
            
            # Champs de surface
            StructField("surface_valeur", DoubleType(), True),
            StructField("surface_unite", StringType(), True),
            
            # Champs de localisation
            StructField("localisation_ville", StringType(), True),
            StructField("localisation_code_postal", StringType(), True),
            StructField("localisation_departement", StringType(), True),
            StructField("localisation_region", StringType(), True),
            
            # Métadonnées
            StructField("metadata_source", StringType(), True),
            StructField("metadata_date_extraction", TimestampType(), True),
            
            # Champs additionnels
            StructField("description", StringType(), True),
            StructField("url", StringType(), True)
        ])
        
        return schema

    def flatten_json_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplatir la structure JSON imbriquée"""
        flattened = {}
        
        # Référence
        flattened["reference"] = data.get("reference", "").strip()
        
        # Composition
        composition = data.get("composition", {})
        flattened["composition_type_bien"] = composition.get("type_bien")
        flattened["composition_nb_pieces"] = composition.get("nb_pieces")
        flattened["composition_nb_chambres"] = composition.get("nb_chambres")
        
        # Prix
        prix = data.get("prix", {})
        flattened["prix_valeur"] = self.safe_float(prix.get("valeur"))
        flattened["prix_devise"] = prix.get("devise", "EUR")
        
        # Surface
        surface = data.get("surface", {})
        flattened["surface_valeur"] = self.safe_float(surface.get("valeur"))
        flattened["surface_unite"] = surface.get("unite", "m²")
        
        # Localisation
        localisation = data.get("localisation", {})
        flattened["localisation_ville"] = localisation.get("ville")
        flattened["localisation_code_postal"] = localisation.get("code_postal")
        flattened["localisation_departement"] = localisation.get("departement")
        flattened["localisation_region"] = localisation.get("region")
        
        # Métadonnées
        metadata = data.get("metadata", {})
        flattened["metadata_source"] = metadata.get("source")
        flattened["metadata_date_extraction"] = self.parse_date(metadata.get("date_extraction"))
        
        # Champs additionnels
        flattened["description"] = data.get("description")
        flattened["url"] = data.get("url")
        
        return flattened

    def safe_float(self, value) -> Optional[float]:
        """Convertir en float de manière sécurisée"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parser une date string en datetime"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return None

    def validate_annonce(self, annonce_data: Dict[str, Any]) -> bool:
        """Valider une annonce selon les règles de configuration"""
        # Vérifier les champs requis
        for field in self.config['validation_rules']['required_fields']:
            if not self.get_nested_value(annonce_data, field):
                return False
        
        # Vérifier la référence
        reference = annonce_data.get('reference', '').strip()
        if not reference:
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

    def load_json_data(self, json_file_path: str) -> DataFrame:
        """Charger et traiter le fichier JSON dans un DataFrame Spark"""
        print(f"📁 Chargement du fichier: {json_file_path}")
        
        try:
            # Lire le fichier JSON
            df_raw = self.spark.read.option("multiline", "true").json(json_file_path)
            
            # Afficher les statistiques initiales
            initial_count = df_raw.count()
            print(f"📊 {initial_count} annonces chargées depuis le JSON")
            
            # Appliquer les transformations
            df_processed = self.process_dataframe(df_raw)
            
            # Afficher les statistiques après traitement
            final_count = df_processed.count()
            print(f"✅ {final_count} annonces après validation et nettoyage")
            
            return df_processed
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement du JSON: {e}")
            raise

    def process_dataframe(self, df: DataFrame) -> DataFrame:
        """Traiter et nettoyer le DataFrame"""
        
        # Ajouter la date d'import
        df = df.withColumn("date_import", current_timestamp())
        
        # Nettoyer les champs texte
        text_columns = ["reference", "description"]
        for col_name in text_columns:
            df = df.withColumn(col_name, regexp_replace(col(col_name), "\s+", " "))
        
        # Filtrer les annonces valides (basé sur les champs requis)
        df = self.filter_valid_annonces(df)
        
        # Calculer des métriques de qualité
        df = self.add_quality_metrics(df)
        
        return df

    def filter_valid_annonces(self, df: DataFrame) -> DataFrame:
        """Filtrer les annonces valides"""
        # Créer des conditions de validation basées sur les champs requis
        conditions = []
        
        for field in self.config['validation_rules']['required_fields']:
            col_name = field.replace('.', '_')
            conditions.append(col(col_name).isNotNull())
        
        # Ajouter la condition de référence non vide
        conditions.append(col("reference").isNotNull())
        conditions.append(col("reference") != "")
        
        # Appliquer le filtre
        valid_df = df
        for condition in conditions:
            valid_df = valid_df.filter(condition)
        
        return valid_df

    def add_quality_metrics(self, df: DataFrame) -> DataFrame:
        """Ajouter des métriques de qualité des données"""
        
        df_with_metrics = df \
            .withColumn("has_prix", when(col("prix_valeur").isNotNull(), 1).otherwise(0)) \
            .withColumn("has_surface", when(col("surface_valeur").isNotNull(), 1).otherwise(0)) \
            .withColumn("has_localisation", when(col("localisation_ville").isNotNull(), 1).otherwise(0)) \
            .withColumn("data_quality_score", 
                       (col("has_prix") + col("has_surface") + col("has_localisation")) / 3.0)
        
        return df_with_metrics

    def show_statistics(self, df: DataFrame):
        """Afficher les statistiques des données"""
        print(f"\n{'='*60}")
        print("📊 STATISTIQUES DES DONNÉES TRAITÉES")
        print(f"{'='*60}")
        
        # Comptes basiques
        total_count = df.count()
        print(f"📈 Total annonces valides: {total_count:,}")
        
        # Statistiques par type de bien
        type_stats = df.groupBy("composition_type_bien").count().orderBy("count", ascending=False)
        print(f"\n🏠 RÉPARTITION PAR TYPE DE BIEN:")
        type_stats.show(truncate=False)
        
        # Statistiques de prix
        prix_stats = df.filter(col("prix_valeur").isNotNull()) \
                      .select(
                          col("prix_valeur").cast("double").alias("prix")
                      ) \
                      .describe("prix")
        print(f"\n💰 STATISTIQUES DE PRIX:")
        prix_stats.show()
        
        # Statistiques de surface
        surface_stats = df.filter(col("surface_valeur").isNotNull()) \
                         .select(
                             col("surface_valeur").cast("double").alias("surface")
                         ) \
                         .describe("surface")
        print(f"\n📏 STATISTIQUES DE SURFACE:")
        surface_stats.show()
        
        # Qualité des données
        quality_stats = df.select(
            col("data_quality_score").cast("double").alias("quality")
        ).describe("quality")
        print(f"\n🎯 QUALITÉ MOYENNE DES DONNÉES:")
        quality_stats.show()

    def save_results(self, df: DataFrame, output_format: str = "parquet"):
        """Sauvegarder les résultats traités"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/opt/data/output/annonces_traitees_{timestamp}"
        
        try:
            if output_format.lower() == "parquet":
                df.write.mode("overwrite").parquet(output_path)
                print(f"💾 Données sauvegardées en Parquet: {output_path}")
            elif output_format.lower() == "csv":
                df.write.mode("overwrite").option("header", "true").csv(output_path)
                print(f"💾 Données sauvegardées en CSV: {output_path}")
            else:
                print(f"❌ Format non supporté: {output_format}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")

    def run_analysis(self, df: DataFrame):
        """Exécuter des analyses avancées sur les données"""
        print(f"\n{'='*60}")
        print("🔍 ANALYSES AVANCÉES")
        print(f"{='*60}")
        
        # Prix au m²
        df_with_price_per_sqm = df.filter(
            (col("prix_valeur").isNotNull()) & 
            (col("surface_valeur").isNotNull()) &
            (col("surface_valeur") > 0)
        ).withColumn(
            "prix_au_m2", 
            col("prix_valeur") / col("surface_valeur")
        )
        
        # Top 10 des villes par prix au m² moyen
        top_villes = df_with_price_per_sqm.groupBy("localisation_ville") \
            .agg({
                "prix_au_m2": "avg",
                "reference": "count"
            }) \
            .withColumnRenamed("avg(prix_au_m2)", "prix_m2_moyen") \
            .withColumnRenamed("count(reference)", "nb_annonces") \
            .filter(col("nb_annonces") >= 5) \
            .orderBy("prix_m2_moyen", ascending=False) \
            .limit(10)
        
        print("🏆 TOP 10 VILLES PAR PRIX AU M² MOYEN:")
        top_villes.show(truncate=False)

    def process_file(self, json_file_path: str):
        """Traiter un fichier JSON complet avec Spark"""
        
        if not os.path.exists(json_file_path):
            print(f"❌ Fichier non trouvé: {json_file_path}")
            return
        
        try:
            # Initialiser Spark
            self.initialize_spark()
            
            # Charger et traiter les données
            df_processed = self.load_json_data(json_file_path)
            
            # Afficher les statistiques
            self.show_statistics(df_processed)
            
            # Exécuter des analyses
            self.run_analysis(df_processed)
            
            # Sauvegarder les résultats
            self.save_results(df_processed, "parquet")
            
            # Afficher le schéma final
            print(f"\n📋 SCHÉMA FINAL:")
            df_processed.printSchema()
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()
                print("✅ Session Spark arrêtée")

def main():
    """Fonction principale"""
    
    print("🏠 PROCESSUS SPARK - TRAITEMENT D'ANNONCES AGRÉGÉES")
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
        print("💡 Placez votre fichier JSON dans le même dossier que le script")
        sys.exit(1)
    
    # Initialiser le processeur Spark
    processor = SparkDataProcessor(config_file)
    
    print("\n" + "=" * 60)
    
    try:
        # Traiter le fichier
        processor.process_file(json_file_path)
        
        print(f"\n🎉 TRAITEMENT TERMINÉ AVEC SUCCÈS!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Traitement interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()