from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
import uvicorn

# Charger les variables d'environnement
load_dotenv()

app = FastAPI(
    title="API Immobilière",
    description="API pour consulter les données immobilières",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la base de données
def get_db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('IMO_DB') or os.getenv('DB_NAME', 'imo_db'),
        'user': os.getenv('IMO_USER') or os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('IMO_PASSWORD') or os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
    }

# Dépendance pour la connexion à la base de données
def get_db_connection():
    config = get_db_config()
    try:
        conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion à la base: {str(e)}")

# Modèles de réponse
class AnnonceBase:
    def __init__(self, data):
        self.id_annonce = data.get('id_annonce')
        self.reference = data.get('reference')
        self.titre = data.get('titre')
        self.titre_complet = data.get('titre_complet')
        self.prix = data.get('prix')
        self.prix_detaille = data.get('prix_detaille')
        self.prix_au_m2 = data.get('prix_au_m2')
        self.localisation = data.get('localisation')
        self.localisation_complete = data.get('localisation_complete')
        self.surface = data.get('surface')
        self.surface_terrain = data.get('surface_terrain')
        self.pieces = data.get('pieces')
        self.type_bien = data.get('type_bien')
        self.description = data.get('description')
        self.annee_construction = data.get('annee_construction')
        self.honoraires = data.get('honoraires')
        self.image_url = data.get('image_url')
        self.nombre_photos = data.get('nombre_photos')
        self.has_video = data.get('has_video')
        self.has_visite_virtuelle = data.get('has_visite_virtuelle')
        self.media_info = data.get('media_info')
        self.lien = data.get('lien')
        self.date_extraction = data.get('date_extraction')
        self.dpe_classe_active = data.get('dpe_classe_active')
        self.ges_classe_active = data.get('ges_classe_active')
        self.depenses_energie_min = data.get('depenses_energie_min')
        self.depenses_energie_max = data.get('depenses_energie_max')
        self.annee_reference = data.get('annee_reference')

class CaracteristiqueBase:
    def __init__(self, data):
        self.id_caracteristique = data.get('id_caracteristique')
        self.id_annonce = data.get('id_annonce')
        self.valeur = data.get('valeur')

class ImageBase:
    def __init__(self, data):
        self.id_image = data.get('id_image')
        self.id_annonce = data.get('id_annonce')
        self.url = data.get('url')
        self.ordre = data.get('ordre')

class ConseillerBase:
    def __init__(self, data):
        self.id_conseiller = data.get('id_conseiller')
        self.id_annonce = data.get('id_annonce')
        self.nom_complet = data.get('nom_complet')
        self.telephone = data.get('telephone')
        self.lien = data.get('lien')
        self.photo = data.get('photo')
        self.note = data.get('note')

class DPEBase:
    def __init__(self, data):
        self.id_dpe = data.get('id_dpe')
        self.id_annonce = data.get('id_annonce')
        self.classe_energie = data.get('classe_energie')
        self.indice_energie = data.get('indice_energie')
        self.classe_climat = data.get('classe_climat')
        self.indice_climat = data.get('indice_climat')

class CoproprieteBase:
    def __init__(self, data):
        self.id_copropriete = data.get('id_copropriete')
        self.id_annonce = data.get('id_annonce')
        self.nb_lots = data.get('nb_lots')
        self.charges_previsionnelles = data.get('charges_previsionnelles')
        self.procedures = data.get('procedures')

# Routes de l'API

@app.get("/")
async def root():
    return {
        "message": "API Immobilière - Bienvenue",
        "version": "1.0.0",
        "endpoints": {
            "annonces": "/annonces",
            "annonce_by_id": "/annonces/{id}",
            "annonce_by_reference": "/annonces/reference/{reference}",
            "search": "/annonces/search",
            "statistiques": "/statistiques"
        }
    }

