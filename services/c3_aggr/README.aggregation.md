
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
    subgraph Preparation [PHASE 1: PRÉPARATION]
        direction TB
        N1[Nettoyage Structurel]
        N2[Standardisation]
        N3[Correction Données]
        N4[Extraction Information]
        N5[Validation Qualité]
        
        N1 --> N2 --> N3 --> N4 --> N5
    end
    
    N1 --> NC1["Prix: '380 000 €' → 380000"]
    N1 --> NC2["Surface: '39' → 39.0"]
    N1 --> NC3["Charges: '1 176 € / an' → 1176"]
    
    N2 --> ST1["Localisation: 'Paris 75019' → arrondissement"]
    N2 --> ST2["Type bien: standardisation catégories"]
    N2 --> ST3["Date extraction: format datetime"]
    
    N3 --> CR1["Incohérence pièces: 1 chambre vs 3 pièces"]
    N3 --> CR2["Images dupliquées: 7 photos uniques"]
    N3 --> CR3["DPE: classes A-G → scores numériques"]
    
    N4 --> EX1["Année construction: '1900' → siècle"]
    N4 --> EX2["Caractéristiques: liste → dimensions"]
    N4 --> EX3["Localisation: extraction coordonnées"]
    
    N5 --> VQ1["Valeurs manquantes: honoraires, note"]
    VQ1 --> VQ2["Plausibilité: prix/m² cohérent"]
    VQ2 --> VQ3["Complétude: champs obligatoires"]
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
    subgraph Aggregation [PHASE 2: AGRÉGATION]
        direction TB
        A1[Calculs Métier]
        A2[Enrichissement Contextuel]
        A3[Segmentation]
        A4[Indicateurs Synthétiques]
        A5[Intégration Multi-Sources]
        
        A1 --> A2 --> A3 --> A4 --> A5
    end
    
    A1 --> CA1["Prix/m²: 380000 / 39 = 9744 €"]
    A1 --> CA2["Rentabilité: charges 1176€/an"]
    A1 --> CA3["Surface/pièce: 39m² / 3 = 13m²"]
    A1 --> CA4["Âge bien: 2025 - 1900 = 125 ans"]
    
    A2 --> EN1["Score énergétique: DPE F → 4/10"]
    A2 --> EN2["Accessibilité: étage 5 sans ascenseur"]
    A2 --> EN3["Environnement: proximité écoles/commerces"]
    A2 --> EN4["Marché: prix moyen arrondissement"]
    
    A3 --> SG1["Segment: 'ancien sans ascenseur'"]
    SG1 --> SG2["Cible: 'budget moyen 75019'"]
    SG2 --> SG3["Potentiel: 'rénovation énergétique'"]
    
    A4 --> IN1["Attractivité: score global 7/10"]
    IN1 --> IN2["Opportunité: DPE à améliorer"]
    IN2 --> IN3["Risque: copropriété 48 lots"]
    
    A5 --> IM1["Croisement: données géographiques"]
    IM1 --> IM2["Historique: évolution prix secteur"]
    IM2 --> IM3["Benchmark: biens similaires"]
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