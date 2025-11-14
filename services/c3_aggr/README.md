
# c3_aggr:  Préparer & Agréger les données


## Principe de fonctionnement
```mermaid

flowchart TB
  Collecte[Collecte des données] --> Preparation[Préparation]
  Preparation --> Aggregation[Agrégation]
  Aggregation --> Analyse[Analyse]
  Analyse --> Decisions[Décisions]
  
  Decisions -.->|Amélioration continue| Collecte
  ```

## Phase 1: Preparation des données

```mermaid

flowchart TB
    subgraph Preparation [PHASE 1: PRÉPARATION - Structuration & Normalisation]
        direction TB
        P1[Normalisation Numérique]
        P2[Extraction Géographique]
        P3[Caractéristiques Bien]
        P4[Traitement Médias]
        P5[Calcul Scores]
        P6[Structuration Finale]
        
        P1 --> P2 --> P3 --> P4 --> P5 --> P6
    end
    
    %% NORMALISATION NUMÉRIQUE
    P1 --> NN1["Prix: '380 000 €' → 380000"]
    P1 --> NN2["Surface: '39' → 39.0"]
    P1 --> NN3["Pièces: '3' → 3"]
    P1 --> NN4["Booléens: standardisation"]
    
    %% EXTRACTION GÉOGRAPHIQUE
    P2 --> EG1["Localisation: extraction code postal 75019"]
    P2 --> EG2["Quartier: 'Buttes Chaumont'"]
    P2 --> EG3["Proximités: métro, écoles, commerces"]
    P2 --> EG4["Ville: Paris"]
    
    %% CARACTÉRISTIQUES BIEN
    P3 --> CB1["Étage: 5/6 + ascenseur: false"]
    P3 --> CB2["Chambres: 1 vs pièces: 3 → correction"]
    P3 --> CB3["Caractéristiques: nettoyage liste"]
    P3 --> CB4["Âge bien: 2025-1900 = 125 ans"]
    
    %% TRAITEMENT MÉDIAS
    P4 --> TM1["Images: déduplication URLs"]
    P4 --> TM2["Photos: 7 uniques identifiées"]
    P4 --> TM3["Vidéo: false → booléen"]
    P4 --> TM4["Visite virtuelle: false → booléen"]
    
    %% CALCUL SCORES
    P5 --> CS1["Score DPE: F → 3/10"]
    P5 --> CS2["Score GES: C → 6/10"]
    P5 --> CS3["Charges: '1 176 €/an' → 1176"]
    P5 --> CS4["Score qualité: 8.5/10"]
    
    %% STRUCTURATION FINALE
    P6 --> SF1["Modules: Prix, Surface, Localisation..."]
    P6 --> SF2["Nettoyage: suppression valeurs None"]
    P6 --> SF3["Métadonnées: étapes traitées"]
    P6 --> SF4["JSON structuré prêt pour agrégation"]
    
    %% FLUX DE DONNÉES
    DonneesBrutes[("Données brutes<br/>JSON")] --> Preparation
    P6 --> DonneesPreparees[("Données préparées<br/>Structurées & Normalisées")]
    
    %% STYLES
    classDef normalisation fill:#e3f2fd
    classDef geographie fill:#e8f5e8
    classDef caracteristiques fill:#fff3e0
    classDef medias fill:#f3e5f5
    classDef scores fill:#ffebee
    classDef structuration fill:#fce4ec
    
    class P1,NN1,NN2,NN3,NN4 normalisation
    class P2,EG1,EG2,EG3,EG4 geographie
    class P3,CB1,CB2,CB3,CB4 caracteristiques
    class P4,TM1,TM2,TM3,TM4 medias
    class P5,CS1,CS2,CS3,CS4 scores
    class P6,SF1,SF2,SF3,SF4 structuration
  
  ```

## Schéma UML après la préparation des données

```mermaid

classDiagram
    class AnnonceImmobiliere {
        -String reference
        -String titre
        -Prix prix
        -Surface surface
        -Composition composition
        -Localisation localisation
        -String description
        -List~String~ caracteristiques
        -Batiment batiment
        -Diagnostics diagnostics
        -Copropriete copropriete
        -Medias medias
        -Contact contact
        -String url_annonce
        -Metadata metadata
    }

    class Prix {
        -Float valeur
        -String devise
        -Float au_m2
    }

    class Surface {
        -Float valeur
        -String unite
    }

    class Composition {
        -Float pieces
        -Integer chambres
        -String type_bien
    }

    class Localisation {
        -String ville
        -String code_postal
        -String quartier
        -String proximite
    }

    class Batiment {
        -Integer annee_construction
        -Integer age_bien
        -Integer etage
        -Integer etage_total
        -Boolean ascenseur
    }

    class Diagnostics {
        -Diagnostic dpe
        -Diagnostic ges
    }

    class Diagnostic {
        -String classe
        -Integer score
    }

    class Copropriete {
        -Float nb_lots
        -Charges charges
        -Boolean procedures_en_cours
    }

    class Charges {
        -Float valeur
        -String unite
        -String periode
    }

    class Medias {
        -List~String~ images
        -Integer nombre_photos
        -Boolean has_video
        -Boolean has_visite_virtuelle
        -Boolean has_photo
    }

    class Contact {
        -String conseiller
        -String telephone
        -String photo
        -String lien
    }

    class Metadata {
        -String date_extraction
        -Float score_qualite
        -List~String~ champs_manquants
    }

    %% Relations de composition
    AnnonceImmobiliere *-- Prix
    AnnonceImmobiliere *-- Surface
    AnnonceImmobiliere *-- Composition
    AnnonceImmobiliere *-- Localisation
    AnnonceImmobiliere *-- Batiment
    AnnonceImmobiliere *-- Diagnostics
    AnnonceImmobiliere *-- Copropriete
    AnnonceImmobiliere *-- Medias
    AnnonceImmobiliere *-- Contact
    AnnonceImmobiliere *-- Metadata
    
    Diagnostics *-- Diagnostic : dpe
    Diagnostics *-- Diagnostic : ges
    Copropriete *-- Charges
```
  
