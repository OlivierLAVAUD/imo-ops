#!/bin/bash
set -e

# Attendre que PostgreSQL soit prêt
until pg_isready -h localhost -U admin; do
  sleep 1
done

# Ajouter une règle pour le réseau Docker dans pg_hba.conf
echo "host    all             all             172.19.0.0/16           md5" >> /var/lib/postgresql/data/pg_hba.conf

# Redémarrer PostgreSQL pour appliquer les modifications
pg_ctl restart