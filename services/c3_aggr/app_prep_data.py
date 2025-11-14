import json
import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

class DataPreparator:
    """
    Classe pour la préparation et la normalisation des données d'annonces immobilières
    """
    
    def __init__(self):
        # Configuration des scores normalisés
        self.dpe_scores = {'A': 10, 'B': 8, 'C': 6, 'D': 5, 'E': 4, 'F': 3, 'G': 2}
        self.ges_scores = {'A': 10, 'B': 8, 'C': 6, 'D': 5, 'E': 4, 'F': 3, 'G': 2}
        self.current_year = datetime.now().year
        
        # Configuration des étapes de traitement
        self.etapes_preparation = [
            "normalisation_numerique",
            "extraction_geographique", 
            "extraction_caracteristiques",
            "traitement_medias",
            "calcul_scores",
            "structuration_finale"
        ]

    # ==========================================================================
    # ÉTAPE 1: NORMALISATION DES DONNÉES NUMÉRIQUES
    # ==========================================================================
    
    def normaliser_prix(self, price_str: str) -> Optional[float]:
        """Nettoie et convertit les prix en format numérique standard"""
        if not price_str:
            return None
        
        # Suppression des caractères non numériques et normalisation
        cleaned = re.sub(r'[  €]', '', price_str).strip()
        cleaned = cleaned.replace(',', '.')
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def normaliser_nombre(self, number_str: str) -> Optional[float]:
        """Nettoie les nombres (surface, pièces, etc.)"""
        if not number_str or number_str == '':
            return None
        
        cleaned = re.sub(r'[  ]', '', number_str)
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def normaliser_booleen(self, value: Any) -> bool:
        """Convertit une valeur en boolean standardisé"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['true', 'vrai', 'oui', 'yes', '1', 't']:
                return True
            elif value_lower in ['false', 'faux', 'non', 'no', '0', 'f']:
                return False
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        return False

    # ==========================================================================
    # ÉTAPE 2: EXTRACTION ET NORMALISATION GÉOGRAPHIQUE
    # ==========================================================================
    
    def extraire_localisation(self, localisation: str) -> Dict[str, str]:
        """Extrait et normalise les informations de localisation"""
        if not localisation:
            return {'ville': None, 'code_postal': None}
        
        # Extraction du code postal via regex
        code_postal_match = re.search(r'\((\d{5})\)', localisation)
        code_postal = code_postal_match.group(1) if code_postal_match else None
        
        # Extraction du nom de ville
        ville = re.sub(r'\s*\(\d{5}\)', '', localisation).strip()
        
        return {'ville': ville, 'code_postal': code_postal}
    
    def extraire_quartier(self, description: str) -> Optional[str]:
        """Extrait le quartier de la description"""
        if not description:
            return None
        
        quartier_match = re.search(r'Quartier\s+([^,\.]+)', description)
        return quartier_match.group(1) if quartier_match else None
    
    def extraire_proximites(self, description: str) -> Optional[str]:
        """Extrait les éléments de proximité de la description"""
        if not description:
            return None
        
        proximites = []
        
        # Détection de points d'intérêt spécifiques
        if 'Buttes Chaumont' in description:
            proximites.append('Buttes Chaumont')
        
        # Extraction des stations de métro
        if 'métro' in description.lower():
            metro_match = re.search(r'métro\s+([^,\.]+)', description, re.IGNORECASE)
            if metro_match:
                proximites.append(f"métro {metro_match.group(1)}")
        
        return ', '.join(proximites) if proximites else None

    # ==========================================================================
    # ÉTAPE 3: EXTRACTION DES CARACTÉRISTIQUES DU BIEN
    # ==========================================================================
    
    def extraire_infos_etage(self, caracteristiques: List[str]) -> Dict[str, Any]:
        """Extrait et normalise les informations d'étage"""
        etage_info = {
            'etage': None, 
            'etage_total': None, 
            'ascenseur': False
        }
        
        for carac in caracteristiques:
            carac_lower = carac.lower()
            
            # Détection de l'ascenseur
            if 'ascenseur' in carac_lower:
                etage_info['ascenseur'] = True
            
            # Extraction des informations d'étage
            match = re.search(r'étage\s*(\d+)\s*(?:sur|/)\s*(\d+)', carac_lower)
            if match:
                etage_info['etage'] = int(match.group(1))
                etage_info['etage_total'] = int(match.group(2))
        
        return etage_info
    
    def extraire_nombre_chambres(self, caracteristiques: List[str]) -> Optional[int]:
        """Extrait le nombre de chambres des caractéristiques"""
        for carac in caracteristiques:
            match = re.search(r'(\d+)\s*chambre', carac.lower())
            if match:
                return int(match.group(1))
        return None
    
    def normaliser_caracteristiques(self, caracteristiques: List[str]) -> List[str]:
        """Nettoie et déduplique les caractéristiques"""
        if not caracteristiques:
            return []
        
        caracteristiques_propres = []
        elements_exclus = {'chambre', 'pièces', 'm²', 'étage', 'construit'}
        
        for carac in caracteristiques:
            carac_lower = carac.lower()
            # Exclusion des caractéristiques déjà gérées ailleurs
            if not any(exclu in carac_lower for exclu in elements_exclus):
                caracteristiques_propres.append(carac)
        
        return list(set(caracteristiques_propres))

    # ==========================================================================
    # ÉTAPE 4: TRAITEMENT DES MÉDIAS ET IMAGES
    # ==========================================================================
    
    def normaliser_images(self, images: List[str]) -> List[str]:
        """Nettoie, déduplique et normalise les URLs d'images"""
        if not images:
            return []
        
        unique_images = []
        seen_urls = set()
        
        for img in images:
            # Conservation de l'URL de base sans paramètres
            base_url = img.split('?')[0]
            if base_url not in seen_urls:
                seen_urls.add(base_url)
                unique_images.append(base_url)
        
        return unique_images

    # ==========================================================================
    # ÉTAPE 5: CALCUL DES SCORES ET INDICATEURS
    # ==========================================================================
    
    def calculer_score_dpe(self, dpe_classe: str) -> int:
        """Calcule un score numérique normalisé pour le DPE"""
        return self.dpe_scores.get(dpe_classe, 0) if dpe_classe else 0
    
    def extraire_charges_copropriete(self, charges_str: str) -> Dict[str, Any]:
        """Extrait et normalise les charges de copropriété"""
        if not charges_str:
            return {'valeur': None, 'unite': None, 'periode': None}
        
        # Nettoyage du texte
        cleaned = re.sub(r'[  ]', '', charges_str)
        montant_match = re.search(r'(\d+(?:[.,]\d+)?)', cleaned)
        
        if not montant_match:
            return {'valeur': None, 'unite': None, 'periode': None}
        
        # Conversion du montant
        valeur_str = montant_match.group(1).replace(',', '.')
        try:
            valeur = float(valeur_str)
        except ValueError:
            return {'valeur': None, 'unite': None, 'periode': None}
        
        # Détermination de la période et unité
        if '/ an' in cleaned.lower() or 'annuel' in cleaned.lower():
            periode = "annuel"
            unite = "€ / an"
        elif '/ trim' in cleaned.lower() or 'trimestriel' in cleaned.lower():
            periode = "trimestriel"
            unite = "€ / trim"
        elif '/ mois' in cleaned.lower() or '/mois' in cleaned.lower() or 'mensuel' in cleaned.lower():
            periode = "mensuel"
            unite = "€ / mois"
        elif '€' in cleaned:
            periode = "annuel"
            unite = "€"
        else:
            periode = None
            unite = None
        
        return {'valeur': valeur, 'unite': unite, 'periode': periode}
    
    def calculer_score_qualite(self, champs_obligatoires: List[Any]) -> float:
        """Calcule un score de qualité basé sur les champs obligatoires remplis"""
        champs_remplis = sum(1 for champ in champs_obligatoires if champ is not None)
        return (champs_remplis / len(champs_obligatoires)) * 10

    # ==========================================================================
    # ÉTAPE 6: STRUCTURATION FINALE ET NETTOYAGE
    # ==========================================================================
    
    def nettoyer_structure(self, data_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoie la structure en supprimant les valeurs None et listes vides"""
        
        def _nettoyer_recursif(obj):
            if isinstance(obj, dict):
                return {k: _nettoyer_recursif(v) for k, v in obj.items() 
                       if v is not None and _nettoyer_recursif(v) is not None}
            elif isinstance(obj, list):
                cleaned_list = [_nettoyer_recursif(item) for item in obj 
                              if _nettoyer_recursif(item) is not None]
                return cleaned_list if cleaned_list else None
            else:
                return obj
        
        return _nettoyer_recursif(data_structure)
    
    def serialiser_datetime(self, obj):
        """Sérialise les objets datetime pour JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    # ==========================================================================
    # MÉTHODE PRINCIPALE DE PRÉPARATION
    # ==========================================================================
    
    def preparer_donnees(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute toutes les étapes de préparation des données
        
        Args:
            raw_data: Données brutes d'une annonce
            
        Returns:
            Dict: Données structurées et normalisées
        """
        print(f"🔧 Préparation de l'annonce {raw_data.get('reference', 'N/A')}")
        
        # ======================================================================
        # SOUS-ÉTAPE 1: NORMALISATION NUMÉRIQUE
        # ======================================================================
        print("  📊 Normalisation des données numériques...")
        prix_numerique = self.normaliser_prix(raw_data['prix'])
        surface_numerique = self.normaliser_nombre(raw_data['surface'])
        pieces_numerique = self.normaliser_nombre(raw_data['pieces'])
        
        # ======================================================================
        # SOUS-ÉTAPE 2: EXTRACTION GÉOGRAPHIQUE
        # ======================================================================
        print("  🗺️  Extraction des informations géographiques...")
        localisation_info = self.extraire_localisation(raw_data['localisation'])
        code_postal = localisation_info['code_postal']
        quartier = self.extraire_quartier(raw_data['description'])
        proximites = self.extraire_proximites(raw_data['description'])
        
        # ======================================================================
        # SOUS-ÉTAPE 3: EXTRACTION DES CARACTÉRISTIQUES
        # ======================================================================
        print("  🏠 Extraction des caractéristiques du bien...")
        caracteristiques_detaillees = raw_data.get('caracteristiques_detaillees', [])
        infos_etage = self.extraire_infos_etage(caracteristiques_detaillees)
        chambres_extracted = self.extraire_nombre_chambres(caracteristiques_detaillees)
        charges_info = self.extraire_charges_copropriete(
            raw_data.get('copropriete_charges_previsionnelles', '')
        )
        
        # ======================================================================
        # SOUS-ÉTAPE 4: TRAITEMENT DES MÉDIAS
        # ======================================================================
        print("  🖼️  Traitement des médias...")
        images_nettoyees = self.normaliser_images(raw_data.get('images', []))
        has_video = self.normaliser_booleen(raw_data.get('has_video', False))
        has_visite_virtuelle = self.normaliser_booleen(raw_data.get('has_visite_virtuelle', ''))
        has_photo = len(images_nettoyees) > 0
        
        # ======================================================================
        # SOUS-ÉTAPE 5: CALCUL DES SCORES
        # ======================================================================
        print("  📈 Calcul des scores et indicateurs...")
        
        # Identification des champs manquants
        champs_manquants = []
        for champ, valeur in [('prix', prix_numerique), 
                            ('surface', surface_numerique),
                            ('pieces', pieces_numerique),
                            ('code_postal', code_postal)]:
            if valeur is None:
                champs_manquants.append(champ)
        
        # Calcul du score de qualité
        score_qualite = self.calculer_score_qualite([
            prix_numerique, surface_numerique, pieces_numerique, code_postal
        ])
        
        # ======================================================================
        # SOUS-ÉTAPE 6: CONSTRUCTION DE LA STRUCTURE FINALE
        # ======================================================================
        print("  🏗️  Construction de la structure finale...")
        
        structure_finale = {
            "reference": raw_data['reference'],
            "titre": raw_data['titre'],
            
            # Module Prix
            "prix": {
                "valeur": prix_numerique,
                "devise": "€",
                "au_m2": round(prix_numerique / surface_numerique, 2) 
                         if prix_numerique and surface_numerique and surface_numerique > 0 
                         else None
            },
            
            # Module Surface
            "surface": {
                "valeur": surface_numerique,
                "unite": "m²"
            },
            
            # Module Composition
            "composition": {
                "pieces": pieces_numerique,
                "chambres": chambres_extracted or (pieces_numerique - 1 if pieces_numerique else None),
                "type_bien": raw_data['type_bien']
            },
            
            # Module Localisation
            "localisation": {
                "ville": localisation_info['ville'],
                "code_postal": code_postal,
                "quartier": quartier,
                "proximite": proximites
            },
            
            "description": raw_data['description'],
            "caracteristiques": self.normaliser_caracteristiques(caracteristiques_detaillees),
            
            # Module Bâtiment
            "batiment": {
                "annee_construction": (
                    int(raw_data['annee_construction']) 
                    if raw_data.get('annee_construction') and raw_data['annee_construction'].isdigit()
                    else None
                ),
                "age_bien": (
                    self.current_year - int(raw_data['annee_construction']) 
                    if raw_data.get('annee_construction') and raw_data['annee_construction'].isdigit()
                    else None
                ),
                "etage": infos_etage['etage'],
                "etage_total": infos_etage['etage_total'],
                "ascenseur": infos_etage['ascenseur']
            },
            
            # Module Diagnostics
            "diagnostics": {
                "dpe": {
                    "classe": raw_data.get('dpe_classe_active'),
                    "score": self.calculer_score_dpe(raw_data.get('dpe_classe_active')),
                    "indice": (
                        int(raw_data.get('dpe_score', 0)) 
                        if str(raw_data.get('dpe_score', '')).isdigit() 
                        else None
                    )
                },
                "ges": {
                    "classe": raw_data.get('ges_classe_active'),
                    "score": self.ges_scores.get(raw_data.get('ges_classe_active', ''), 0),
                    "indice": (
                        int(raw_data.get('ges_score', 0)) 
                        if str(raw_data.get('ges_score', '')).isdigit() 
                        else None
                    )
                }
            },
            
            # Module Copropriété
            "copropriete": {
                "nb_lots": self.normaliser_nombre(raw_data.get('copropriete_nb_lots', '')),
                "charges": charges_info,
                "procedures_en_cours": not bool(raw_data.get('copropriete_procedures'))
            },
            
            # Module Médias
            "medias": {
                "images": images_nettoyees,
                "nombre_photos": len(images_nettoyees),
                "has_video": has_video,
                "has_visite_virtuelle": has_visite_virtuelle,
                "has_photo": has_photo
            },
            
            # Module Contact
            "contact": {
                "conseiller": raw_data.get('conseiller_nom_complet'),
                "telephone": raw_data.get('conseiller_telephone'),
                "photo": (
                    raw_data.get('conseiller_photo', '').split('?')[0] 
                    if raw_data.get('conseiller_photo') 
                    else None
                ),
                "lien": raw_data.get('conseiller_lien')
            },
            
            "url_annonce": raw_data.get('lien'),
            
            # Métadonnées de qualité
            "metadata": {
                "date_extraction": raw_data['date_extraction'],
                "score_qualite": score_qualite,
                "champs_manquants": champs_manquants,
                "etapes_traitees": self.etapes_preparation
            }
        }
        
        # ======================================================================
        # NETTOYAGE FINAL DE LA STRUCTURE
        # ======================================================================
        print("  🧹 Nettoyage final de la structure...")
        structure_finale = self.nettoyer_structure(structure_finale)
        
        print(f"  ✅ Annonce {raw_data.get('reference', 'N/A')} préparée avec succès")
        print(f"     - Score qualité: {score_qualite}/10")
        print(f"     - Champs manquants: {champs_manquants}")
        print("-" * 50)
        
        return structure_finale


# ==============================================================================
# FONCTIONS DE GESTION AVEC PANDAS
# ==============================================================================

def charger_donnees_brutes(chemin_fichier: str) -> pd.DataFrame:
    """
    Charge les données brutes depuis un fichier JSON vers un DataFrame pandas
    """
    print(f"📥 Chargement des données depuis {chemin_fichier}...")
    
    with open(chemin_fichier, 'r', encoding='utf-8') as f:
        annonces_brutes = json.load(f)
    
    df = pd.DataFrame(annonces_brutes)
    print(f"✅ {len(df)} annonces chargées dans le DataFrame")
    
    return df

def preparer_avec_pandas(df_brut: pd.DataFrame) -> pd.DataFrame:
    """
    Applique la préparation des données en utilisant pandas pour une meilleure performance
    """
    print("🔧 Début de la préparation avec pandas...")
    
    preparator = DataPreparator()
    
    # Application de la préparation à chaque ligne
    df_prepare = df_brut.copy()
    
    # Création de la colonne avec les données préparées
    df_prepare['donnees_preparees'] = df_prepare.apply(
        lambda row: preparator.preparer_donnees(row.to_dict()), 
        axis=1
    )
    
    # Extraction des métriques de qualité
    df_prepare['score_qualite'] = df_prepare['donnees_preparees'].apply(
        lambda x: x.get('metadata', {}).get('score_qualite', 0)
    )
    
    df_prepare['nb_champs_manquants'] = df_prepare['donnees_preparees'].apply(
        lambda x: len(x.get('metadata', {}).get('champs_manquants', []))
    )
    
    print("✅ Préparation avec pandas terminée")
    
    return df_prepare

def analyser_qualite_donnees(df_prepare: pd.DataFrame):
    """
    Analyse et affiche des statistiques sur la qualité des données préparées
    """
    print("\n📊 ANALYSE DE LA QUALITÉ DES DONNÉES")
    print("=" * 50)
    
    # Statistiques des scores de qualité
    scores = df_prepare['score_qualite']
    print(f"Score de qualité moyen: {scores.mean():.1f}/10")
    print(f"Score de qualité médian: {scores.median():.1f}/10")
    print(f"Distribution des scores:")
    print(f"  - 10/10: {len(scores[scores == 10])} annonces")
    print(f"  - 7.5-10: {len(scores[scores >= 7.5])} annonces")
    print(f"  - 5-7.5: {len(scores[(scores >= 5) & (scores < 7.5)])} annonces")
    print(f"  - <5: {len(scores[scores < 5])} annonces")
    
    # Analyse des champs manquants
    champs_manquants = df_prepare['nb_champs_manquants']
    print(f"\nChamps manquants par annonce:")
    print(f"  - 0 champs manquants: {len(champs_manquants[champs_manquants == 0])} annonces")
    print(f"  - 1-2 champs manquants: {len(champs_manquants[(champs_manquants >= 1) & (champs_manquants <= 2)])} annonces")
    print(f"  - 3+ champs manquants: {len(champs_manquants[champs_manquants >= 3])} annonces")

def sauvegarder_donnees_preparees(df_prepare: pd.DataFrame, chemin_sortie: str):
    """
    Sauvegarde les données préparées au format JSON
    """
    print(f"\n💾 Sauvegarde des données préparées vers {chemin_sortie}...")
    
    # Extraction des données préparées pour la sauvegarde JSON
    donnees_preparees = df_prepare['donnees_preparees'].tolist()
    
    preparator = DataPreparator()
    with open(chemin_sortie, 'w', encoding='utf-8') as f:
        json.dump(donnees_preparees, f, ensure_ascii=False, indent=2, 
                 default=preparator.serialiser_datetime)
    
    print(f"✅ Données sauvegardées: {len(donnees_preparees)} annonces")

# ==============================================================================
# FONCTION PRINCIPALE
# ==============================================================================

def main():
    """
    Fonction principale orchestrant tout le processus de préparation
    """
    print("🚀 DÉMARRAGE DU PROCESSUS DE PRÉPARATION DES DONNÉES")
    print("=" * 60)
    
    try:
        # ÉTAPE 1: Chargement des données brutes
        df_brut = charger_donnees_brutes('annonces.json')
        
        # ÉTAPE 2: Préparation avec pandas
        df_prepare = preparer_avec_pandas(df_brut)
        
        # ÉTAPE 3: Analyse de qualité
        analyser_qualite_donnees(df_prepare)
        
        # ÉTAPE 4: Sauvegarde
        sauvegarder_donnees_preparees(df_prepare, 'annonces_preparees.json')
        
        # ÉTAPE 5: Affichage d'un exemple
        if len(df_prepare) > 0:
            print(f"\n📋 EXEMPLE D'ANNONCE PRÉPARÉE:")
            print("=" * 40)
            exemple = df_prepare.iloc[0]['donnees_preparees']
            print(json.dumps(exemple, ensure_ascii=False, indent=2))
        
        print(f"\n🎉 PROCESSUS TERMINÉ AVEC SUCCÈS!")
        print(f"   {len(df_prepare)} annonces préparées et sauvegardées")
        
        return df_prepare
        
    except Exception as e:
        print(f"❌ ERREUR lors de la préparation: {e}")
        raise

if __name__ == "__main__":
    df_resultat = main()