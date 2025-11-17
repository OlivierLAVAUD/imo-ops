from fastapi import FastAPI, HTTPException, Query, Depends, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import uvicorn
import hashlib
import secrets

# Charger les variables d'environnement
load_dotenv()

# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "votre-secret-tres-securise-changez-moi-en-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

app = FastAPI(
    title="API Immobilière IMO-Ops",
    description="API sécurisée pour les données immobilières IMO-Ops",
    version="2.0.0"
)

# CORS configuré pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour le développement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la base de données
def get_db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('IMO_DB', 'imo_db'),
        'user': os.getenv('IMO_USER', 'postgres'),
        'password': os.getenv('IMO_PASSWORD', 'password'),
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

# Fonction de hachage simple (pour le développement)
def hash_password(password: str) -> str:
    """Hachage simple du mot de passe (à remplacer par bcrypt en production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérification du mot de passe"""
    return hash_password(plain_password) == hashed_password

# Base de données utilisateurs simulée
users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@immo-ops.com",
        "hashed_password": hash_password("admin123"),  # Mot de passe: admin123
        "disabled": False,
        "role": "admin",
        "permissions": ["read:annonces", "read:statistiques", "read:analytics"]
    },
    "user": {
        "username": "user", 
        "email": "user@immo-ops.com",
        "hashed_password": hash_password("user123"),  # Mot de passe: user123
        "disabled": False,
        "role": "user",
        "permissions": ["read:annonces"]
    }
}

# Fonctions d'authentification
def get_user(db: dict, username: str) -> Optional[dict]:
    if username in db:
        return db[username]
    return None

def authenticate_user(db: dict, username: str, password: str) -> Optional[dict]:
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(users_db, username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("disabled"):
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user

def check_permission(user: dict, required_permission: str) -> bool:
    permissions = user.get("permissions", [])
    return required_permission in permissions

# Routes d'authentification
@app.post("/token")
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(users_db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires,
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"], 
        "role": current_user["role"],
        "permissions": current_user["permissions"]
    }

# Routes publiques
@app.get("/")
async def root():
    return {
        "message": "API Immobilière IMO-Ops - Bienvenue",
        "version": "2.0.0",
        "documentation": "/docs",
        "authentification": "Utilisez POST /token avec username=admin&password=admin123"
    }

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = "connected"
        cursor.close()
        conn.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status
    }

