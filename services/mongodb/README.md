# Mongodb



# Pré-Requis
    - MongoDB          (https://www.mongodb.com/) 
    - MongoDB Compass  ( https://www.mongodb.com/products/tools/compass) 
    - MongoDB Shell     (https://www.mongodb.com/try/download/shell)

# Installation 

## en local




## avec Docker


# Utilisation

```bash
docker exec -it mongodb mongosh

# Tester depuis l'hôte
docker exec -it mongodb mongosh -u admin -p password --authenticationDatabase admin

# Ou depuis l'extérieur
mongosh "mongodb://admin:password@localhost:27017/admin"

```