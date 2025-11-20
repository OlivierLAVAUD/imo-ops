# 


# Utilisation
```bash
# Démarrer Spark
docker-compose --profile spark up -d

# Supprimer Spark
docker-compose --profile spark down -v --rmi all
```



# Vérifier que tout fonctionne
 Ouvrir http://localhost:8080

```bash
# Tester un job
docker-compose exec spark-submit /opt/scripts/submit-job.sh /opt/scripts/wordcount.py

```