import re
import time
import requests
from typing import Optional

import settings
from settings import enums
from spider.models import MarketSPU
import pymongo

logger = settings.get_logger()

exterior_pattern: re.Pattern = re.compile(r".*\((.*)\).*")


class MongoDB:
    def __init__(self):
        self.client = pymongo.MongoClient(settings.MONGO_URI, connect=False)

    def filter_for_insert(self, market_spu_array: list[MarketSPU]) -> list[MarketSPU]:
        database = self.client.get_database("tms_db")
        collection = database.get_collection("steam_spu")
        collection.update_many({}, [])
        need_insert_spu_array: list[Optional[MarketSPU]] = []
        for market_spu in market_spu_array:
            one = collection.find_one({"hash_name": market_spu.hash_name})
            if not one:
                need_insert_spu_array.append(market_spu)
        logger.info(f"查询到{len(market_spu_array)}条数据，有{len(need_insert_spu_array)}条数据需要插库。")
        return need_insert_spu_array

    def insert_many(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database("tms_db")
        collection = database.get_collection("steam_spu")
        collection.insert_many(spu.dict(by_alias=True) for spu in market_spu_array)

    def update_item_set(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database("tms_db")
        collection = database.get_collection("steam_spu")
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            pipeline = [
                {
                    "$set": {
                        "query_item.item_set": {
                            "$cond": {
                                "if": {'$eq': ['$query_item.item_set', None]},
                                "then": market_spu.query_item.item_set,
                                "else": {"$concat": ['$query_item.item_set', ' - ', market_spu.query_item.item_set]}
                            }
                        }
                    }
                }
            ]
            result = collection.update_one(condition, pipeline)
            if result.acknowledged and result.modified_count == 1:
                logger.info(f"{condition} update $query_item.item_set success")
            else:
                logger.warning(f"{condition} not found in mongo.")

    def update_tournament(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            pipeline = [
                {
                    "$set": {
                        "query_item.tournament": {
                            "$cond": {
                                "if": {'$eq': ['$query_item.tournament', None]},
                                "then": market_spu.query_item.tournament,
                                "else": {"$concat": ['$query_item.tournament', ' - ', market_spu.query_item.tournament]}
                            }
                        }
                    }
                }
            ]
            result = collection.update_one(condition, pipeline)
            if not (result.acknowledged and result.modified_count == 1):
                logger.info(f"{condition} update $query_item.tournament failed.")

    def update_tournament_team(self, market_spu_array: list[MarketSPU]):
        # 战队
        database = self.client.get_database(settings.MONGO_DB)
        collection = database.get_collection(settings.MONGO_COLLECTION)
        for market_spu in market_spu_array:
            condition = {"hash_name": market_spu.hash_name}
            pipeline = [
                {
                    "$set": {
                        "query_item.tournament_team": {
                            "$cond": {
                                "if": {'$eq': ['$query_item.tournament_team', None]},
                                "then": market_spu.query_item.tournament_team,
                                "else": {"$concat": ['$query_item.tournament_team', ' - ',
                                                     market_spu.query_item.tournament_team]}
                            }
                        }
                    }
                }
            ]
            result = collection.update_one(condition, pipeline)
            if not (result.acknowledged and result.modified_count == 1):
                logger.info(f"{condition} update $query_item.tournament_team failed.")

    def check_duplicate_hash_name(self) -> bool:
        db = self.client.get_database("tms_db")
        collection = db.get_collection("steam_spu")
        pipeline = [
            {'$match': {'hash_name': {'$exists': True}}},
            {'$group': {'_id': "$hash_name", 'count': {'$sum': 1}}},
            {'$match': {'count': {"$gte": 2}}}
        ]
        cursor = collection.aggregate(pipeline)

        resp: list[Optional[dict]] = list(cursor)
        if resp:
            logger.warning(f"存在重复数据 => {resp}")
            return False
        return True


class Spider:

    def __init__(self):
        self.session = requests.Session()
        self._init_session()
        self.logger = settings.get_logger()
        self.mongo = MongoDB()
        self.result_collections: list[MarketSPU] = []
        self.counter: int = 0

    @property
    def mongo_client(self):
        return self.mongo.client

    def _init_session(self):
        self.session.headers.update({"accept-language": "zh-CN,zh"})

    def gem_market_spu(self, params: dict) -> list[Optional[MarketSPU]]:
        url = "https://steamcommunity.com/market/search/render"
        proxies = {'http': 'http://proxy.vmware.com:3128', 'https': 'http://proxy.vmware.com:3128'}

        response: requests.Response = self.session.get(url, params=params, proxies=proxies)
        if response.status_code != 200:
            self.logger.error(f"resp.status_code => {response.status_code}")
            time.sleep(300)
            return self.gem_market_spu(params)
        try:
            results: list[Optional[dict]] = response.json()["results"]
            self.counter += 1
            self.logger.info(f"the {self.counter} requests success.")
        except Exception:
            self.logger.error(f"resp.test = > {response.text}")
            time.sleep(300)
            return self.gem_market_spu(params)

        return [MarketSPU.validate(item) for item in results if item]

    def parser_market_spu(self, market_spu_array: list[MarketSPU], weapon: bool = False, exterior: bool = False):
        # 类别:Quality => 普通,纪念品,StatTrak™",★,★ StatTrak™", 都有，空表示普通
        # 品质:Rarity => 消费级，军规级，受限，工业级，普通级，保密，隐秘，高级，卓越。都有
        # 武器名:Weapon => P250...
        # 外观:Exterior => 久经沙场，崭新出厂
        # "type": "普通级 涂鸦",  => 类别 品质 类型
        # "market_name": "P2000 | 廉价皮革 (略有磨损)", => 武器名 外观
        for market_spu in market_spu_array:
            logger.debug(market_spu.dict(by_alias=True))
            asset_items: list[str] = market_spu.asset_description.asset_type.split(" ")
            if len(asset_items) == 2:  # Quality:普通
                market_spu.query_item.quality = enums.QualityItem.normal
                rarity = asset_items[0]
            elif len(asset_items) == 3:  # Quality:StatTrak™",★, 纪念品
                if asset_items[0] == "StatTrak™":
                    market_spu.query_item.quality = enums.QualityItem.strange
                elif asset_items[0] == "纪念品":
                    market_spu.query_item.quality = enums.QualityItem.tournament
                elif asset_items[0] == "★":
                    market_spu.query_item.quality = enums.QualityItem.unusual
                else:
                    logger.error(f"{asset_items} not parsed correct!")
                rarity = asset_items[1]

            else:  # Quality: ★ StatTrak™"
                market_spu.query_item.quality = enums.QualityItem.unusual_strange
                rarity = asset_items[2]

            market_spu.query_item.spu_type = enums.TypeItem.CSGO_Type_Pistol
            market_spu.query_item.rarity = rarity

            asset_items: list[str] = [item.strip() for item in market_spu.name.split("|")]
            if len(asset_items) > 2:
                logger.warning(f"weapon length more 2 part => {asset_items}")

            if weapon:
                weapon_name: str = asset_items[0]
                market_spu.query_item.weapon = weapon_name

            if exterior:
                asset_exterior = asset_items[1]
                match = exterior_pattern.match(asset_exterior)
                if match is None:
                    logger.error(f"weapon has no exterior => {asset_items}")
                else:
                    exterior = match.group(1)
                    market_spu.query_item.exterior = exterior

    def query_item_set_by_type(self, query: dict):
        # 相当漫长的过长
        # 收藏品 => 武器，武器箱，探员
        tags = settings.get_resources_map("730_ItemSet.json")  # 80次循环
        for tag in tags:
            logger.info(f"ItemSet => tag_{tag}")
            index = 0
            count = 100
            while True:
                params = {"start": index, "count": count, "category_730_ItemSet[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.gem_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"查询收藏品：{tag} => 没有数据了。")
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.item_set = tag

                self.mongo.update_item_set(markets_spu_array)
                index += count

                if len(markets_spu_array) < count:
                    break

    def query_tournament_by_type(self, query: dict):
        # 相当漫长的过长
        # 锦标赛 => 武器，涂鸦, 印花, 武器箱
        tags = settings.get_resources_map("730_Tournament.json")
        for tag in tags:
            logger.info(f"Tournament => tag_{tag}")
            index = 0
            count = 100
            while True:
                params = {"start": index, "count": count, "category_730_Tournament[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.gem_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"查询锦标赛：{tag} => 没有数据了。")
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.tournament = tag

                self.mongo.update_tournament(markets_spu_array)
                index += count

                if len(markets_spu_array) < count:
                    break

    def query_tournament_team_by_type(self, query: dict):
        # 战队 => 武器，印花，涂鸦，布章
        tags = settings.get_resources_map("730_TournamentTeam.json")
        for tag in tags:
            logger.info(f"TournamentTeam => tag_{tag}")
            index = 0
            count = 100
            while True:
                params = {"start": index, "count": count, "category_730_TournamentTeam[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.gem_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"查询战队：{tag} => 没有数据了。")
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.item_set = tag

                self.mongo.update_tournament_team(markets_spu_array)
                index += count

                if len(markets_spu_array) < count:
                    break

    def gem_weapon_spu(self):
        query = {"appid": 730, "norender": 1, "category_730_Type[]": "tag_CSGO_Type_Pistol", "sort_column": "name",
                 "sort_dir": "asc"}
        self.result_collections.clear()
        self.counter = 0
        # 查询条件必须包含匕首，手枪...
        # -可解析： 类型，品质，类别，武器名，外观
        # -需查询： 收藏品，锦标赛，战队，职业选手 最少查询6*5 = 30次大查询

        # 手枪先先查询一轮。获取所有手枪可解析属性
        # 再根据 收藏品，锦标赛，战队，职业选手 依次查询修改market_spu
        index = 0
        count = 100
        while True:
            params = {"start": index, "count": count}
            params.update(query)
            markets_spu = self.gem_market_spu(params)
            if not markets_spu:
                break

            # 查询出数据库中没有的数据
            markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)

            # 解析属性
            self.parser_market_spu(markets_spu_array, weapon=True, exterior=True)

            # 批量插入
            self.mongo.insert_many(markets_spu_array)
            index += count

        # 检查是否插入了重复数据
        if self.mongo.check_duplicate_hash_name() is False:
            logger.error(f"本次查询的：tag_CSGO_Type_Pistol 存在重复数据")

        # 查询并更新收藏品。前提是有数据
        self.query_item_set_by_type(query)

        # 查询并更新锦标赛
        self.query_tournament_by_type(query)

        # 查询并更新战队
        self.query_tournament_team_by_type(query)


if __name__ == '__main__':
    spider = Spider()
