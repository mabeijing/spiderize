"""

一些刷库脚本
"""

import pymongo

mongo_uri = "mongodb://root:example@localhost:27017"

client = pymongo.MongoClient(mongo_uri, connect=False)

mongo_db = "steam_db"
mongo_collection = "steam_spu"


def batch_update_item_set():
    db = client.get_database(mongo_db)
    collection = db.get_collection(mongo_collection)
    collection.update_many({}, [{"$set": {"query_item.item_set": None}}])


# tournament: list[Optional[str]] = fields.Field([])  # 锦标赛 多属性
# pro_player: list[Optional[str]] = fields.Field([])  # 职业选手 多属性
# tournament_team: list[Optional[str]] = fields.Field([])  # 战队 多属性

def batch_reset_tournament():
    db = client.get_database(mongo_db)
    collection = db.get_collection(mongo_collection)
    collection.update_many({}, [{"$set": {"query_item.tournament": []}}])


def batch_reset_tournament_team():
    db = client.get_database(mongo_db)
    collection = db.get_collection(mongo_collection)
    collection.update_many({}, [{"$set": {"query_item.tournament_team": []}}])


def batch_reset_pro_player():
    db = client.get_database(mongo_db)
    collection = db.get_collection(mongo_collection)
    collection.update_many({}, [{"$set": {"query_item.pro_player": []}}])


# set_community_27
def update_one():
    db = client.get_database(mongo_db)
    collection = db.get_collection(mongo_collection)
    one = collection.find(
        {"hash_name": "CZ75-Auto | Vendetta (Field-Tested)"}
    )
    collection.update_one(
        {"hash_name": "CZ75-Auto | Vendetta (Field-Tested)"},
        {"$set": {"query_item.item_set": 'set_community_27'}}
    )


if __name__ == "__main__":
    # batch_update_item_set()
    # batch_update_tournament()

    # 这3个属性，从str修改成list[str]
    # batch_reset_tournament()
    # batch_reset_tournament_team()
    # batch_reset_pro_player()
    update_one()