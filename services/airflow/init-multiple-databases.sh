#!/bin/bash

set -u

function create_database_if_not_exists() {
    local database=$1
    echo "Vérification de la base de données '$database'"
    
    # Vérifier si la base existe déjà
    if psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$database"; then
        echo "✅ Base '$database' existe déjà"
    else
        echo "Création de la base '$database'"
        createdb -U "$POSTGRES_USER" "$database"
        if [ $? -eq 0 ]; then
            echo "✅ Base '$database' créée avec succès"
        else
            echo "❌ Erreur lors de la création de '$database'"
        fi
    fi
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Traitement des bases de données: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_database_if_not_exists "$db"
    done
    echo "Toutes les bases de données ont été traitées"
fi