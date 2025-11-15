from pymongo import MongoClient

try:
    client = MongoClient("mongodb://localhost:27017/")
    client.admin.command('ping')
    dbs = client.list_database_names()
    print(f"✅ Connecté! Bases: {dbs}")
    client.close()
except Exception as e:
    print(f"❌ Erreur: {e}")