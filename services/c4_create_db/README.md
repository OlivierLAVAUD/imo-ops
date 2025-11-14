# c4_create_db

## Modele de donnée IMO


```mermaid
classDiagram
    class Annonce {
        +String reference
        +String titre
        +String titre_complet
        +String prix
        +String prix_detaille
        +String prix_au_m2
        +String localisation
        +String localisation_complete
        +Float surface
        +Float surface_terrain
        +Integer pieces
        +String type_bien
        +String description
        +Integer annee_construction
        +String honoraires
        +String image_url
        +Integer nombre_photos
        +Boolean has_video
        +Boolean has_visite_virtuelle
        +String media_info
        +String lien
        +Date date_extraction
        +String dpe_classe_active
        +String ges_classe_active
        +String depenses_energie_min
        +String depenses_energie_max
        +Integer annee_reference
    }

    class Caracteristique {
        +String valeur
    }

    class Image {
        +String url
        +Integer ordre
    }

    class Copropriete {
        +Integer nb_lots
        +String charges_previsionnelles
        +String procedures
    }

    class Conseiller {
        +String nom_complet
        +String telephone
        +String lien
        +String photo
        +String note
    }

    class DPE {
        +String classe_energie
        +Integer indice_energie
        +String classe_climat
        +Integer indice_climat
    }

    Annonce --> Copropriete : décrit une
    Annonce --> Conseiller : gérée par
    Annonce --> DPE : possède un
    Annonce --> Caracteristique : a pour
    Annonce --> Image : contient
```


# Installation

```bash
# Creation de la base de données imo_db
psql -U postgres -f sql\create_imo_db_init.sql
# Acces a imo_db et reation de la structure et des données partielles.
psql -U postgres -d imo_db -f sql\create_imo_db.sql

# Acces a la base pour verification
psql -U postgres -d imo_db
```

# Usage 

```bash
# Cleaning de la base imo_db
uv run clean_imo_db.py
# Import des données dans la base imo_db a partir du fichier json
uv run import_annonces.py

```

# Exemples de requetes
```bash
select id_annonce, reference from annonces group by annonces.id_annonce,reference order by reference ;
select * from annonces where annonces.id_annonce=1 ;
select * from annonces where reference = '1885312';

SELECT 
    a.*,
    c.nom_complet as conseiller_nom_complet,
    c.telephone as conseiller_telephone,
    c.lien as conseiller_lien,
    c.photo as conseiller_photo,
    c.note as conseiller_note,
    d.classe_energie as dpe_classe_energie,
    d.indice_energie as dpe_indice_energie,
    d.classe_climat as dpe_classe_climat,
    d.indice_climat as dpe_indice_climat,
    cp.nb_lots as copropriete_nb_lots,
    cp.charges_previsionnelles as copropriete_charges,
    cp.procedures as copropriete_procedures,
    car.valeur as caracteristiques,
    img.url as images_url,
    img.ordre as images_ordre
FROM annonces a
LEFT JOIN conseiller c ON a.id_annonce = c.id_annonce
LEFT JOIN dpe d ON a.id_annonce = d.id_annonce
LEFT JOIN copropriete cp ON a.id_annonce = cp.id_annonce
LEFT JOIN caracteristiques car ON a.id_annonce = car.id_annonce
LEFT JOIN images img ON a.id_annonce = img.id_annonce
WHERE a.reference = '1885312';


```

