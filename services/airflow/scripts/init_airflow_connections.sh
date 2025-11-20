#!/bin/bash
# Script d'initialisation des connexions Airflow pour IMO-OPS

set -e

echo "🔗 ==========================================="
echo "🔗 INITIALISATION DES CONNEXIONS AIRFLOW"
echo "🔗 ==========================================="

# Attendre que la base Airflow soit vraiment prête
echo "⏳ Attente de la base Airflow..."
max_retries=30
retry_count=0

until airflow db check >/dev/null 2>&1; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -gt $max_retries ]; then
        echo "❌ Timeout: La base Airflow n'est pas prête après $max_retries tentatives"
        exit 1
    fi
    echo "   📋 Tentative $retry_count/$max_retries - En attente de la base Airflow..."
    sleep 5
done

echo "✅ Base Airflow prête après $retry_count tentatives"

# Attendre que PostgreSQL IMO_DB soit prêt
echo "⏳ Attente de la base IMO_DB..."
until PGPASSWORD=password psql -h postgres -U imo_user -d imo_db -c "SELECT 1;" >/dev/null 2>&1; do
    echo "   🗄️  En attente de IMO_DB..."
    sleep 3
done
echo "✅ Base IMO_DB prête"

# Fonction pour créer une connexion
create_connection() {
    local conn_id=$1
    local conn_type=$2
    local host=$3
    local schema=$4
    local login=$5
    local password=$6
    local port=$7
    local extra=$8

    echo "🔄 Configuration de la connexion $conn_id..."

    # Supprimer la connexion si elle existe
    if airflow connections get "$conn_id" >/dev/null 2>&1; then
        echo "   ♻️  Connexion existante - suppression..."
        airflow connections delete "$conn_id" >/dev/null 2>&1 || true
    fi

    # Créer la nouvelle connexion
    if [ -n "$extra" ]; then
        airflow connections add "$conn_id" \
            --conn-type "$conn_type" \
            --conn-host "$host" \
            --conn-schema "$schema" \
            --conn-login "$login" \
            --conn-password "$password" \
            --conn-port "$port" \
            --conn-extra "$extra"
    else
        airflow connections add "$conn_id" \
            --conn-type "$conn_type" \
            --conn-host "$host" \
            --conn-schema "$schema" \
            --conn-login "$login" \
            --conn-password "$password" \
            --conn-port "$port"
    fi

    echo "   ✅ Connexion $conn_id configurée"
}

# Connexion IMO_DB
create_connection \
    "imo_db" \
    "postgres" \
    "postgres" \
    "imo_db" \
    "imo_user" \
    "password" \
    "5432" \
    '{"sslmode": "prefer", "connect_timeout": 10}'

# Connexion Redis
create_connection \
    "redis_default" \
    "redis" \
    "redis" \
    "" \
    "" \
    "" \
    "6379" \
    '{"db": 0, "socket_connect_timeout": 5}'

# Connexion PostgreSQL Airflow
create_connection \
    "postgres_default" \
    "postgres" \
    "postgres" \
    "airflow" \
    "airflow" \
    "airflow" \
    "5432" \
    '{"sslmode": "prefer"}'

# Test des connexions
echo ""
echo "🧪 ==========================================="
echo "🧪 TEST DES CONNEXIONS"
echo "🧪 ==========================================="

test_connection() {
    local conn_id=$1
    echo "🔍 Test connexion $conn_id..."
    
    if airflow connections test "$conn_id" >/dev/null 2>&1; then
        echo "   ✅ Connexion $conn_id testée avec succès"
        return 0
    else
        echo "   ❌ Échec test connexion $conn_id"
        return 1
    fi
}

# Tests avec gestion d'erreur différenciée
if test_connection "imo_db"; then
    echo "   🎯 IMO_DB: Opérationnelle"
else
    echo "   💥 IMO_DB: Échec critique"
    exit 1
fi

if test_connection "postgres_default"; then
    echo "   🎯 PostgreSQL Airflow: Opérationnelle"
else
    echo "   💥 PostgreSQL Airflow: Échec critique"
    exit 1
fi

if test_connection "redis_default"; then
    echo "   🎯 Redis: Opérationnelle"
else
    echo "   ⚠️  Redis: Non disponible (peut être normal au premier démarrage)"
    # Ne pas quitter en erreur pour Redis
fi

# Affichage final
echo ""
echo "🎯 ==========================================="
echo "🎯 CONNEXIONS INITIALISÉES AVEC SUCCÈS"
echo "🎯 ==========================================="
echo ""
echo "📋 Liste des connexions disponibles:"
airflow connections list --output table

echo ""
echo "🔗 Connexions prêtes à l'emploi:"
echo "   • imo_db (PostgreSQL IMO)"
echo "   • redis_default (Redis)"
echo "   • postgres_default (PostgreSQL Airflow)"

exit 0