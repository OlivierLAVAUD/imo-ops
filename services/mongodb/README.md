# Mongodb



# Pré-Requis
    - MongoDB          (https://www.mongodb.com/) 
    - MongoDB Compass  ( https://www.mongodb.com/products/tools/compass) 
    - MongoDB Shell     (https://www.mongodb.com/try/download/shell)
    - mongosh ( )    

# Installation 

```
docker-compose up -d mondodb
```


## mongosh
```bash
 npm install -g mongosh


```


# Utilisation

```bash
# Tester en local
 docker exec -it mongodb mongosh -u root -p

# Tester depuis l'hôte
docker exec -it mongodb mongosh -u admin -p password --authenticationDatabase admin

# Ou depuis l'extérieur
mongosh "mongodb://admin:password@localhost:27017/admin"


# import ds donnéees agregées
uv run .\import_mongodb_agrege.py
```