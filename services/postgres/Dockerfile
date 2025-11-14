# Use the official PostgreSQL image
FROM postgres:13

# Create directory for SQL scripts
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy the SQL script into the container
COPY sql/databox.sql /docker-entrypoint-initdb.d/

# Expose the PostgreSQL port
EXPOSE 5432