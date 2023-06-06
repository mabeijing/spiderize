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

    def insert_many(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database("tms_db")
        collection = database.get_collection("steam_spu")
        collection.insert_many(spu.dict(by_alias=True) for spu in market_spu_array)

    def update_item_set(self, market_spu_array: list[MarketSPU]):
        database = self.client.get_database("tms_db")
        collection = database.get_collection("steam_spu")
        for market_spu in market_spu_array:
            condition = {"name": market_spu.name, "asset_description.classid": market_spu.asset_description.classid}
            one = collection.find_one(condition)
            if one:
                logger.warning(one)
            else:
                logger.error(condition)
            result = collection.update_one(condition, {"$set": {"query_item.item_set": market_spu.query_item.item_set}})
            # if result.upserted_id is None:
            #     logger.warning(f"{condition} not found in mongo.")
            # else:
            #     logger.info(f"{condition} update {result.upserted_id} success")


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
            params = {"start": index, "count": count, "category_730_ItemSet[]": f"tag_{tag}"}
            params.update(query)
            markets_spu_array = self.gem_market_spu(params)
            if not markets_spu_array:
                break

            for markets_spu in markets_spu_array:
                if markets_spu.query_item.item_set is None:
                    markets_spu.query_item.item_set = tag
                else:
                    markets_spu.query_item.item_set += f" + {tag}"

            self.mongo.update_item_set(markets_spu_array)

    def gem_weapon_spu(self):
        query = {"appid": 730, "norender": 1, "category_730_Type[]": "tag_CSGO_Type_Pistol"}
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
            self.parser_market_spu(markets_spu, weapon=True, exterior=True)
            # self.query_item_set_by_type(query)
            self.mongo.insert_many(markets_spu)
            index += count




if __name__ == '__main__':
    tags = settings.get_resources_map("730_ItemSet.json")
    print(len(tags))