@app.get("/annonces", response_model=List[Dict[str, Any]])
async def get_annonces(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    type_bien: Optional[str] = Query(None, description="Filtrer par type de bien"),
    min_prix: Optional[float] = Query(None, ge=0, description="Prix minimum"),
    max_prix: Optional[float] = Query(None, ge=0, description="Prix maximum"),
    min_surface: Optional[float] = Query(None, ge=0, description="Surface minimum"),
    max_surface: Optional[float] = Query(None, ge=0, description="Surface maximum"),
    localisation: Optional[str] = Query(None, description="Localisation (recherche partielle)"),
    conn = Depends(get_db_connection)
):
    """
    Récupérer la liste des annonces avec pagination et filtres
    """
    try:
        cursor = conn.cursor()
        
        # Construction de la requête avec filtres
        query = """
            SELECT * FROM annonces 
            WHERE 1=1
        """
        params = []
        
        if type_bien:
            query += " AND type_bien ILIKE %s"
            params.append(f"%{type_bien}%")
        
        if min_prix:
            query += " AND prix >= %s"
            params.append(min_prix)
        
        if max_prix:
            query += " AND prix <= %s"
            params.append(max_prix)
        
        if min_surface:
            query += " AND surface >= %s"
            params.append(min_surface)
        
        if max_surface:
            query += " AND surface <= %s"
            params.append(max_surface)
        
        if localisation:
            query += " AND (localisation ILIKE %s OR localisation_complete ILIKE %s)"
            params.extend([f"%{localisation}%", f"%{localisation}%"])
        
        query += " ORDER BY id_annonce DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        annonces = cursor.fetchall()
        
        return [dict(annonce) for annonce in annonces]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des annonces: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/annonces/{annonce_id}", response_model=Dict[str, Any])
async def get_annonce_by_id(annonce_id: int, conn = Depends(get_db_connection)):
    """
    Récupérer une annonce spécifique par son ID avec toutes ses données liées
    """
    try:
        cursor = conn.cursor()
        
        # Récupérer l'annonce principale
        cursor.execute("SELECT * FROM annonces WHERE id_annonce = %s", (annonce_id,))
        annonce = cursor.fetchone()
        
        if not annonce:
            raise HTTPException(status_code=404, detail="Annonce non trouvée")
        
        result = dict(annonce)
        
        # Récupérer les caractéristiques
        cursor.execute("SELECT * FROM caracteristiques WHERE id_annonce = %s ORDER BY id_caracteristique", (annonce_id,))
        result['caracteristiques'] = [dict(row) for row in cursor.fetchall()]
        
        # Récupérer les images
        cursor.execute("SELECT * FROM images WHERE id_annonce = %s ORDER BY ordre", (annonce_id,))
        result['images'] = [dict(row) for row in cursor.fetchall()]
        
        # Récupérer le conseiller
        cursor.execute("SELECT * FROM conseiller WHERE id_annonce = %s", (annonce_id,))
        conseiller = cursor.fetchone()
        result['conseiller'] = dict(conseiller) if conseiller else None
        
        # Récupérer le DPE
        cursor.execute("SELECT * FROM dpe WHERE id_annonce = %s", (annonce_id,))
        dpe = cursor.fetchone()
        result['dpe'] = dict(dpe) if dpe else None
        
        # Récupérer la copropriété
        cursor.execute("SELECT * FROM copropriete WHERE id_annonce = %s", (annonce_id,))
        copropriete = cursor.fetchone()
        result['copropriete'] = dict(copropriete) if copropriete else None
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'annonce: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/annonces/reference/{reference}", response_model=Dict[str, Any])
async def get_annonce_by_reference(reference: str, conn = Depends(get_db_connection)):
    """
    Récupérer une annonce par sa référence
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM annonces WHERE reference = %s", (reference,))
        annonce = cursor.fetchone()
        
        if not annonce:
            raise HTTPException(status_code=404, detail="Annonce non trouvée")
        
        return dict(annonce)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'annonce: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/annonces/search", response_model=List[Dict[str, Any]])
async def search_annonces(
    q: str = Query(..., description="Terme de recherche"),
    conn = Depends(get_db_connection)
):
    """
    Rechercher des annonces par terme dans le titre, description ou localisation
    """
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM annonces 
            WHERE titre ILIKE %s 
               OR titre_complet ILIKE %s 
               OR description ILIKE %s 
               OR localisation ILIKE %s 
               OR localisation_complete ILIKE %s
            ORDER BY id_annonce DESC
            LIMIT 100
        """
        
        search_term = f"%{q}%"
        cursor.execute(query, [search_term] * 5)
        annonces = cursor.fetchall()
        
        return [dict(annonce) for annonce in annonces]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/statistiques")
