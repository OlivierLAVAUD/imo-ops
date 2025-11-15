FROM postgres:13

# Create directory for SQL scripts
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy configuration template
COPY config/pg_hba.conf /tmp/pg_hba.conf.template

# Copy configuration script
COPY scripts/configure_pg_hba.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/configure_pg_hba.sh

# Copy all SQL scripts into the container
COPY sql/*.sql /docker-entrypoint-initdb.d/

EXPOSE 5432