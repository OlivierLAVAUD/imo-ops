import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from scipy import stats
import statistics

class DataAggregator:
    """
    Classe pour l'agrégation et l'analyse des données immobilières préparées
    """
    
    def __init__(self):
        # Configuration des segments de marché
        self.segments_config = {
            'prix_m2_limites': [5000, 7000, 10000, 15000],
            'surface_limites': [30, 50, 80, 120],
            'age_limites': [5, 20, 50, 100]
        }
        
        # Pondérations pour le scoring
        self.ponderations = {
            'prix_m2': 0.25,
            'localisation': 0.20,
            'dpe': 0.15,
            'surface': 0.10,
            'etage': 0.10,
            'annee': 0.10,
            'equipements': 0.10
        }

    # ==========================================================================
    # MÉTHODES D'ANALYSE PAR SEGMENT
    # ==========================================================================
    
    def segmenter_par_prix_m2(self, prix_m2: float) -> str:
        """Segmente un bien selon son prix au m²"""
        limites = self.segments_config['prix_m2_limites']
        
        if prix_m2 < limites[0]:
            return "économique"
        elif prix_m2 < limites[1]:
            return "moyen"
        elif prix_m2 < limites[2]:
            return "supérieur"
        elif prix_m2 < limites[3]:
            return "premium"
        else:
            return "luxe"
    
    def segmenter_par_surface(self, surface: float) -> str:
        """Segmente un bien selon sa surface"""
        limites = self.segments_config['surface_limites']
        
        if surface < limites[0]:
            return "studio"
        elif surface < limites[1]:
            return "appartement"
        elif surface < limites[2]:
            return "grand_appartement"
        elif surface < limites[3]:
            return "maison"
        else:
            return "grande_maison"
    
    def segmenter_par_age(self, age: int) -> str:
        """Segmente un bien selon son âge"""
        limites = self.segments_config['age_limites']
        
        if age < limites[0]:
            return "neuf"
        elif age < limites[1]:
            return "recent"
        elif age < limites[2]:
            return "ancien"
        elif age < limites[3]:
            return "très_ancien"
        else:
            return "patrimoine"

    # ==========================================================================
    # CALCULS D'INDICATEURS AVANCÉS
    # ==========================================================================
    
    def calculer_rentabilite(self, annonce: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule les indicateurs de rentabilité"""
        prix = annonce.get('prix', {}).get('valeur')
        surface = annonce.get('surface', {}).get('valeur')
        charges = annonce.get('copropriete', {}).get('charges', {}).get('valeur')
        
        if not prix or not surface:
            return {}
        
        prix_m2 = prix / surface
        
        # Calcul du loyer potentiel (règle de base)
        loyer_mensuel_estime = prix_m2 * surface * 0.05 / 12  # 5% de rendement annuel
        
        rentabilite = {
            'prix_m2': round(prix_m2, 2),
            'loyer_estime_mensuel': round(loyer_mensuel_estime, 2),
            'rendement_annuel_estime': round((loyer_mensuel_estime * 12 / prix) * 100, 2) if prix > 0 else 0
        }
        
        if charges:
            rentabilite['charges_annuelles'] = charges
            rentabilite['rentabilite_nette'] = max(0, rentabilite['rendement_annuel_estime'] - (charges / prix * 100))
        
        return rentabilite
    
    def calculer_score_emplacement(self, annonce: Dict[str, Any]) -> float:
        """Calcule un score d'emplacement basé sur la localisation"""
        score = 5.0  # Score de base
        
        localisation = annonce.get('localisation', {})
        code_postal = localisation.get('code_postal')
        quartier = localisation.get('quartier')
        proximite = localisation.get('proximite')
        
        # Points selon l'arrondissement (exemple simplifié)
        if code_postal:
            arrondissement = int(code_postal[-2:])
            if arrondissement in [75, 92]:  # Paris + Hauts-de-Seine
                score += 2
            elif arrondissement in [93, 94]:  # Seine-Saint-Denis, Val-de-Marne
                score += 1
        
        # Bonus pour quartier spécifique
        if quartier and 'Buttes Chaumont' in str(quartier):
            score += 1
        
        # Bonus pour proximités
        if proximite:
            if 'métro' in str(proximite):
                score += 1
            if 'école' in str(proximite).lower():
                score += 0.5
        
        return min(10, max(1, score))
    
    def calculer_score_modernite(self, annonce: Dict[str, Any]) -> float:
        """Calcule un score de modernité du bien"""
        score = 5.0
        
        batiment = annonce.get('batiment', {})
        diagnostics = annonce.get('diagnostics', {})
        
        # Score DPE
        dpe_score = diagnostics.get('dpe', {}).get('score', 0)
        score += (dpe_score - 5) * 0.5  # Bonus/malus selon DPE
        
        # Âge du bien
        age = batiment.get('age_bien')
        if age:
            if age < 10:
                score += 2
            elif age < 30:
                score += 1
            elif age > 50:
                score -= 1
        
        # Équipements
        caracteristiques = annonce.get('caracteristiques', [])
        equipements_modernes = {'digicode', 'interphone', 'chauffage central', 'double vitrage'}
        for equipement in caracteristiques:
            if any(eq in equipement.lower() for eq in equipements_modernes):
                score += 0.5
        
        # Ascenseur
        if batiment.get('ascenseur'):
            score += 1
        
        return min(10, max(1, score))

    # ==========================================================================
    # ANALYSE DE MARCHÉ
    # ==========================================================================
    
    def analyser_marche_local(self, annonces: List[Dict]) -> Dict[str, Any]:
        """Analyse le marché local basé sur toutes les annonces"""
        if not annonces:
            return {}
        
        # Extraction des données pertinentes
        prix_list = []
        surfaces_list = []
        prix_m2_list = []
        arrondissements = []
        
        for annonce in annonces:
            prix = annonce.get('prix', {}).get('valeur')
            surface = annonce.get('surface', {}).get('valeur')
            code_postal = annonce.get('localisation', {}).get('code_postal')
            
            if prix and surface:
                prix_list.append(prix)
                surfaces_list.append(surface)
                prix_m2_list.append(prix / surface)
            
            if code_postal:
                arrondissements.append(code_postal)
        
        if not prix_m2_list:
            return {}
        
        # Calcul des statistiques
        stats_marche = {
            'prix_m2_moyen': round(np.mean(prix_m2_list), 2),
            'prix_m2_median': round(np.median(prix_m2_list), 2),
            'prix_m2_min': round(min(prix_m2_list), 2),
            'prix_m2_max': round(max(prix_m2_list), 2),
            'ecart_type_prix_m2': round(np.std(prix_m2_list), 2),
            'nombre_biens_analyses': len(prix_m2_list),
            'arrondissements_uniques': list(set(arrondissements)),
            'surface_moyenne': round(np.mean(surfaces_list), 2),
            'prix_moyen': round(np.mean(prix_list), 2)
        }
        
        # Segmentation par prix
        stats_marche['distribution_prix_m2'] = {
            'economique': len([p for p in prix_m2_list if p < 5000]),
            'moyen': len([p for p in prix_m2_list if 5000 <= p < 8000]),
            'superieur': len([p for p in prix_m2_list if 8000 <= p < 12000]),
            'premium': len([p for p in prix_m2_list if p >= 12000])
        }
        
        return stats_marche
    
    def comparer_au_marche(self, annonce: Dict[str, Any], stats_marche: Dict[str, Any]) -> Dict[str, Any]:
        """Compare un bien au marché local"""
        prix_m2_bien = annonce.get('prix', {}).get('au_m2')
        if not prix_m2_bien or not stats_marche:
            return {}
        
        prix_m2_marche = stats_marche.get('prix_m2_moyen')
        ecart_type = stats_marche.get('ecart_type_prix_m2', 1)
        
        # Calcul de l'écart normalisé
        if prix_m2_marche and ecart_type > 0:
            z_score = (prix_m2_bien - prix_m2_marche) / ecart_type
            
            if z_score < -1.5:
                positionnement = "très_sous_cote"
            elif z_score < -0.5:
                positionnement = "sous_cote"
            elif z_score <= 0.5:
                positionnement = "dans_la_moyenne"
            elif z_score <= 1.5:
                positionnement = "sur_cote"
            else:
                positionnement = "très_sur_cote"
        else:
            z_score = 0
            positionnement = "non_determine"
        
        return {
            'z_score_prix_m2': round(z_score, 2),
            'positionnement_marche': positionnement,
            'ecart_pourcentage': round(((prix_m2_bien - prix_m2_marche) / prix_m2_marche) * 100, 2) if prix_m2_marche else 0,
            'prix_m2_marche_reference': prix_m2_marche
        }

    # ==========================================================================
    # GÉNÉRATION DE RECOMMANDATIONS
    # ==========================================================================
    
    def generer_recommandations(self, annonce: Dict[str, Any], analyse_marche: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des recommandations basées sur l'analyse"""
        recommandations = {
            'prix': [],
            'marketing': [],
            'amelioration': [],
            'ciblage': []
        }
        
        # Analyse du positionnement prix
        positionnement = analyse_marche.get('positionnement_marche', '')
        if positionnement in ['très_sur_cote', 'sur_cote']:
            recommandations['prix'].append("Envisager une révision du prix à la baisse")
        elif positionnement in ['très_sous_cote', 'sous_cote']:
            recommandations['prix'].append("Prix attractif - maintenir la stratégie")
        
        # Analyse DPE
        dpe_classe = annonce.get('diagnostics', {}).get('dpe', {}).get('classe')
        if dpe_classe in ['F', 'G']:
            recommandations['amelioration'].append("Priorité: rénovation énergétique")
            recommandations['marketing'].append("Mettre en avant le potentiel de valorisation")
        
        # Analyse de l'étage
        batiment = annonce.get('batiment', {})
        if batiment.get('etage', 0) >= 4 and not batiment.get('ascenseur'):
            recommandations['ciblage'].append("Cibler public jeune et sportif")
        else:
            recommandations['ciblage'].append("Convient à toutes les cibles")
        
        # Analyse des médias
        medias = annonce.get('medias', {})
        if medias.get('nombre_photos', 0) < 5:
            recommandations['marketing'].append("Ajouter plus de photos pour mieux valoriser")
        
        if not medias.get('has_visite_virtuelle', False):
            recommandations['marketing'].append("Envisager une visite virtuelle")
        
        return recommandations

    # ==========================================================================
    # MÉTHODE PRINCIPALE D'AGRÉGATION
    # ==========================================================================
    
    def aggregator_donnees(self, annonces_preparees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Exécute toutes les étapes d'agrégation sur les données préparées
        
        Args:
            annonces_preparees: Liste des annonces déjà préparées
            
        Returns:
            Liste des annonces avec données agrégées
        """
        print("🚀 DÉMARRAGE DE L'AGRÉGATION DES DONNÉES")
        print("=" * 50)
        
        if not annonces_preparees:
            print("❌ Aucune donnée à agréger")
            return []
        
        # ÉTAPE 1: Analyse du marché global
        print("📊 Analyse du marché local...")
        stats_marche = self.analyser_marche_local(annonces_preparees)
        
        annonces_aggregees = []
        
        for i, annonce in enumerate(annonces_preparees):
            print(f"🔍 Traitement de l'annonce {i+1}/{len(annonces_preparees)}")
            
            # Création d'une copie pour l'agrégation
            annonce_aggregee = annonce.copy()
            
            # ÉTAPE 2: Calcul des indicateurs avancés
            rentabilite = self.calculer_rentabilite(annonce)
            score_emplacement = self.calculer_score_emplacement(annonce)
            score_modernite = self.calculer_score_modernite(annonce)
            
            # ÉTAPE 3: Segmentation
            prix_m2 = annonce.get('prix', {}).get('au_m2')
            surface = annonce.get('surface', {}).get('valeur')
            age = annonce.get('batiment', {}).get('age_bien')
            
            segmentation = {
                'prix_m2': self.segmenter_par_prix_m2(prix_m2) if prix_m2 else None,
                'surface': self.segmenter_par_surface(surface) if surface else None,
                'age': self.segmenter_par_age(age) if age else None
            }
            
            # ÉTAPE 4: Analyse comparative du marché
            analyse_marche = self.comparer_au_marche(annonce, stats_marche)
            
            # ÉTAPE 5: Génération des recommandations
            recommandations = self.generer_recommandations(annonce, analyse_marche)
            
            # ÉTAPE 6: Construction de la structure agrégée
            agregats = {
                # Indicateurs de performance
                'performance': rentabilite,
                
                # Scores normalisés
                'scores': {
                    'emplacement': round(score_emplacement, 2),
                    'modernite': round(score_modernite, 2),
                    'global': round((score_emplacement + score_modernite) / 2, 2)
                },
                
                # Segmentation marché
                'segmentation': segmentation,
                
                # Analyse comparative
                'analyse_marche': analyse_marche,
                
                # Recommandations
                'recommandations': recommandations,
                
                # Métadonnées d'agrégation
                'metadata_aggregation': {
                    'date_aggregation': datetime.now().isoformat(),
                    'algorithme_version': '1.0',
                    'marche_reference': {
                        'prix_m2_moyen': stats_marche.get('prix_m2_moyen'),
                        'nombre_biens_reference': stats_marche.get('nombre_biens_analyses')
                    }
                }
            }
            
            # Fusion avec les données originales
            annonce_aggregee['aggregats'] = agregats
            annonces_aggregees.append(annonce_aggregee)
        
        print(f"✅ Agrégation terminée: {len(annonces_aggregees)} annonces traitées")
        return annonces_aggregees

# ==============================================================================
# FONCTIONS D'ANALYSE AVANCÉE AVEC PANDAS
# ==============================================================================

def analyser_tendances_marche(df_aggrege: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyse les tendances du marché à partir des données agrégées
    """
    print("\n📈 ANALYSE DES TENDANCES DU MARCHÉ")
    print("=" * 40)
    
    tendances = {}
    
    try:
        # Extraction des agrégats
        df_aggrege['scores_global'] = df_aggrege['aggregats'].apply(
            lambda x: x.get('scores', {}).get('global', 0)
        )
        df_aggrege['prix_m2'] = df_aggrege['aggregats'].apply(
            lambda x: x.get('performance', {}).get('prix_m2', 0)
        )
        df_aggrege['segment_prix'] = df_aggrege['aggregats'].apply(
            lambda x: x.get('segmentation', {}).get('prix_m2', 'inconnu')
        )
        
        # Statistiques générales
        tendances['score_global_moyen'] = round(df_aggrege['scores_global'].mean(), 2)
        tendances['prix_m2_moyen'] = round(df_aggrege['prix_m2'].mean(), 2)
        tendances['correlation_score_prix'] = round(
            df_aggrege['scores_global'].corr(df_aggrege['prix_m2']), 3
        )
        
        # Distribution par segment
        tendances['distribution_segments'] = df_aggrege['segment_prix'].value_counts().to_dict()
        
        # Top 10% des biens
        seuil_top_10 = df_aggrege['scores_global'].quantile(0.9)
        biens_top_10 = df_aggrege[df_aggrege['scores_global'] >= seuil_top_10]
        
        tendances['top_10_percent'] = {
            'nombre_biens': len(biens_top_10),
            'prix_m2_moyen': round(biens_top_10['prix_m2'].mean(), 2),
            'caracteristiques_communes': []
        }
        
        print(f"📊 Score global moyen: {tendances['score_global_moyen']}/10")
        print(f"💰 Prix m² moyen: {tendances['prix_m2_moyen']} €")
        print(f"📈 Correlation score/prix: {tendances['correlation_score_prix']}")
        print(f"🏷️  Distribution des segments: {tendances['distribution_segments']}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse des tendances: {e}")
    
    return tendances

def generer_rapport_optimisation(df_aggrege: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère un rapport d'optimisation pour les annonces
    """
    print("\n🎯 RAPPORT D'OPTIMISATION")
    print("=" * 35)
    
    rapport = {
        'opportunites_amelioration': [],
        'biens_sous_cotes': [],
        'biens_sur_cotes': []
    }
    
    for idx, annonce in df_aggrege.iterrows():
        agregats = annonce['aggregats']
        analyse_marche = agregats.get('analyse_marche', {})
        recommandations = agregats.get('recommandations', {})
        
        # Identification des biens sous/sur-cotés
        positionnement = analyse_marche.get('positionnement_marche', '')
        if positionnement in ['très_sous_cote', 'sous_cote']:
            rapport['biens_sous_cotes'].append({
                'reference': annonce['reference'],
                'positionnement': positionnement,
                'ecart_pourcentage': analyse_marche.get('ecart_pourcentage', 0)
            })
        elif positionnement in ['très_sur_cote', 'sur_cote']:
            rapport['biens_sur_cotes'].append({
                'reference': annonce['reference'],
                'positionnement': positionnement,
                'ecart_pourcentage': analyse_marche.get('ecart_pourcentage', 0)
            })
        
        # Opportunités d'amélioration
        if recommandations.get('amelioration'):
            rapport['opportunites_amelioration'].append({
                'reference': annonce['reference'],
                'recommandations': recommandations['amelioration']
            })
    
    print(f"🔍 {len(rapport['biens_sous_cotes'])} biens sous-cotés identifiés")
    print(f"⚠️  {len(rapport['biens_sur_cotes'])} biens sur-cotés identifiés")
    print(f"🛠️  {len(rapport['opportunites_amelioration'])} opportunités d'amélioration")
    
    return rapport

# ==============================================================================
# FONCTION PRINCIPALE
# ==============================================================================

def main_aggregation():
    """
    Fonction principale orchestrant le processus d'agrégation
    """
    print("🚀 DÉMARRAGE DU PROCESSUS D'AGRÉGATION")
    print("=" * 50)
    
    try:
        # ÉTAPE 1: Chargement des données préparées
        print("📥 Chargement des données préparées...")
        with open('annonces_preparees.json', 'r', encoding='utf-8') as f:
            annonces_preparees = json.load(f)
        
        print(f"✅ {len(annonces_preparees)} annonces préparées chargées")
        
        # ÉTAPE 2: Agrégation des données
        aggregator = DataAggregator()
        annonces_aggregees = aggregator.aggregator_donnees(annonces_preparees)
        
        # ÉTAPE 3: Conversion en DataFrame pour analyse
        df_aggrege = pd.DataFrame(annonces_aggregees)
        
        # ÉTAPE 4: Analyses avancées
        tendances = analyser_tendances_marche(df_aggrege)
        rapport_optimisation = generer_rapport_optimisation(df_aggrege)
        
        # ÉTAPE 5: Sauvegarde des résultats
        print("\n💾 Sauvegarde des données agrégées...")
        with open('annonces_aggregees.json', 'w', encoding='utf-8') as f:
            json.dump(annonces_aggregees, f, ensure_ascii=False, indent=2)
        
        # ÉTAPE 6: Sauvegarde des analyses
        with open('analyses_marche.json', 'w', encoding='utf-8') as f:
            json.dump({
                'tendances': tendances,
                'rapport_optimisation': rapport_optimisation,
                'date_analyse': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        # ÉTAPE 7: Affichage d'un exemple
        if len(annonces_aggregees) > 0:
            print(f"\n📋 EXEMPLE D'ANNONCE AGRÉGÉE:")
            print("=" * 40)
            exemple = annonces_aggregees[0]
            print(json.dumps(exemple, ensure_ascii=False, indent=2))
        
        print(f"\n🎉 AGRÉGATION TERMINÉE AVEC SUCCÈS!")
        print(f"   {len(annonces_aggregees)} annonces agrégées")
        print(f"   📊 Analyses sauvegardées: tendances_marche.json")
        print(f"   📈 Rapports générés: rapport_optimisation.json")
        
        return df_aggrege
        
    except Exception as e:
        print(f"❌ ERREUR lors de l'agrégation: {e}")
        raise

if __name__ == "__main__":
    df_aggrege = main_aggregation()