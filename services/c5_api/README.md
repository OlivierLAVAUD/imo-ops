# 🏠 API Immobilière - FastAPI

Une API RESTful complète pour consulter et rechercher des données immobilières à partir d'une base PostgreSQL.
📋 Fonctionnalités

    🔍 Recherche avancée - Filtres par prix, surface, localisation, type de bien
    📊 Statistiques détaillées - Analyses et métriques sur le parc immobilier
    🖼️ Données complètes - Accès aux annonces, images, caractéristiques, DPE, conseillers
    🔒 Gestion des erreurs - Retours d'erreur standardisés et informatifs
    📚 Documentation interactive - Swagger UI et ReDoc intégrés
    🌐 CORS activé - Compatible avec les applications web frontend`

```bash
# Structure
c5_api/
├── api.py              # Application FastAPI principale
├── run_api.py          # Script de lancement
├── requirements.txt    # Dépendances Python
├── .env               # Variables d'environnement
└── README.md          # Documentation
```



# 🚀 Installation
Prérequis

    Python 3.8+
    PostgreSQL
    UV (recommandé) ou pip

# Installation des dépendances

```bash
# Avec UV (recommandé)
uv sync

# Ou avec pip
pip install -r requirements.txt
```

# Configuration

1. Créez un fichier .env à la racine du projet :
```bash
    # Configuration Base de Données
    DB_HOST=localhost
    DB_PORT=5432
    POSTGRES_IMO_DB=imo_db
    POSTGRES_IMO_USER=postgres
    POSTGRES_IMO_PASSWORD=votre_mot_de_passe

    # Configuration API
    API_HOST=0.0.0.0
    API_PORT=8000
    API_RELOAD=True

 ```

 2. Assurez-vous que votre base de données PostgreSQL contient les tables nécessaires :

        annonces
        caracteristiques
        images
        conseiller
        dpe
        copropriete

# 🎯 Utilisation

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


# 📡 Endpoints API
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

## 🔍 Exemples d'utilisation
Récupérer des annonces avec filtres

```bash
# 10 premières annonces
curl "http://localhost:8000/annonces?limit=10"

# Appartements entre 100k€ et 300k€
curl "http://localhost:8000/annonces?type_bien=appartement&min_prix=100000&max_prix=300000"

# Annonces à Paris avec au moins 50m²
curl "http://localhost:8000/annonces?localisation=paris&min_surface=50"

# Pagination (annonces 11 à 20)
curl "http://localhost:8000/annonces?skip=10&limit=10"
```

## Recherche avancée

```bash
# Recherche plein texte
curl "http://localhost:8000/annonces/search?q=paris%20centre"

# Détail d'une annonce spécifique
curl "http://localhost:8000/annonces/123"

# Par référence
curl "http://localhost:8000/annonces/reference/ABC123"
```

## Obtenir des statistiques

```
# Statistiques générales
curl "http://localhost:8000/statistiques"

# Types de biens disponibles
curl "http://localhost:8000/types-bien"

# Localisations les plus courantes
curl "http://localhost:8000/localisations"
```

# 📄Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

# 👥 Auteurs
@2025 Olivier LAVAUD