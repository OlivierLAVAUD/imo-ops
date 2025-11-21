# Mongodb



# Pré-Requis
    - MongoDB          (https://www.mongodb.com/) 
    - MongoDB Compass  ( https://www.mongodb.com/products/tools/compass) 
    - MongoDB Shell     (https://www.mongodb.com/try/download/shell)
    - mongosh ( )    

# Installation 


## avec Docker
```bash
# Démarrer MongoDB
docker-compose up -d mongodb

# Vérifier que MongoDB est healthy
docker-compose ps

# Lancer l'import
docker-compose --profile import up data-importer

# Charger un fichier specifique 
docker exec -i mongodb mongosh -u admin -p password --authenticationDatabase admin --eval "
use imo_agrege
db.annonces.drop()
db.annonces.insertMany(JSON.parse(cat('/data/imports/annonces_agregees.json')))
"

```

## Tester la connexion depuis l'extérieur
docker exec -it mongodb mongosh -u admin -p password --authenticationDatabase admin

## Dans mongosh,
```bash
use imo_agrege
db.runCommand({ping: 1})

# // Se connecter à votre base de données
use imo_agrege

#  // Lister toutes les collections
show collections

#  // Compter le nombre d'annonces
db.annonces.countDocuments()

#  // Afficher les premières annonces (formaté)
db.annonces.find().limit(5).pretty()

# // Afficher les statistiques de la collection
db.annonces.stats()

# // Afficher un échantillon d'annonces
db.annonces.aggregate([{ $sample: { size: 3 } }]).pretty() // Se connecter à votre base de données
use imo_agrege

# // Lister toutes les collections
show collections

# // Compter le nombre d'annonces
db.annonces.countDocuments()

# // Afficher les premières annonces (formaté)
db.annonces.find().limit(5).pretty()

# // Afficher les statistiques de la collection
db.annonces.stats()

# // Afficher un échantillon d'annonces
db.annonces.aggregate([{ $sample: { size: 3 } }]).pretty()
```

## en local

## installer mongosh
```bash
 npm install -g mongosh
```


# Utilisation

```bash
# Tester en local
 docker exec -it mongodb mongosh -u admin -p

# Tester depuis l'hôte
docker exec -it mongodb mongosh -u admin -p password --authenticationDatabase admin

# Ou depuis l'extérieur
mongosh "mongodb://admin:password@localhost:27017/admin"


# import ds donnéees agregées
uv run .\import_mongodb_agrege.py
```



