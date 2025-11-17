# 🏠 API Immobilière - IMO-Ops

API sécurisée pour la gestion et la consultation des données immobilières IMO-Ops à partir d'une base de données PostgresSQL.

- 🔐 Gestion des données : Publiques vs Protégées

L'API implémente une stratégie de sécurité à deux niveaux pour l'accès aux données :

- 🔓 Données publiques : Accessibles sans authentification via /public/annonces, cette route retourne un sous-ensemble limité de champs (référence, titre, prix, surface, localisation) spécialement sélectionnés pour un usage externe. Cette approche protège les informations sensibles tout en permettant une consultation basique.

- 🔐 Données complètes : Accessibles uniquement après authentification via /annonces, cette route donne accès à l'intégralité des données avec tous les champs de la base (description détaillée, coordonnées GPS, DPE, caractéristiques techniques, etc.). L'authentification JWT garantit que seuls les utilisateurs autorisés peuvent accéder aux informations complètes.

Cette séparation permet de maintenir une accessibilité publique tout en préservant la confidentialité des données métier sensibles.



📋 Table des matières

- [Fonctionnalités](#✨fonctionnalités)
- [Technologies utilisées](#🛠technologies-utilisées)
- [Installation](#📥installation)
- [Configuration](#⚙️configuration)
- [Utilisation](#🎯utilisation)
- [Endpoints](#📡endpoints)
- [Authentification](#🔑authentification)
- [Sécurité](#🛡️sécurité)
- [Développement](#développement)


 # ✨Fonctionnalités 

    - 🔐 Authentification JWT sécurisée
    - 👥 Gestion des permissions utilisateurs
    - 🛡️ Sécurité avec middleware CORS
    - 💾 Intégration PostgreSQL avec connexion poolée
    - 📚 Documentation interactive - Swagger UI et ReDoc intégrés
    - 🌐 CORS activé - Compatible avec les applications web frontend`
    - 🏠 Gestion des annonces immobilières avec recherche avancée
    - 📊 Statistiques détaillées - Analyses et métriques sur le parc immobilier
    - 🔍 Recherche multicritères: Filtres par prix, surface, localisation, type de bien
    - 🖼️ Données complètes - Accès aux annonces, images, caractéristiques, DPE, conseillers
    - 🔒 Gestion des erreurs - Retours d'erreur standardisés et informatifs
   


# 🛠Technologies utilisées 

    - FastAPI - Framework web moderne et rapide
    - PostgreSQL - Base de données relationnelle
    - JWT - Authentification par tokens
    - Python-jose - Gestion des tokens JWT
    - Psycopg2 - Connecteur PostgreSQL
    - Uvicorn - Serveur ASGI
    - Python-dotenv - Gestion des variables d'environnement

# 📥Installation

## Prérequis

    - Python 3.8+
    - PostgreSQL
    - uv (recommandé) ou pip

# Installation des dépendances

```bash
# Avec UV (recommandé)
uv sync

# installation manuelle des packages python 
uv pip install -r requirements.txt
# ou 
pip install -r requirements.txt
```

# ⚙️Configuration

## Tester la connexion avec la base de données Postgres SQL

- Préalable : encodage UTF-8
```bash
# Pour la console Windows, définir l'encodage UTF-8.
chcp 6500
# ou bien
$env:PGCLIENTENCODING = 'UTF-8'
```
```bash
# Acceder à la base de données PostgresSQQL imo_db (Windows, Linux)
psql -d imo_db -U postgres

```
 - Assurez-vous que votre base de données PostgreSQL contient les tables nécessaires :

    - annonces, caracteristiques, images, conseiller, dpe, copropriete
```bash
psql -d imo_db -U postgres
```
```bash
# Commandes PL/SQL
-- # Lister toutes les commandes
\d\?
-- # Lister toutes les tables de la base
\dt
-- # Voir toutes les tables avec leur schéma
\dt+
-- # Voir les séquences
\ds
-- # Voir les vues
\dv
-- # Voir les fonctions
\df
-- # Ou avec une requête SQL
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```


- Créez un fichier .env à la racine du projet :
```bash
# Sécurité JWT
JWT_SECRET_KEY=votre-super-secret-tres-long-et-securise-en-production
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Base de données
DB_HOST=localhost
IMO_DB=imo_db
IMO_USER=postgres
IMO_PASSWORD=votre-mot-de-passe
DB_PORT=5432

 ```


# 🎯Utilisation

```bash
# Méthode 1 - Directement avec Uvicorn
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Méthode 2 - Avec le script Python
python api.py

# Méthode 3 - Avec UV
uv run api.py
```
L'API sera accessible à : http://localhost:8000


# Documentation

    📖 Swagger UI : http://localhost:8000/docs
    📚 ReDoc : http://localhost:8000/redoc


# 📡Endpoints
![](/img/c5_api_1.png)
## 🏠 Annonces

| Méthode | Endpoint                      | Description |
|:--------|:------------------------------|:------------|
| GET     | /                             | Page d'accueil avec la liste des endpoints |
| GET     | /annonces                     | Liste paginée des annonces avec filtres |
| GET     | /annonces/{id}                | Détail complet d'une annonce |
| GET     | /annonces/reference/{reference} | Annonce par référence |
| GET     | /annonces/search              | Recherche par terme |

## 📊 Statistiques
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | /statistiques | Statistiques générales de la base |
| GET | /types-bien | Liste des types de biens disponibles |
| GET | /localisations | Liste des localisations disponibles |


| Méthode | Endpoint | Description |
|:--------|:---------|:------------|
| GET | /statistiques | Statistiques générales de la base |
| GET | /types-bien | Liste des types de biens disponibles |
| GET | /localisations | Liste des localisations disponibles |


## 📊Paramètres de recherche des annonces

    - skip : Nombre d'éléments à sauter (pagination)
    - limit : Nombre d'éléments à retourner (1-1000)
    - type_bien : Filtre par type de bien
    - min_prix / max_prix : Filtre par fourchette de prix
    - min_surface / max_surface : Filtre par surface
    - localisation : Recherche par localisation (recherche partielle)

# 🔑Authentification

## Obtenir un token
```bash
# Méthode avec curl
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"

# Méthode avec PowerShell
$token = (curl.exe -s -X POST http://localhost:8000/token -d "username=admin" -d "password=admin123" | ConvertFrom-Json).access_token
```

## Utiliser le token
```bash
# Méthode avec curl
curl -X GET "http://localhost:8000/annonces" \
     -H "Authorization: Bearer VOTRE_TOKEN_JWT"

# Méthode avec PowerShell
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/annonces?limit=2"
```


## 🔐 Exemples d'utilisation avec authentification


Récupérer des annonces avec filtres
### 🐧 Version PowerShell
```bash
# Obtenir le token
$token = (curl.exe -s -X POST "http://localhost:8000/token" -d "username=admin" -d "password=admin123" | ConvertFrom-Json).access_token

Write-Host "Token obtenu: $($token.Substring(0,50))..." -ForegroundColor Green

# 10 premières annonces
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/annonces?limit=10" | ConvertFrom-Json | Format-Table reference, titre, prix

# Appartements entre 100k€ et 300k€
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/annonces?type_bien=appartement&min_prix=100000&max_prix=300000" | ConvertFrom-Json | Format-Table reference, titre, prix, surface
```

### Version Linux
```bash
# Obtenir un token d'authentification
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"

# 10 premières annonces (avec token)
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces?limit=10"

# Appartements entre 100k€ et 300k€ (avec token)
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces?type_bien=appartement&min_prix=100000&max_prix=300000"

# Annonces à Paris avec au moins 50m² (avec token)
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces?localisation=paris&min_surface=50"

# Pagination (annonces 11 à 20) (avec token)
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces?skip=10&limit=10"

```

🔓 Version sans authentification (routes publiques limitées)
```bash
# Route publique (limité à 10 résultats, données réduites)
curl "http://localhost:8000/public/annonces?limit=5"
```

Note importante : Toutes les routes protégées (/annonces, /statistiques, etc.) nécessitent un token JWT valide obtenu via /token. Sans token, vous recevrez une erreur {"detail":"Not authenticated"}

## Recherche avancée
### 🐧 Version PowerShell
```bash

# Recherche plein texte
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/annonces/search?q=paris%20centre" | ConvertFrom-Json

# Détail par ID
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/annonces/90" | ConvertFrom-Json

# Détail par référence
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/annonces/reference/1825968" | ConvertFrom-Json

# Statistiques générales
$stats = curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/statistiques" | ConvertFrom-Json
Write-Host "📊 $($stats.total_annonces) annonces - Prix moyen: $($stats.prix_moyen)€"

# Types de biens
$types = curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/types-bien" | ConvertFrom-Json
$types | ForEach-Object { Write-Host "🏠 $($_.type_bien)" }

# Localisations
$localisations = curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/localisations" | ConvertFrom-Json
$localisations | Select-Object -First 10 | ForEach-Object { Write-Host "📍 $($_.localisation)" }

```

### Version Linux
```bash
# Recherche dans les titres, descriptions et localisations
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces/search?q=paris%20centre"

# Recherche d'appartements à Montpellier
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces/search?q=montpellier%20appartement"

# Détail d'une annonce par son ID
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces/123"

# Recherche d'une annonce par sa référence
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces/reference/ABC123"

# Exemple avec une référence réelle
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/annonces/reference/1825968"
```

## Obtenir des statistiques

```
# Tableau de bord complet avec indicateurs clés
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/statistiques"

# Liste de tous les types de biens disponibles dans la base
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/types-bien"

# Localisations les plus courantes (limité aux 50 premières)
curl -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
     "http://localhost:8000/localisations"
```


# 🛡️Sécurité
Mesures de sécurité implémentées

    - ✅ JWT avec expiration configurable
    - ✅ Hachage des mots de passe (SHA256 - à améliorer en production)
    - ✅ Vérification des permissions par endpoint
    - ✅ Middleware CORS configurable
    - ✅ Validation des entrées avec FastAPI
    - ✅ Gestion des erreurs sécurisée


# 📄Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

# 👥 Auteurs
@2025 Olivier LAVAUD