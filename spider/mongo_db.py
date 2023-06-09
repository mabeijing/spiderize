from typing import Optional, Any

import pymongo

import settings
from spider.models import MarketSPU

logger = settings.get_logger()


class MongoDB:
    # 字段是数组的 => tournament, pro_player, tournament_team, sticker_capsule, spray_capsule, patch_capsule
    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGO_URI, connect=False)

    def filter_for_insert(self, market_spu_array: list[MarketSPU]) -> list[MarketSPU]:
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        need_insert_spu_array: list[Optional[MarketSPU]] = []
        for market_spu in market_spu_array:
            one = collection.find_one({"hash_name": market_spu.hash_name})
            if not one:
                need_insert_spu_array.append(market_spu)
        if len(market_spu_array) != len(need_insert_spu_array):
            logger.info(f"查询到{len(market_spu_array)}条数据，有{len(need_insert_spu_array)}条数据需要插库。")
        return need_insert_spu_array

    def check_duplicate_hash_name(self, func: Any):
        db = self.client.get_database(settings.MONGO_DB)
        collection = db.get_collection(settings.MONGO_COLLECTION)
        pipeline = [
            {'$match': {'hash_name': {'$exists': True}}},
            {'$group': {'_id': "$hash_name", 'count': {'$sum': 1}}},
            {'$match': {'count': {"$gte": 2}}}
        ]
        cursor = collection.aggregate(pipeline)

        resp: list[Optional[dict]] = list(cursor)
        if resp:
            logger.warning(f"{func.tag} 存在重复数据 => {resp}")

    def insert_many(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        if market_spu_array:
            collection.insert_many(spu.dict(by_alias=True) for spu in market_spu_array)

    # 更新收藏品
    def update_item_set(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$set": {"query_item.item_set": market_spu.query_item.item_set}}

            result = collection.update_one(condition, updated)
            if not (result.acknowledged and result.modified_count == 1):
                logger.error(f"{condition} update $query_item.item_set failed.")

    # 更新锦标赛
    def update_tournament(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$addToSet": {"query_item.tournament": market_spu.query_item.tournament}}
            result = collection.update_one(condition, updated)
            if not result.acknowledged:
                logger.error(f"{condition} update $query_item.tournament failed.")

    # 更新战队
    def update_tournament_team(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$addToSet": {"query_item.tournament_team": market_spu.query_item.tournament_team}}
            result = collection.update_one(condition, updated)
            if not result.acknowledged:
                logger.error(f"{condition} update $query_item.tournament_team failed.")

    # 更新职业选手
    def update_pro_player(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$addToSet": {"query_item.pro_player": market_spu.query_item.pro_player}}
            result = collection.update_one(condition, updated)
            if not result.acknowledged:
                logger.error(f"{condition} update $query_item.pro_player failed.")

    # 更新印花收藏品
    def update_sticker_capsule(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$addToSet": {"query_item.sticker_capsule": market_spu.query_item.sticker_capsule}}
            result = collection.update_one(condition, updated)
            if not result.acknowledged:
                logger.error(f"{condition} update $query_item.sticker_capsule failed.")

    # 更新印花类型
    def update_sticker_category(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$set": {"query_item.sticker_category": market_spu.query_item.sticker_category}}

            result = collection.update_one(condition, updated)
            if not (result.acknowledged and result.modified_count == 1):
                logger.error(f"{condition} update $query_item.sticker_category failed.")

    # 更新涂鸦收藏品
    def update_spray_capsule(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$addToSet": {"query_item.spray_capsule": market_spu.query_item.spray_capsule}}
            result = collection.update_one(condition, updated)
            if not result.acknowledged:
                logger.error(f"{condition} update $query_item.spray_capsule failed.")

    # 更新涂鸦类型
    def update_spray_category(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$set": {"query_item.spray_category": market_spu.query_item.spray_category}}

            result = collection.update_one(condition, updated)
            if not (result.acknowledged and result.modified_count == 1):
                logger.error(f"{condition} update $query_item.spray_category failed.")

    # 更新涂鸦颜色
    def update_spray_color_category(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$set": {"query_item.spray_color_category": market_spu.query_item.spray_color_category}}

            result = collection.update_one(condition, updated)
            if not (result.acknowledged and result.modified_count == 1):
                logger.error(f"{condition} update $query_item.spray_color_category failed.")

    # 更新布章收藏品
    def update_patch_capsule(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$addToSet": {"query_item.patch_capsule": market_spu.query_item.patch_capsule}}
            result = collection.update_one(condition, updated)
            if not result.acknowledged:
                logger.error(f"{condition} update $query_item.patch_capsule failed.")

    # 更新布章类型
    def update_patch_category(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            updated = {"$set": {"query_item.patch_category": market_spu.query_item.patch_category}}

            result = collection.update_one(condition, updated)
            if not (result.acknowledged and result.modified_count == 1):
                logger.error(f"{condition} update $query_item.patch_category failed.")
