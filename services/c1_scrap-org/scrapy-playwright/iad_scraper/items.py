import scrapy

class IadItem(scrapy.Item):
    # Informations de base
    reference = scrapy.Field()
    titre = scrapy.Field()
    titre_complet = scrapy.Field()
    lien = scrapy.Field()
    prix = scrapy.Field()
    prix_detaille = scrapy.Field()
    prix_au_m2 = scrapy.Field()
    localisation = scrapy.Field()
    localisation_complete = scrapy.Field()
    date_extraction = scrapy.Field()
    
    # Caractéristiques techniques
    surface = scrapy.Field()
    surface_terrain = scrapy.Field()
    pieces = scrapy.Field()
    type_bien = scrapy.Field()
    description = scrapy.Field()
    caracteristiques_detaillees = scrapy.Field()
    equipements = scrapy.Field()
    annee_construction = scrapy.Field()
    honoraires = scrapy.Field()
    
    # Médias
    image_url = scrapy.Field()
    images = scrapy.Field()
    toutes_les_photos = scrapy.Field()
    nombre_photos = scrapy.Field()
    has_video = scrapy.Field()
    has_visite_virtuelle = scrapy.Field()
    media_info = scrapy.Field()
    
    # Performance énergétique
    dpe_classe_active = scrapy.Field()
    ges_classe_active = scrapy.Field()
    dpe_consommation_energie_primaire = scrapy.Field()
    dpe_consommation_energie_finale = scrapy.Field()
    dpe_emissions = scrapy.Field()
    depenses_energie_min = scrapy.Field()
    depenses_energie_max = scrapy.Field()
    ges_emissions = scrapy.Field()
    
    # Copropriété
    copropriete_nb_lots = scrapy.Field()
    copropriete_charges_previsionnelles = scrapy.Field()
    copropriete_procedures = scrapy.Field()
    
    # Conseiller
    conseiller_nom_complet = scrapy.Field()
    conseiller_telephone = scrapy.Field()
    conseiller_lien = scrapy.Field()
    conseiller_photo = scrapy.Field()
    conseiller_note = scrapy.Field()
    conseiller_nombre_avis = scrapy.Field()
    
    # Badges et autres
    badges = scrapy.Field()
    date_publication = scrapy.Field()