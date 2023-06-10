"""

一些刷库脚本
"""

import pymongo
from bson.regex import Regex

from spider.mapping import WEAPON_NAME_MAP
from spider.models import MarketSPU

mongo_uri = "mongodb://root:example@43.155.102.212:27017"

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


def update_weapon_map_scripts():
    # 武器，匕首，手套
    db = client.get_database(mongo_db)
    collection = db.get_collection(mongo_collection)

    cursor = collection.find(
        {
            "query_item.type": "CSGO_Type_Knife",
            "query_item.weapon": {"$regex": Regex("（纪念品）|（StatTrak™）|（★）|（★ StatTrak™）")}
        }
    )

    market_spu_array: list[MarketSPU] = [MarketSPU.validate(item) for item in list(cursor)]

    count = len(market_spu_array)
    print(count)
    for index, market_spu in enumerate(market_spu_array, start=1):
        print(f"剩余{count - index} 个...")
        new_name = market_spu.query_item.weapon.split('（')[0].strip()
        name_tag = WEAPON_NAME_MAP.get(new_name)
        query = {"hash_name": market_spu.hash_name}
        updated = {
            "$set": {"query_item.weapon": name_tag}
        }
        collection.update_one(query, updated)


if __name__ == "__main__":
    # batch_update_item_set()
    # batch_update_tournament()

    # 这3个属性，从str修改成list[str]
    # batch_reset_tournament()
    # batch_reset_tournament_team()
    # batch_reset_pro_player()
    update_weapon_map_scripts()