## Phase 2: Agrégation des données

```mermaid
flowchart TB
    subgraph Aggregation [PHASE 2: AGRÉGATION - Analyse Avancée]
        direction TB
        A1[Calculs Performance]
        A2[Scores & Indicateurs]
        A3[Analyse Marché]
        A4[Segmentation Stratégique]
        A5[Recommandations Actionnables]
        
        A1 --> A2 --> A3 --> A4 --> A5
    end
    
    %% CALCULS PERFORMANCE
    A1 --> CP1["Rentabilité: rendement 4.2% annuel"]
    A1 --> CP2["Prix/m² calculé: 9744 €/m²"]
    A1 --> CP3["Loyer estimé: 1583 €/mois"]
    A1 --> CP4["Surface/pièce: 13m²/pièce"]
    
    %% SCORES & INDICATEURS
    A2 --> SC1["Score emplacement: 8.0/10"]
    A2 --> SC2["Score modernité: 6.5/10"]
    A2 --> SC3["Score global: 7.2/10"]
    A2 --> SC4["Score DPE: 3/10 → F"]
    
    %% ANALYSE MARCHÉ
    A3 --> AM1["Positionnement: sous-coté -5.2%"]
    A3 --> AM2["Z-score: -0.8 écart-type"]
    A3 --> AM3["Prix m² marché: 10280 €"]
    A3 --> AM4["Concurrence: 12 biens similaires"]
    
    %% SEGMENTATION STRATÉGIQUE
    A4 --> SG1["Segment: ancien_accessible"]
    A4 --> SG2["Cible: investisseurs_rénovation"]
    A4 --> SG3["Potentiel: valorisation +15%"]
    A4 --> SG4["Risque: DPE F + étage 5"]
    
    %% RECOMMANDATIONS ACTIONNABLES
    A5 --> RC1["Prix: maintenir stratégie"]
    A5 --> RC2["Marketing: visuel rénovation"]
    A5 --> RC3["Ciblage: jeunes actifs"]
    A5 --> RC4["Optimisation: photos + visite virtuelle"]
    
    %% FLUX DE DONNÉES
    Préparation --> Aggregation
    A5 --> Stockage[("Base de données<br/>agrégée")]
    
    %% STYLES
    classDef performance fill:#e3f2fd
    classDef scores fill:#e8f5e8
    classDef marche fill:#fff3e0
    classDef segmentation fill:#f3e5f5
    classDef recommandation fill:#ffebee
    
    class A1,CP1,CP2,CP3,CP4 performance
    class A2,SC1,SC2,SC3,SC4 scores
    class A3,AM1,AM2,AM3,AM4 marche
    class A4,SG1,SG2,SG3,SG4 segmentation
    class A5,RC1,RC2,RC3,RC4 recommandation
  
  ```

## Pré-requis

    - uv

## Installation et Usage

```bash
# Lancer la préparation des données
uv run app_prep_data.py

# Lancer l'aggrégation des données
uv run app_aggr_data.py
```

## Traitements détaillés :

### Préparation :

    - Nettoyer prix : "380 000 €" → 380000 (nombre)
    - Extraire surface : "39" → 39.0 (float)
    - Standardiser localisation : extraire arrondissement 75019
    - Corriger incohérence : "1 chambre" mais "3 pièces"

###  Agrégation :

    - Calculer prix_au_m2 : 380000 / 39 = 9744 €/m²
    - Score énergétique : DPE F = mauvais → impact valeur
    - Catégoriser : "Appartement" + 1900 = "ancien"
    - Enrichir avec données quartier Buttes Chaumont

###  Analyse :

    - Comparer avec prix moyen du 75019
    - Analyser rentabilité : charges copropriété 1176€/an
    - Détecter opportunité : appartement sans travaux
    - Alerter sur DPE F nécessitant rénovation

### Décisions :

    - Recommandation prix : ajuster selon marché
    - Prioriser pour prospects cherchant "sans travaux"
    - Stratégie rénovation énergétique
    - Ciblage marketing : familles écoles proximité