# Routes protégées
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
    current_user: dict = Depends(get_current_active_user),
    conn = Depends(get_db_connection)
):
    """
    🔒 Récupérer la liste des annonces (Authentification requise)
    """
    if not check_permission(current_user, "read:annonces"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes pour accéder aux annonces"
        )
    
    try:
        cursor = conn.cursor()
        
        query = "SELECT * FROM annonces WHERE 1=1"
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
async def get_annonce_by_id(
    annonce_id: int, 
    current_user: dict = Depends(get_current_active_user),
    conn = Depends(get_db_connection)
):
    """
    🔒 Récupérer une annonce spécifique par son ID
    """
    if not check_permission(current_user, "read:annonces"):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM annonces WHERE id_annonce = %s", (annonce_id,))
        annonce = cursor.fetchone()
        
        if not annonce:
            raise HTTPException(status_code=404, detail="Annonce non trouvée")
        
        result = dict(annonce)
        
        # Récupérer les données liées
        cursor.execute("SELECT * FROM caracteristiques WHERE id_annonce = %s", (annonce_id,))
        result['caracteristiques'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM images WHERE id_annonce = %s", (annonce_id,))
        result['images'] = [dict(row) for row in cursor.fetchall()]
        
        # Masquage des données sensibles selon les permissions
        if check_permission(current_user, "read:analytics"):
            cursor.execute("SELECT * FROM conseiller WHERE id_annonce = %s", (annonce_id,))
        else:
            cursor.execute("SELECT nom_complet, photo, note FROM conseiller WHERE id_annonce = %s", (annonce_id,))
        
        conseiller = cursor.fetchone()
        result['conseiller'] = dict(conseiller) if conseiller else None
        
        cursor.execute("SELECT * FROM dpe WHERE id_annonce = %s", (annonce_id,))
        dpe = cursor.fetchone()
        result['dpe'] = dict(dpe) if dpe else None
        
        cursor.execute("SELECT * FROM copropriete WHERE id_annonce = %s", (annonce_id,))
        copropriete = cursor.fetchone()
        result['copropriete'] = dict(copropriete) if copropriete else None
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/annonces/reference/{reference}", response_model=Dict[str, Any])
async def get_annonce_by_reference(
    reference: str, 
    current_user: dict = Depends(get_current_active_user),
    conn = Depends(get_db_connection)
):
    if not check_permission(current_user, "read:annonces"):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM annonces WHERE reference = %s", (reference,))
        annonce = cursor.fetchone()
        
        if not annonce:
            raise HTTPException(status_code=404, detail="Annonce non trouvée")
        
        return dict(annonce)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/annonces/search", response_model=List[Dict[str, Any]])
async def search_annonces(
    q: str = Query(..., description="Terme de recherche"),
    current_user: dict = Depends(get_current_active_user),
    conn = Depends(get_db_connection)
):
    if not check_permission(current_user, "read:annonces"):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT * FROM annonces 
            WHERE titre ILIKE %s OR description ILIKE %s OR localisation ILIKE %s
            ORDER BY id_annonce DESC LIMIT 100
        """
        search_term = f"%{q}%"
        cursor.execute(query, [search_term] * 3)
        annonces = cursor.fetchall()
        return [dict(annonce) for annonce in annonces]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/statistiques")
async def get_statistiques(
    current_user: dict = Depends(get_current_active_user),
    conn = Depends(get_db_connection)
):
    if not check_permission(current_user, "read:statistiques"):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    try:
        cursor = conn.cursor()
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM annonces")
        stats['total_annonces'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT type_bien, COUNT(*) as count FROM annonces WHERE type_bien IS NOT NULL GROUP BY type_bien")
        stats['annonces_par_type'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT AVG(prix) as prix_moyen, AVG(surface) as surface_moyenne FROM annonces WHERE prix IS NOT NULL")
        prix_stats = cursor.fetchone()
        stats['prix_moyen'] = float(prix_stats['prix_moyen']) if prix_stats['prix_moyen'] else None
        stats['surface_moyenne'] = float(prix_stats['surface_moyenne']) if prix_stats['surface_moyenne'] else None
        
        cursor.execute("SELECT dpe_classe_active, COUNT(*) as count FROM annonces WHERE dpe_classe_active IS NOT NULL GROUP BY dpe_classe_active")
        stats['distribution_dpe'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/types-bien")
async def get_types_bien(
    current_user: dict = Depends(get_current_active_user),
    conn = Depends(get_db_connection)
):
    if not check_permission(current_user, "read:annonces"):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT type_bien FROM annonces WHERE type_bien IS NOT NULL")
        types = [dict(row) for row in cursor.fetchall()]
        return types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/localisations")
async def get_localisations(
    current_user: dict = Depends(get_current_active_user),
    conn = Depends(get_db_connection)
):
    if not check_permission(current_user, "read:annonces"):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT localisation FROM annonces WHERE localisation IS NOT NULL LIMIT 50")
        localisations = [dict(row) for row in cursor.fetchall()]
        return localisations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Route pour tester sans authentification
@app.get("/public/annonces")
async def get_public_annonces(
    limit: int = Query(10, ge=1, le=100),
    conn = Depends(get_db_connection)
):
    """
    Route publique pour tester sans authentification (limité à 10 résultats)
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT reference, titre, prix, surface, localisation FROM annonces ORDER BY id_annonce DESC LIMIT %s", (limit,))
        annonces = cursor.fetchall()
        return [dict(annonce) for annonce in annonces]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Démarrage de l'API Immobilière IMO-Ops...")
    print("📊 URL de documentation: http://localhost:8000/docs")
    print("🔐 Identifiants de test: admin/admin123 ou user/user123")
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )