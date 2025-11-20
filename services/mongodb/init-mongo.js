db.createUser({
  user: "admin",
  pwd: "apassword,
  roles: [
    {
      role: "readWrite",
      db: "myapp"
    }
  ]
});

// Créer une collection de test
db.createCollection("imo_collection");