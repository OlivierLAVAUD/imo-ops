import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, current_timestamp, when, regexp_replace
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType

class SparkDataProcessor:
    def __init__(self, config_file: str = "/opt/scripts/config_aggreges.json"):  # ← Chemin par défaut corrigé
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

    def load_json_data(self, json_file_path: str) -> DataFrame:
        """Charger et traiter le fichier JSON dans un DataFrame Spark"""
        print(f"📁 Chargement du fichier: {json_file_path}")
        
        try:
            # Lire le fichier JSON
            df_raw = self.spark.read.option("multiline", "true").json(json_file_path)
            
            # Afficher les statistiques initiales
            initial_count = df_raw.count()
            print(f"📊 {initial_count} annonces chargées depuis le JSON")
            
            # Appliquer les transformations de base
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
        if "reference" in df.columns:
            df = df.withColumn("reference", regexp_replace(col("reference"), "\s+", " "))
        if "description" in df.columns:
            df = df.withColumn("description", regexp_replace(col("description"), "\s+", " "))
        
        # Filtrer les annonces valides (avec référence)
        if "reference" in df.columns:
            df = df.filter(col("reference").isNotNull() & (col("reference") != ""))
        
        return df

    def show_statistics(self, df: DataFrame):
        """Afficher les statistiques des données"""
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES DES DONNÉES TRAITÉES")
        print("=" * 60)
        
        # Comptes basiques
        total_count = df.count()
        print(f"📈 Total annonces valides: {total_count:,}")
        
        # Afficher les colonnes disponibles
        print(f"\n📋 Colonnes disponibles: {df.columns}")
        
        # Statistiques par type de bien si la colonne existe
        if "composition.type_bien" in df.columns:
            type_stats = df.groupBy("composition.type_bien").count().orderBy("count", ascending=False)
            print(f"\n🏠 RÉPARTITION PAR TYPE DE BIEN:")
            type_stats.show(truncate=False)
        
        # Statistiques par source si la colonne existe
        if "metadata.source" in df.columns:
            source_stats = df.groupBy("metadata.source").count().orderBy("count", ascending=False)
            print(f"\n📰 RÉPARTITION PAR SOURCE:")
            source_stats.show(truncate=False)

    def run_analysis(self, df: DataFrame):
        """Exécuter des analyses avancées sur les données"""
        print("\n" + "=" * 60)
        print("🔍 ANALYSES AVANCÉES")
        print("=" * 60)
        
        # Afficher un échantillon des données
        print("📄 ÉCHANTILLON DES DONNÉES (5 premières lignes):")
        df.select("reference", "composition.type_bien", "prix.valeur", "surface.valeur").show(5, truncate=False)

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
    
    # Fichiers - CHEMINS ABSOLUS DANS LE CONTENEUR
    config_file = "/opt/scripts/config_aggreges.json"
    json_file_path = "/opt/scripts/annonces_agregees.json"
    
    # Vérifications
    if not os.path.exists(config_file):
        print(f"❌ Fichier de configuration non trouvé: {config_file}")
        sys.exit(1)
        
    if not os.path.exists(json_file_path):
        print(f"❌ Fichier de données non trouvé: {json_file_path}")
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