async def get_statistiques(conn = Depends(get_db_connection)):
    """
    Récupérer les statistiques générales de la base de données
    """
    try:
        cursor = conn.cursor()
        
        stats = {}
        
        # Nombre total d'annonces
        cursor.execute("SELECT COUNT(*) FROM annonces")
        stats['total_annonces'] = cursor.fetchone()['count']
        
        # Nombre d'annonces par type de bien
        cursor.execute("""
            SELECT type_bien, COUNT(*) as count 
            FROM annonces 
            WHERE type_bien IS NOT NULL 
            GROUP BY type_bien 
            ORDER BY count DESC
        """)
        stats['annonces_par_type'] = [dict(row) for row in cursor.fetchall()]
        
        # Prix moyen et surface moyenne
        cursor.execute("""
            SELECT 
                AVG(prix) as prix_moyen,
                AVG(surface) as surface_moyenne,
                AVG(prix_au_m2) as prix_m2_moyen
            FROM annonces 
            WHERE prix IS NOT NULL AND surface IS NOT NULL
        """)
        prix_stats = cursor.fetchone()
        stats['prix_moyen'] = float(prix_stats['prix_moyen']) if prix_stats['prix_moyen'] else None
        stats['surface_moyenne'] = float(prix_stats['surface_moyenne']) if prix_stats['surface_moyenne'] else None
        stats['prix_m2_moyen'] = float(prix_stats['prix_m2_moyen']) if prix_stats['prix_m2_moyen'] else None
        
        # Distribution DPE
        cursor.execute("""
            SELECT dpe_classe_active, COUNT(*) as count 
            FROM annonces 
            WHERE dpe_classe_active IS NOT NULL 
            GROUP BY dpe_classe_active 
            ORDER BY dpe_classe_active
        """)
        stats['distribution_dpe'] = [dict(row) for row in cursor.fetchall()]
        
        # Compteurs des tables liées
        cursor.execute("SELECT COUNT(*) FROM caracteristiques")
        stats['total_caracteristiques'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM images")
        stats['total_images'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM conseiller")
        stats['total_conseillers'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM dpe")
        stats['total_dpe'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM copropriete")
        stats['total_coproprietes'] = cursor.fetchone()['count']
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/types-bien")
async def get_types_bien(conn = Depends(get_db_connection)):
    """
    Récupérer la liste des types de biens disponibles
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT type_bien, COUNT(*) as count
            FROM annonces 
            WHERE type_bien IS NOT NULL AND type_bien != ''
            GROUP BY type_bien 
            ORDER BY count DESC
        """)
        
        types = [dict(row) for row in cursor.fetchall()]
        return types
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des types: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/localisations")
async def get_localisations(conn = Depends(get_db_connection)):
    """
    Récupérer la liste des localisations disponibles
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT localisation, COUNT(*) as count
            FROM annonces 
            WHERE localisation IS NOT NULL AND localisation != ''
            GROUP BY localisation 
            ORDER BY count DESC
            LIMIT 100
        """)
        
        localisations = [dict(row) for row in cursor.fetchall()]
        return localisations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des localisations: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)