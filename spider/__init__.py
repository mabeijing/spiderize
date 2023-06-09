import time
from typing import Optional, Any

import requests
from requests.exceptions import HTTPError

import settings
from settings import bind_tag
from spider.models import MarketSPU
from spider.mongo_db import MongoDB
from spider.parser_asset import parser_market_spu
from scaffold.break_point import Cursor

logger = settings.get_logger()


class Spider:

    def __init__(self, only_update: bool = True):
        self.session = requests.Session()
        self._init_session()
        self.mongo = MongoDB()
        self.counter: int = 0
        self.cursor: Cursor = Cursor()
        self.only_update: bool = only_update
        self.count: int = settings.COUNT

    @staticmethod
    def base_query(func: Any) -> dict:
        return {"appid": 730, "norender": 1, "sort_column": "name", "sort_dir": "asc", "category_730_Type[]": func.tag}

    @property
    def mongo_client(self):
        return self.mongo.client

    def _init_session(self):
        self.session.headers.update({"accept-language": "zh-CN,zh"})

    def get_steam_market_spu(self, params: dict) -> list[Optional[MarketSPU]]:
        response: requests.Response = self.session.get(settings.MARKET_URL, params=params, proxies=settings.PROXY_POOL)
        if response.status_code != 200:
            logger.warning(f"status_code =>{response.status_code}, wait {settings.DELAY_TIME}s and auto retry...")
            time.sleep(settings.DELAY_TIME)
            return self.get_steam_market_spu(params)
        try:
            results: list[Optional[dict]] = response.json()["results"]
            self.counter += 1
            logger.info(f"the {self.counter} requests success. length => {len(results)}")
            return [MarketSPU.validate(item) for item in results if item]
        except HTTPError:
            logger.error(f"resp.test = > {response.text}")
            time.sleep(settings.DELAY_TIME)
            return self.get_steam_market_spu(params)
        except Exception:
            logger.exception(f"异常终止")
            exit(500)

    # 收藏品 => 武器，武器箱，探员
    def update_spu_item_set(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_ItemSet.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.item_set.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前收藏品ItemSet => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.item_set.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.item_set.index
            while True:
                params = {"start": index, "count": self.count, "category_730_ItemSet[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"收藏品ItemSet：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.item_set.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.item_set = tag

                self.mongo.update_item_set(markets_spu_array)
                index += self.count

                # 更新游标
                point = self.cursor.current_point
                point.item_set.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.item_set.index = 0
                    self.cursor.save(point)
                    break

    # 锦标赛 => 武器，涂鸦, 印花, 武器箱
    def update_spu_tournament(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_Tournament.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.tournament.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前锦标赛Tournament => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.tournament.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.tournament.index
            while True:
                params = {"start": index, "count": self.count, "category_730_Tournament[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"锦标赛Tournament：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.tournament.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.tournament = tag

                self.mongo.update_tournament(markets_spu_array)
                index += self.count

                # 更新游标
                point = self.cursor.current_point
                point.tournament.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.tournament.index = 0
                    self.cursor.save(point)
                    break

    # 战队 => 武器，印花，涂鸦，布章
    def update_spu_tournament_team(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_TournamentTeam.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.tournament_team.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前战队TournamentTeam => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.tournament_team.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.tournament_team.index
            while True:
                params = {"start": index, "count": self.count, "category_730_TournamentTeam[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"战队TournamentTeam：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.tournament_team.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.tournament_team = tag

                self.mongo.update_tournament_team(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.tournament_team.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.tournament_team.index = 0
                    self.cursor.save(point)
                    break

    # 职业选手 => 武器，印花
    def update_spu_pro_player(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_ProPlayer.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.pro_player.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前职业选手ProPlayer => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.pro_player.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.pro_player.index
            while True:
                params = {"start": index, "count": self.count, "category_730_ProPlayer[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"职业选手ProPlayer：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.pro_player.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.pro_player = tag

                self.mongo.update_pro_player(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.pro_player.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.pro_player.index = 0
                    self.cursor.save(point)
                    break

    # 印花收藏品 => 印花
    def update_spu_sticker_capsule(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_StickerCapsule.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.sticker_capsule.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前印花收藏品StickerCapsule => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.sticker_capsule.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.sticker_capsule.index
            while True:
                params = {"start": index, "count": self.count, "category_730_StickerCapsule[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"印花收藏品StickerCapsule：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.sticker_capsule.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.sticker_capsule = tag

                self.mongo.update_sticker_capsule(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.sticker_capsule.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.sticker_capsule.index = 0
                    self.cursor.save(point)
                    break

    # 印花类型 => 印花
    def update_spu_sticker_category(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_StickerCategory.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.sticker_category.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前印花类型StickerCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.sticker_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.sticker_category.index
            while True:
                params = {"start": index, "count": self.count, "category_730_StickerCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"印花类型StickerCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.sticker_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.sticker_category = tag

                self.mongo.update_sticker_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.sticker_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.sticker_category.index = 0
                    self.cursor.save(point)
                    break

    # 涂鸦收藏品 => 涂鸦
    def update_spu_spray_capsule(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_StickerCategory.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.spray_capsule.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前涂鸦收藏品SprayCapsule => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.spray_capsule.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.spray_capsule.index
            while True:
                params = {"start": index, "count": self.count, "category_730_SprayCapsule[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"涂鸦收藏品SprayCapsule：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.spray_capsule.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.spray_capsule = tag

                self.mongo.update_spray_capsule(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.spray_capsule.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.spray_capsule.index = 0
                    self.cursor.save(point)
                    break

    # 涂鸦类型 => 涂鸦
    def update_spu_spray_category(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_StickerCategory.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.spray_category.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前涂鸦类型SprayCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.spray_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.spray_category.index
            while True:
                params = {"start": index, "count": self.count, "category_730_SprayCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"涂鸦类型SprayCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.spray_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.spray_category = tag

                self.mongo.update_spray_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.spray_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.spray_category.index = 0
                    self.cursor.save(point)
                    break

    # 涂鸦颜色 => 涂鸦
    def update_spu_spray_color_category(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_SprayColorCategory.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.spray_color_category.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前涂鸦颜色SprayColorCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.spray_color_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.spray_color_category.index
            while True:
                params = {"start": index, "count": self.count, "category_730_SprayColorCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"涂鸦颜色SprayColorCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.spray_color_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.spray_color_category = tag

                self.mongo.update_spray_color_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.spray_color_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.spray_color_category.index = 0
                    self.cursor.save(point)
                    break

    # 布章收藏品 => 布章
    def update_spu_patch_capsule(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_PatchCapsule.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.patch_capsule.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前布章收藏品PatchCapsule => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.patch_capsule.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.patch_capsule.index
            while True:
                params = {"start": index, "count": self.count, "category_730_PatchCapsule[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"布章收藏品PatchCapsule：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.patch_capsule.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.patch_capsule = tag

                self.mongo.update_patch_capsule(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.patch_capsule.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.patch_capsule.index = 0
                    self.cursor.save(point)
                    break

    # 布章类型 => 布章
    def update_spu_patch_category(self, query: dict):
        tags: list[str] = settings.get_sorted_resources("730_PatchCategory.json")
        try:
            tag_index: int = tags.index(self.cursor.current_point.patch_category.localized_key)
            logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
        except ValueError:
            tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前布章类型PatchCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.patch_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.patch_category.index
            while True:
                params = {"start": index, "count": self.count, "category_730_PatchCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"布章类型PatchCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.patch_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.patch_category = tag

                self.mongo.update_patch_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.patch_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.patch_category.index = 0
                    self.cursor.save(point)
                    break

    @bind_tag("CSGO_Type_Pistol")
    def gem_weapon_pistol_spu(self, only_update: bool = None):
        """
        手枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        query: dict = self.base_query(self.gem_weapon_pistol_spu)
        logger.info(f"query => {query}")

        self.counter = 0

        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_pistol.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_pistol.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_pistol_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                # 更新游标
                point = self.cursor.current_point
                point.csgo_type_pistol.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_pistol.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_pistol_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

        # 查询并更新职业选手
        self.update_spu_pro_player(query)

    @bind_tag("CSGO_Type_SMG")
    def gem_weapon_smg_spu(self, only_update: bool = None):
        """
        微型冲锋枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        query: dict = self.base_query(self.gem_weapon_smg_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_smg.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_smg.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_smg_spu.support_asset)
                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)
                index += self.count

                # 更新游标
                point = self.cursor.current_point
                point.csgo_type_smg.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_smg.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_smg_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

        # 查询并更新职业选手
        self.update_spu_pro_player(query)

    @bind_tag("CSGO_Type_Rifle")
    def gem_weapon_rifle_spu(self, only_update: bool = None):
        """
        步枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        query: dict = self.base_query(self.gem_weapon_rifle_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_rifle.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_rifle.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_rifle_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count

                # 更新游标
                point = self.cursor.current_point
                point.csgo_type_rifle.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_rifle.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_rifle_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

        # 查询并更新职业选手
        self.update_spu_pro_player(query)

    @bind_tag("CSGO_Type_SniperRifle")
    def gem_weapon_sniper_rifle_spu(self, only_update: bool = None):
        """
        狙击步枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        query: dict = self.base_query(self.gem_weapon_sniper_rifle_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_sniper_rifle.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_sniper_rifle.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_sniper_rifle_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_sniper_rifle.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_sniper_rifle.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_sniper_rifle_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

        # 查询并更新职业选手
        self.update_spu_pro_player(query)

    @bind_tag("CSGO_Type_Shotgun")
    def gem_weapon_shotgun_spu(self, only_update: bool = None):
        """
        霰弹枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        query: dict = self.base_query(self.gem_weapon_shotgun_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_shotgun.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_shotgun.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_shotgun_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_shotgun.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_shotgun.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_shotgun_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

        # 查询并更新职业选手
        self.update_spu_pro_player(query)

    @bind_tag("CSGO_Type_Machinegun")
    def gem_weapon_machinegun_spu(self, only_update: bool = None):
        """
        机枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        query: dict = self.base_query(self.gem_weapon_machinegun_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_machinegun.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_machinegun.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_machinegun_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_machinegun.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_machinegun.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_machinegun_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

        # 查询并更新职业选手
        self.update_spu_pro_player(query)

    @bind_tag("CSGO_Type_WeaponCase")
    def gem_weapon_case_spu(self, only_update: bool = None):
        """
        武器箱
         -可解析： 类型，品质，类别
         -需查询： 收藏品
        """
        query: dict = self.base_query(self.gem_weapon_case_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_weapon_case.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_weapon_case.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_case_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_weapon_case.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_weapon_case.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_case_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

    @bind_tag("Type_CustomPlayer")
    def gem_custom_player_spu(self, only_update: bool = None):
        """
        探员
         -可解析： 类型，品质，类别
         -需查询： 收藏品
        """
        query: dict = self.base_query(self.gem_custom_player_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_custom_player.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_custom_player.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_custom_player_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_custom_player.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_custom_player.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_custom_player_spu)

        # 查询并更新收藏品
        self.update_spu_item_set(query)

    @bind_tag("CSGO_Type_Knife")
    def gem_knife_spu(self, only_update: bool = None):
        """
        匕首
         - 可解析： 类型，品质，类别，武器名，外观
        """
        query: dict = self.base_query(self.gem_knife_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_knife.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_knife.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_knife_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_knife.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_knife.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_knife_spu)

    @bind_tag("CSGO_Tool_Sticker")
    def gem_sticker_spu(self, only_update: bool = None):
        """
        印花
         -可解析： 类型，品质，类别
         -需查询： 印花收藏品，印花类型，锦标赛，战队，职业选手
        """
        query: dict = self.base_query(self.gem_sticker_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_sticker.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_sticker.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_sticker_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_sticker.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_sticker.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_sticker_spu)

        # 更新印花收藏品
        self.update_spu_sticker_capsule(query)

        # 更新印花类型
        self.update_spu_sticker_category(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

        # 查询并更新职业选手
        self.update_spu_pro_player(query)

    @bind_tag("Type_Hands")
    def gem_hands_spu(self, only_update: bool = None):
        """
        手套
         - 可解析： 类型，品质，类别，外观
        """
        query: dict = self.base_query(self.gem_hands_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_hands.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_hands.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_hands_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_hands.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_hands.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_hands_spu)

    @bind_tag("CSGO_Type_Spray")
    def gem_spray_spu(self, only_update: bool = None):
        """
        涂鸦
         -可解析： 类型，品质，类别
         -需查询： 涂鸦收藏品，涂鸦类型，涂鸦颜色，锦标赛，战队
        """
        query: dict = self.base_query(self.gem_spray_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_spray.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_spray.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_spray_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_spray.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_spray.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_spray_spu)

        # 更新涂鸦收藏品
        self.update_spu_spray_capsule(query)

        # 更新涂鸦类型
        self.update_spu_spray_category(query)

        # 更新涂鸦颜色
        self.update_spu_spray_color_category(query)

        # 查询并更新锦标赛
        self.update_spu_tournament(query)

        # 查询并更新战队
        self.update_spu_tournament_team(query)

    @bind_tag("CSGO_Tool_Patch")
    def gem_patch_spu(self, only_update: bool = None):
        """
        布章
         -可解析： 类型，品质，类别
         -需查询： 布章收藏品，布章类型， 战队
        """
        query: dict = self.base_query(self.gem_patch_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_patch.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_patch.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_patch_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_patch.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_patch.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_patch_spu)

        # 更新布章收藏品
        self.update_spu_patch_capsule(query)

        # 更新布章类型
        self.update_spu_patch_category(query)

        # 更新战队
        self.update_spu_tournament_team(query)

    @bind_tag("CSGO_Type_MusicKit")
    def gem_music_kit_spu(self, only_update: bool = None):
        """
        音乐盒
         -可解析： 类型，品质，类别
        """
        query: dict = self.base_query(self.gem_music_kit_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_music_kit.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_music_kit.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_music_kit_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_music_kit.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_music_kit.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_music_kit_spu)

    @bind_tag("CSGO_Type_Collectible")
    def gem_collectible_spu(self, only_update: bool = None):
        """
        收藏品
         -可解析： 类型，品质，类别
        """
        query: dict = self.base_query(self.gem_collectible_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_collectible.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_collectible.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_collectible_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_collectible.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_collectible.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_collectible_spu)

    @bind_tag("CSGO_Tool_WeaponCase_KeyTag")
    def gem_weapon_case_key_spu(self, only_update: bool = None):
        """
        药匙
         -可解析： 类型，品质，类别
        """
        query: dict = self.base_query(self.gem_weapon_case_key_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_weapon_case_key.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_weapon_case_key.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_case_key_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_weapon_case_key.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_weapon_case_key.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_case_key_spu)

    @bind_tag("CSGO_Type_Ticket")
    def gem_weapon_ticket_spu(self, only_update: bool = None):
        """
        通行证
         -可解析： 类型，品质，类别
        """
        query: dict = self.base_query(self.gem_weapon_ticket_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_ticket.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_ticket.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_weapon_ticket_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_ticket.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_ticket.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_weapon_ticket_spu)

    @bind_tag("CSGO_Tool_GiftTag")
    def gem_gift_spu(self, only_update: bool = None):
        """
        礼物
         -可解析： 类型，品质，类别
        """
        query: dict = self.base_query(self.gem_gift_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_gift.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_gift.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_gift_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_gift.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_gift.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_gift_spu)

    @bind_tag("CSGO_Tool_Name_TagTag")
    def gem_name_tag_spu(self, only_update: bool = None):
        """
        标签
         -可解析： 类型，品质，类别
        """
        query: dict = self.base_query(self.gem_name_tag_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_name_tag.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_name_tag.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_name_tag_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_name_tag.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_name_tag.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_name_tag_spu)

    @bind_tag("CSGO_Type_Tool")
    def gem_tool_spu(self, only_update: bool = None):
        """
        工具
         -可解析： 类型，品质，类别
        """
        query: dict = self.base_query(self.gem_tool_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_tool.index
            while True:
                params = {"start": index, "count": self.count}
                params.update(query)
                markets_spu = self.get_steam_market_spu(params)
                if not markets_spu:
                    point = self.cursor.current_point
                    point.csgo_type_tool.index = 0
                    self.cursor.save(point)
                    break

                # 查询出数据库中没有的数据
                markets_spu_array: list[Optional[MarketSPU]] = self.mongo.filter_for_insert(markets_spu)
                if markets_spu_array:
                    # 解析属性
                    parser_market_spu(markets_spu_array, **self.gem_tool_spu.support_asset)

                    # 批量插入
                    self.mongo.insert_many(markets_spu_array)

                index += self.count
                point = self.cursor.current_point
                point.csgo_type_tool.index = index
                self.cursor.save(point)

                if len(markets_spu) < self.count:
                    point = self.cursor.current_point
                    point.csgo_type_tool.index = 0
                    self.cursor.save(point)
                    break

            # 检查是否插入了重复数据
            self.mongo.check_duplicate_hash_name(self.gem_tool_spu)


if __name__ == '__main__':
    spider = Spider()
    spider.gem_weapon_smg_spu()
    spider.gem_weapon_pistol_spu()
