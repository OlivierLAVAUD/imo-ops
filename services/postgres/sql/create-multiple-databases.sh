#!/bin/bash

set -e
set -u

function create_user_and_database() {
    local database=$1
    local user=$2
    local password=$3
    echo "Creating user and database '$database' for user '$user'"
    
    # Utiliser l'utilisateur postgres par défaut pour créer les autres utilisateurs
    psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
        CREATE USER $user WITH PASSWORD '$password';
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $user;
EOSQL
}

# Créer la base Airflow si spécifiée
if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Creating multiple databases..."
    IFS=',' read -ra databases <<< "$POSTGRES_MULTIPLE_DATABASES"
    IFS=',' read -ra users <<< "$POSTGRES_MULTIPLE_USERS"
    IFS=',' read -ra passwords <<< "$POSTGRES_MULTIPLE_USERS"
    
    for i in "${!databases[@]}"; do
        create_user_and_database "${databases[i]}" "${users[i]}" "${passwords[i]}"
    done
fi