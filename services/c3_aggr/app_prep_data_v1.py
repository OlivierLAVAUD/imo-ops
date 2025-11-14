import json
import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

class DataPreparator:
    def __init__(self):
        self.dpe_scores = {'A': 10, 'B': 8, 'C': 6, 'D': 5, 'E': 4, 'F': 3, 'G': 2}
        self.ges_scores = {'A': 10, 'B': 8, 'C': 6, 'D': 5, 'E': 4, 'F': 3, 'G': 2}
        self.current_year = datetime.now().year
    
    def clean_price(self, price_str: str) -> float:
        """Nettoie et convertit les prix en numérique"""
        if not price_str:
            return None
        cleaned = re.sub(r'[  €]', '', price_str).strip()
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def clean_number(self, number_str: str) -> float:
        """Nettoie les nombres (surface, pièces, etc.)"""
        if not number_str or number_str == '':
            return None
        cleaned = re.sub(r'[  ]', '', number_str)
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def to_boolean(self, value: Any) -> bool:
        """Convertit une valeur en boolean"""
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
    
    def extract_localisation(self, localisation: str) -> Dict[str, str]:
        """Extrait le nom de ville et code postal simple de la localisation"""
        if not localisation:
            return {'ville': None, 'code_postal': None}
        
        code_postal_match = re.search(r'\((\d{5})\)', localisation)
        code_postal = code_postal_match.group(1) if code_postal_match else None
        
        ville = re.sub(r'\s*\(\d{5}\)', '', localisation).strip()
        
        return {'ville': ville, 'code_postal': code_postal}
    
    def extract_quartier(self, description: str) -> str:
        """Extrait le quartier de la description"""
        if not description:
            return None
        quartier_match = re.search(r'Quartier\s+([^,\.]+)', description)
        return quartier_match.group(1) if quartier_match else None
    
    def extract_proximite(self, description: str) -> str:
        """Extrait les éléments de proximité de la description"""
        if not description:
            return None
        proximites = []
        if 'Buttes Chaumont' in description:
            proximites.append('Buttes Chaumont')
        if 'métro' in description.lower():
            metro_match = re.search(r'métro\s+([^,\.]+)', description, re.IGNORECASE)
            if metro_match:
                proximites.append(f"métro {metro_match.group(1)}")
        
        return ', '.join(proximites) if proximites else None
    
    def extract_etage(self, caracteristiques: List[str]) -> Dict[str, Any]:
        """Extrait les informations d'étage des caractéristiques"""
        etage_info = {'etage': None, 'etage_total': None, 'ascenseur': False}
        
        for carac in caracteristiques:
            carac_lower = carac.lower()
            if 'ascenseur' in carac_lower:
                etage_info['ascenseur'] = True
            match = re.search(r'étage\s*(\d+)\s*(?:sur|/)\s*(\d+)', carac_lower)
            if match:
                etage_info['etage'] = int(match.group(1))
                etage_info['etage_total'] = int(match.group(2))
        
        return etage_info
    
    def extract_chambres(self, caracteristiques: List[str]) -> int:
        """Extrait le nombre de chambres des caractéristiques"""
        for carac in caracteristiques:
            match = re.search(r'(\d+)\s*chambre', carac.lower())
            if match:
                return int(match.group(1))
        return None
    
    def clean_images(self, images: List[str]) -> List[str]:
        """Nettoie et déduplique les images"""
        if not images:
            return []
        
        unique_images = []
        seen_urls = set()
        
        for img in images:
            # Garde l'URL de base sans paramètres
            base_url = img.split('?')[0]
            if base_url not in seen_urls:
                seen_urls.add(base_url)
                unique_images.append(base_url)  # On garde l'URL nettoyée
        
        return unique_images
    
    def clean_caracteristiques(self, caracteristiques: List[str]) -> List[str]:
        """Nettoie les caractéristiques en enlevant les doublons et informations redondantes"""
        if not caracteristiques:
            return []
        
        caracteristiques_propres = []
        elements_exclus = {'chambre', 'pièces', 'm²', 'étage', 'construit'}
        
        for carac in caracteristiques:
            carac_lower = carac.lower()
            # Exclut les caractéristiques qui sont déjà gérées ailleurs
            if not any(exclu in carac_lower for exclu in elements_exclus):
                caracteristiques_propres.append(carac)
        
        return list(set(caracteristiques_propres))  # Supprime les doublons
    
    def calculate_dpe_score(self, dpe_classe: str) -> int:
        """Calcule un score numérique pour le DPE"""
        return self.dpe_scores.get(dpe_classe, 0) if dpe_classe else 0
    
    def serialize_datetime(self, obj):
        """Fonction pour sérialiser les objets datetime en JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def extract_charges_copropriete(self, charges_str: str) -> Dict[str, Any]:
        """Extrait la valeur numérique et l'unité des charges de copropriété"""
        if not charges_str:
            return {'valeur': None, 'unite': None, 'periode': None}
        
        cleaned = re.sub(r'[  ]', '', charges_str)
        montant_match = re.search(r'(\d+(?:[.,]\d+)?)', cleaned)
        if not montant_match:
            return {'valeur': None, 'unite': None, 'periode': None}
        
        valeur_str = montant_match.group(1).replace(',', '.')
        try:
            valeur = float(valeur_str)
        except ValueError:
            return {'valeur': None, 'unite': None, 'periode': None}
        
        # Détermination de la période
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
            # Par défaut, on considère que c'est annuel si pas précisé
            periode = "annuel"
            unite = "€"
        else:
            periode = None
            unite = None
        
        return {'valeur': valeur, 'unite': unite, 'periode': periode}
    
    def prepare_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute toutes les étapes de préparation sur une annonce pour le format cible"""
        
        # 1. PRÉPARATION DES DONNÉES DE BASE
        prix_numerique = self.clean_price(raw_data['prix'])
        surface_numerique = self.clean_number(raw_data['surface'])
        pieces_numerique = self.clean_number(raw_data['pieces'])
        chambres_extracted = self.extract_chambres(raw_data.get('caracteristiques_detaillees', []))
        localisation_info = self.extract_localisation(raw_data['localisation'])
        code_postal = localisation_info['code_postal']
        
        # Extraction des charges de copropriété avec unité
        charges_info = self.extract_charges_copropriete(raw_data.get('copropriete_charges_previsionnelles', ''))
        
        # Conversion des booléens
        has_video = self.to_boolean(raw_data.get('has_video', False))
        has_visite_virtuelle = self.to_boolean(raw_data.get('has_visite_virtuelle', ''))
        has_photo = len(self.clean_images(raw_data.get('images', []))) > 0
        
        # Calcul des champs manquants AVANT la construction de l'objet
        champs_manquants = []
        if prix_numerique is None:
            champs_manquants.append('prix')
        if surface_numerique is None:
            champs_manquants.append('surface')
        if pieces_numerique is None:
            champs_manquants.append('pieces')
        if code_postal is None:
            champs_manquants.append('code_postal')
        
        # Calcul du score de qualité
        score_qualite = sum([
            1 for champ in [prix_numerique, surface_numerique, pieces_numerique, code_postal]
            if champ is not None
        ]) / 4 * 10
        
        # 2. CONSTRUCTION DU FORMAT CIBLE
        prepared = {
            "reference": raw_data['reference'],
            "titre": raw_data['titre'],
            "prix": {
                "valeur": prix_numerique,
                "devise": "€",
                "au_m2": round(prix_numerique / surface_numerique, 2) if prix_numerique and surface_numerique and surface_numerique > 0 else None
            },
            "surface": {
                "valeur": surface_numerique,
                "unite": "m²"
            },
            "composition": {
                "pieces": pieces_numerique,
                "chambres": chambres_extracted or (pieces_numerique - 1 if pieces_numerique else None),
                "type_bien": raw_data['type_bien']
            },
            "localisation": {
                "ville": localisation_info['ville'],
                "code_postal": code_postal,
                "quartier": self.extract_quartier(raw_data['description']),
                "proximite": self.extract_proximite(raw_data['description'])
            },
            "description": raw_data['description'],
            "caracteristiques": self.clean_caracteristiques(raw_data.get('caracteristiques_detaillees', [])),
            "batiment": {
                "annee_construction": int(raw_data['annee_construction']) if raw_data.get('annee_construction') and raw_data['annee_construction'].isdigit() else None,
                "age_bien": self.current_year - int(raw_data['annee_construction']) if raw_data.get('annee_construction') and raw_data['annee_construction'].isdigit() else None,
                "etage": self.extract_etage(raw_data.get('caracteristiques_detaillees', []))['etage'],
                "etage_total": self.extract_etage(raw_data.get('caracteristiques_detaillees', []))['etage_total'],
                "ascenseur": self.extract_etage(raw_data.get('caracteristiques_detaillees', []))['ascenseur']
            },
            "diagnostics": {
                "dpe": {
                    "classe": raw_data.get('dpe_classe_active'),
                    "score": self.calculate_dpe_score(raw_data.get('dpe_classe_active')),
                    "indice": int(raw_data.get('dpe_score', 0)) if str(raw_data.get('dpe_score', '')).isdigit() else None
                },
                "ges": {
                    "classe": raw_data.get('ges_classe_active'),
                    "score": self.ges_scores.get(raw_data.get('ges_classe_active', ''), 0),
                    "indice": int(raw_data.get('ges_score', 0)) if str(raw_data.get('ges_score', '')).isdigit() else None
                }
            },
            "copropriete": {
                "nb_lots": self.clean_number(raw_data.get('copropriete_nb_lots', '')),
                "charges": {
                    "valeur": charges_info['valeur'],
                    "unite": charges_info['unite'],
                    "periode": charges_info['periode']
                },
                "procedures_en_cours": not bool(raw_data.get('copropriete_procedures'))
            },
            "medias": {
                "images": self.clean_images(raw_data.get('images', [])),
                "nombre_photos": len(self.clean_images(raw_data.get('images', []))),
                "has_video": has_video,  # ← Maintenant garanti boolean
                "has_visite_virtuelle": has_visite_virtuelle,  # ← Maintenant garanti boolean
                "has_photo": has_photo  # ← Maintenant garanti boolean
            },
            "contact": {
                "conseiller": raw_data.get('conseiller_nom_complet'),
                "telephone": raw_data.get('conseiller_telephone'),
                "photo": raw_data.get('conseiller_photo', '').split('?')[0] if raw_data.get('conseiller_photo') else None,
                "lien": raw_data.get('conseiller_lien')
            },
            "url_annonce": raw_data.get('lien'),
            "metadata": {
                "date_extraction": raw_data['date_extraction'],
                "score_qualite": score_qualite,
                "champs_manquants": champs_manquants
            }
        }
        
        # 3. NETTOYAGE DES VALEURS NULL
        # Supprime les clés avec valeurs None dans les sous-objets
        for category in ['prix', 'surface', 'composition', 'localisation', 'batiment', 
                        'diagnostics', 'copropriete', 'medias', 'contact', 'metadata']:
            if category in prepared:
                if category == 'copropriete' and 'charges' in prepared[category]:
                    # Nettoyage spécifique pour l'objet charges
                    if prepared[category]['charges']['valeur'] is None:
                        prepared[category]['charges'] = {k: v for k, v in prepared[category]['charges'].items() if v is not None}
                else:
                    prepared[category] = {k: v for k, v in prepared[category].items() if v is not None}
        
        # Nettoyage spécifique pour les sous-objets diagnostics
        for diagnostic in ['dpe', 'ges']:
            if diagnostic in prepared['diagnostics']:
                prepared['diagnostics'][diagnostic] = {k: v for k, v in prepared['diagnostics'][diagnostic].items() if v is not None}
        
        # Nettoie les listes vides
        if not prepared['caracteristiques']:
            prepared['caracteristiques'] = []
        
        if not prepared['medias']['images']:
            prepared['medias']['images'] = []
        
        return prepared

# UTILISATION
def main_preparation():
    # Charger les données JSON
    with open('annonces.json', 'r', encoding='utf-8') as f:
        annonces = json.load(f)
    
    preparator = DataPreparator()
    annonces_preparees = []
    
    for annonce in annonces:
        annonce_preparee = preparator.prepare_data(annonce)
        annonces_preparees.append(annonce_preparee)
    
    # Sauvegarder les données préparées
    with open('annonces_preparees.json', 'w', encoding='utf-8') as f:
        json.dump(annonces_preparees, f, ensure_ascii=False, indent=2, default=preparator.serialize_datetime)
    
    print(f"Préparation terminée : {len(annonces_preparees)} annonces traitées")
    print(f"Format cible généré avec succès")
    
    # Afficher un exemple pour vérification
    if annonces_preparees:
        print("\nExemple d'annonce préparée (format cible) :")
        exemple = annonces_preparees[0]
        print(json.dumps(exemple, ensure_ascii=False, indent=2))
    
    return annonces_preparees

if __name__ == "__main__":
    main_preparation()