db.createUser({
  user: "app_user",
  pwd: "password_app",
  roles: [
    {
      role: "readWrite",
      db: "imo_db"
    }
  ]
});