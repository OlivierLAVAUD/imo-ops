##  Configuration PostgreSQL - Projet Imo

Ce conteneur PostgreSQL fournit plusieurs bases de données pour l'écosystème du projet Databox :

    - imo_db - Base de données principale pour les données immobilières
    - airflow_db - Base de données pour Apache Airflow
    - grafana_db - Base de données pour les tableaux de bord Grafana


## 🚀 Démarrage Rapide
### Prérequis

    - Docker et Docker Compose
    - Variables d'environnement configurées dans .env


## Démarrage
```bash

## Démarrer seulement PostgreSQL
docker-compose up postgres

## Ou démarrer tous les services
docker-compose up
```


### 📁 Structure du Projet

```text
services/postgres/
├── Dockerfile                 ### Image PostgreSQL avec scripts SQL
├── docker-compose.yml         ### Configuration du service
├── config/
│   └── pg_hba.conf           ## Authentification client PostgreSQL
├── scripts/
│   └── configure_pg_hba.sh   ## Configuration accès réseau
└── sql/
    ├── 00_system_config.sql      ## Paramètres système & utilisateurs
    ├── 01_imo_db_complete.sql    ## Structure de la base principale
    ├── 02_airflow_db_complete.sql ## Base Airflow
    └── 03_grafana_db_complete.sql ## Base Grafana
```

## 🔧 Configuration
### Variables d'Environnement (.env)


#### Administration PostgreSQL
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

#### Bases de données applicatives
IMO_USER=imo_user
IMO_PASSWORD=password
IMO_DB=imo_db
IMO_URL=postgresql://imo_user:password@postgres:5432/imo_db

AIRFLOW_USER=airflow
AIRFLOW_PASSWORD=airflow
AIRFLOW_DB_NAME=airflow_db

GRAFANA_USER=grafana
GRAFANA_PASSWORD=grafana
GRAFANA_DB_NAME=grafana_db
```

### Accès Réseau

Le conteneur est configuré pour :

    - Écouter sur toutes les interfaces (0.0.0.0:5432)
    - Accepter les connexions des réseaux Docker (172.16.0.0/12, 192.168.0.0/16, 10.0.0.0/8)

    - Utiliser l'authentification par mot de passe MD5 ou TRUST (si dev) 


## 🔌 URLs de Connexion
Depuis Autres Services
```bash

## Connexion imo_db
IMO_URL=postgresql://imo_user:password@postgres:5432/imo_db

## Connexion airflow_db  
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow_db

## Connexion grafana_db
GRAFANA_DB_URL=postgresql://grafana:grafana@postgres:5432/grafana_db
```
Connexions Externes
```bash

## Utiliser le compte admin
psql -h localhost -U postgres -d imo_db

## Utiliser le compte applicatif (depuis le réseau Docker)
docker exec -it db_databox psql -U imo_user -d imo_db
```
## 🛠️ Administration
Commandes Courantes
```bash

## Se connecter à la base de données
docker exec -it db_databox psql -U postgres -d imo_db

## Lister les bases de données
docker exec -it db_databox psql -U postgres -c "\l"

## Lister les tables dans imo_db
docker exec -it db_databox psql -U imo_user -d imo_db -c "\dt"

## Vérifier la taille des bases
docker exec -it db_databox psql -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) as size FROM pg_database;"
```

## Sauvegarde & Restauration

```bash
### Sauvegarder imo_db
docker exec -it db_databox pg_dump -U postgres imo_db > imo_db_backup.sql

### Restaurer imo_db
docker exec -i db_databox psql -U postgres imo_db < imo_db_backup.sql
```
🔒 Notes de Sécurité

    - Les mots de passe sont définis dans le fichier .env
    - Accès réseau restreint aux sous-réseaux Docker
    - Chaque service utilise un utilisateur dédié
    - Utilisateur en lecture seule disponible pour les analyses

## 🐛 Dépannage
Problèmes Courants
```bash
Connexion refusée depuis l'hôte :
bash

## Utiliser l'utilisateur postgres pour les connexions externes
psql -h localhost -U postgres -d imo_db
```

L'utilisateur n'existe pas :

    Vérifier la création des utilisateurs dans 00_system_config.sql
    Vérifier l'ordre d'exécution des scripts

Base de données non trouvée :

    Vérifier que POSTGRES_DB n'est pas défini dans docker-compose (les bases sont créées via scripts)

## Logs & Débogage
```bash

## Voir les logs PostgreSQL
docker logs db_databox

## Vérifier le statut de santé
docker exec -it db_databox pg_isready -U postgres

## Tester les connexions utilisateur
docker exec -it db_databox psql -U imo_user -d imo_db -c "SELECT 1;"
```
## 📈 Monitoring

La base de données inclut :

    - Extension pg_stat_statements pour le monitoring des requêtes
    - Vues en lecture seule pour les tableaux de bord Grafana
    - Contrôles de santé via Docker Compose

## 🔄 Maintenance
- Tâches Régulières

    - Surveiller l'utilisation du disque
    - Vérifier les logs PostgreSQL
    - Mettre à jour les mots de passe dans .env si nécessaire
    - Sauvegarder les données critiques
    - Réinitialiser l'Environnement de Développement

## Réinitialisation complète
```bash
docker-compose down -v
docker-compose build postgres
docker-compose up postgres
```
#📝 Ordre d'Exécution des Scripts

    - 00_system_config.sql - Configuration système et création des utilisateurs
    - 01_imo_db_complete.sql - Création et configuration de la base principale
    - 02_airflow_db_complete.sql - Création de la base Airflow
    - 03_grafana_db_complete.sql - Création de la base Grafana
    - configure_pg_hba.sh - Configuration des accès réseau

