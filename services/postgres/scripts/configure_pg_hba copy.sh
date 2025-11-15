#!/bin/bash
set -e

echo "Configuring PostgreSQL access controls..."

# Wait for PostgreSQL to be ready
until pg_isready -U $POSTGRES_USER; do
  echo "Waiting for PostgreSQL to start..."
  sleep 2
done

# Use custom template if available
if [ -f /tmp/pg_hba.conf.template ]; then
    echo "Applying custom pg_hba.conf template..."
    cat /tmp/pg_hba.conf.template > /var/lib/postgresql/data/pg_hba.conf
    chmod 600 /var/lib/postgresql/data/pg_hba.conf
    chown postgres:postgres /var/lib/postgresql/data/pg_hba.conf
else
    echo "No custom template found, using default configuration with appended rules..."
    cat >> /var/lib/postgresql/data/pg_hba.conf << EOF

# Custom rules for Imo application
host    all             all             172.16.0.0/12           md5
host    all             all             192.168.0.0/16          md5
host    all             all             10.0.0.0/8              md5
host    imo_db          all             all                     md5
EOF
fi

# Reload configuration
echo "Reloading PostgreSQL configuration..."
psql -U $POSTGRES_USER -c "SELECT pg_reload_conf();"

echo "PostgreSQL access configuration completed successfully"