# Utilisation de l'image de base officielle Apache Airflow
FROM apache/airflow:2.10.5

# Définir le répertoire de travail
WORKDIR /opt/airflow

# Copier les fichiers nécessaires dans l'image Docker
COPY ./dags /opt/airflow/dags
COPY ./config /opt/airflow/config
COPY ./plugins /opt/airflow/plugins

# Définir une valeur par défaut pour la variable
ENV _PIP_ADDITIONAL_REQUIREMENTS=${_PIP_ADDITIONAL_REQUIREMENTS:-}

# Installation des dépendances supplémentaires si nécessaires
RUN if [ -n "${_PIP_ADDITIONAL_REQUIREMENTS}" ]; then pip install --no-cache-dir ${_PIP_ADDITIONAL_REQUIREMENTS}; fi

# Exposer le port pour le serveur web d'Airflow
EXPOSE 8080

# Commande par défaut pour démarrer Airflow
ENTRYPOINT ["bash", "/entrypoint"]
CMD ["airflow", "webserver"]