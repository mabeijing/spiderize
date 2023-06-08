"""
将mongo的数据，转化成mysql数据表的映射关系

1. 需要mysql的基础数据，查询出来。
2. 先将mongo的数据，读取出来，转成mysql需要的字段插入
3. 在根据hash_name，从mongo查询出spu的所有属性，在去mysql查询，有就不动，没有就新增，None的就删除
"""
import pymongo

mongo_uri = "mongodb://root:example@localhost:27017"

client = pymongo.MongoClient(mongo_uri, connect=False)


def batch_update_item_set():
    db = client.get_database("steam_db")
    collection = db.get_collection("steam_spu")
    collection.update_many({}, [{"$set": {"query_item.item_set": None}}])


def batch_update_tournament():
    db = client.get_database("steam_db")
    collection = db.get_collection("steam_spu")
    collection.update_many({}, [{"$set": {"query_item.tournament": None}}])


if __name__ == "__main__":
    # batch_update_item_set()
    batch_update_tournament()
