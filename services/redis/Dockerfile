FROM redis:7.2-alpine

# Installation des dépendances supplémentaires si nécessaire
RUN apk add --no-cache tzdata

# Copier la configuration Redis personnalisée
COPY redis.conf /usr/local/etc/redis/redis.conf

# Exposer le port Redis
EXPOSE 6379

# Démarrer Redis avec la configuration personnalisée
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]