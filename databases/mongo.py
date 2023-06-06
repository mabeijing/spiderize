import pymongo


client = pymongo.MongoClient("mongodb://root:example@192.168.1.20:27017", minPoolSize=2)

# db = client["tms_db"]
db = client.get_database("tms_db")

# print(db)
collection = db.get_collection("steam_spu")
# collection = db.create_collection("steam_spu")
print(collection)

data = {}

r = collection.insert_one(data)

client.close()



