import time
from typing import Optional, Any

import requests
from requests.exceptions import RequestException

import settings
from spider.models import MarketSPU
from spider.mongo_db import MongoDB
from spider.parser_asset import parser_market_spu
from spider.mapping import SUPPORT_ASSET_MAP
from scaffold.break_point import Cursor
from scaffold.update_basic_resources import init_basic_resources

logger = settings.get_logger()


def bind_tag(name: str):
    def inner(func):
        func.tag = f"tag_{name}"
        assets: dict = SUPPORT_ASSET_MAP.get(name, {'weapon': False, 'exterior': False})
        assets.update({"spu_type": name})
        func.support_asset = assets
        return func

    return inner


class Spider:

    def __init__(self, only_update: bool = True, ignore_breakpoint: bool = False):
        init_basic_resources()
        self.session = requests.Session()
        self.mongo = MongoDB()
        self.counter: int = 0
        self.cursor: Cursor = Cursor()
        self.only_update: bool = only_update
        self.ignore_breakpoint: bool = ignore_breakpoint
        self.count: int = settings.COUNT
        self._init_session()

    @staticmethod
    def base_query(func: Any) -> dict:
        return {"appid": 730, "norender": 1, "sort_column": "name", "sort_dir": "asc", "category_730_Type[]": func.tag}

    @property
    def mongo_client(self):
        return self.mongo.client

    def _init_session(self):
        self.session.headers.update({"accept-language": "zh-CN,zh"})

    def get_steam_market_spu(self, params: dict) -> list[Optional[MarketSPU]]:
        time.sleep(settings.REQUEST_INTERVAL)
        response: requests.Response = self.session.get(settings.MARKET_URL, params=params, proxies=settings.PROXY_POOL)
        if response.status_code != 200:
            logger.warning(f"status_code =>{response.status_code}, wait {settings.DELAY_TIME}s and auto retry...")
            time.sleep(settings.DELAY_TIME)
            return self.get_steam_market_spu(params)
        try:
            results: list[Optional[dict]] = response.json()["results"]
            total_count: int = response.json()['total_count']
            tag_name: str = params.get("category_730_Type[]", "")
            self.counter += 1
            logger.info(f"the {self.counter} requests success. {tag_name} => {total_count}")
            return [MarketSPU.validate(item) for item in results if item]
        except RequestException:
            logger.error(f"resp.test = > {response.text}")
            time.sleep(settings.DELAY_TIME)
            return self.get_steam_market_spu(params)
        except Exception:
            logger.exception(f"异常终止")
            exit(500)

    # 收藏品 => 武器，武器箱，探员
    def update_spu_item_set(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_ItemSet.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                func_point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(func_point.item_set.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前收藏品ItemSet => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).item_set.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).item_set.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_ItemSet[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"收藏品ItemSet：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).item_set.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.item_set = tag

                self.mongo.update_item_set(markets_spu_array)

                # 更新游标
                index += self.count
                point = self.cursor.current_point
                point.get_current_point_item(func_tag).item_set.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).item_set.index = 0
                    self.cursor.save(point)
                    break

    # 锦标赛 => 武器，涂鸦, 印花, 武器箱
    def update_spu_tournament(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_Tournament.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                func_point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(func_point.tournament.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前锦标赛Tournament => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).tournament.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).tournament.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_Tournament[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"锦标赛Tournament：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).tournament.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.tournament = tag

                self.mongo.update_tournament(markets_spu_array)

                # 更新游标
                index += self.count
                point = self.cursor.current_point
                point.get_current_point_item(func_tag).tournament.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).tournament.index = 0
                    self.cursor.save(point)
                    break

    # 战队 => 武器，印花，涂鸦，布章
    def update_spu_tournament_team(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_TournamentTeam.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.tournament_team.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前战队TournamentTeam => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).tournament_team.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).tournament_team.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_TournamentTeam[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"战队TournamentTeam：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).tournament_team.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.tournament_team = tag

                self.mongo.update_tournament_team(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).tournament_team.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).tournament_team.index = 0
                    self.cursor.save(point)
                    break

    # 职业选手 => 武器，印花
    def update_spu_pro_player(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_ProPlayer.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.pro_player.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前职业选手ProPlayer => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).pro_player.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).pro_player.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_ProPlayer[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"职业选手ProPlayer：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).pro_player.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.pro_player = tag

                self.mongo.update_pro_player(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).pro_player.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).pro_player.index = 0
                    self.cursor.save(point)
                    break

    # 印花收藏品 => 印花
    def update_spu_sticker_capsule(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_StickerCapsule.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.sticker_capsule.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前印花收藏品StickerCapsule => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).sticker_capsule.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).sticker_capsule.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_StickerCapsule[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"印花收藏品StickerCapsule：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).sticker_capsule.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.sticker_capsule = tag

                self.mongo.update_sticker_capsule(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).sticker_capsule.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).sticker_capsule.index = 0
                    self.cursor.save(point)
                    break

    # 印花类型 => 印花
    def update_spu_sticker_category(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_StickerCategory.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.sticker_category.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前印花类型StickerCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).sticker_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).sticker_category.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_StickerCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"印花类型StickerCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).sticker_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.sticker_category = tag

                self.mongo.update_sticker_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).sticker_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).sticker_category.index = 0
                    self.cursor.save(point)
                    break

    # 涂鸦收藏品 => 涂鸦
    def update_spu_spray_capsule(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_StickerCategory.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.spray_capsule.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前涂鸦收藏品SprayCapsule => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).spray_capsule.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).spray_capsule.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_SprayCapsule[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"涂鸦收藏品SprayCapsule：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).spray_capsule.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.spray_capsule = tag

                self.mongo.update_spray_capsule(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).spray_capsule.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).spray_capsule.index = 0
                    self.cursor.save(point)
                    break

    # 涂鸦类型 => 涂鸦
    def update_spu_spray_category(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_StickerCategory.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.spray_category.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前涂鸦类型SprayCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).sticker_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).spray_category.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_SprayCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"涂鸦类型SprayCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).spray_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.spray_category = tag

                self.mongo.update_spray_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).spray_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).spray_category.index = 0
                    self.cursor.save(point)
                    break

    # 涂鸦颜色 => 涂鸦
    def update_spu_spray_color_category(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_SprayColorCategory.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.spray_color_category.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前涂鸦颜色SprayColorCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).spray_color_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).spray_color_category.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_SprayColorCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"涂鸦颜色SprayColorCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).spray_color_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.spray_color_category = tag

                self.mongo.update_spray_color_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).spray_color_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).spray_color_category.index = 0
                    self.cursor.save(point)
                    break

    # 布章收藏品 => 布章
    def update_spu_patch_capsule(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_PatchCapsule.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.patch_capsule.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前布章收藏品PatchCapsule => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).patch_capsule.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).patch_capsule.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_PatchCapsule[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"布章收藏品PatchCapsule：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).patch_capsule.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.patch_capsule = tag

                self.mongo.update_patch_capsule(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).patch_capsule.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).patch_capsule.index = 0
                    self.cursor.save(point)
                    break

    # 布章类型 => 布章
    def update_spu_patch_category(self, query: dict, ignore_breakpoint: bool, func_tag: str):
        tags: list[str] = settings.get_sorted_resources("730_PatchCategory.json")

        if ignore_breakpoint:
            tag_index = 0
        else:
            try:
                point = self.cursor.current_point.get_current_point_item(func_tag)
                tag_index: int = tags.index(point.patch_category.localized_key)
                logger.info(f"断点执行,从第{tag_index}个，{tags[tag_index]}开始执行。")
            except ValueError:
                tag_index = 0

        total_tags = tags[tag_index:]
        for i, tag in enumerate(total_tags, start=1):
            logger.info(f"当前布章类型PatchCategory => tag_{tag}, 剩余：{len(total_tags) - i} 待更新。")
            # 更新游标
            point = self.cursor.current_point
            point.get_current_point_item(func_tag).patch_category.localized_key = tag
            self.cursor.save(point)

            index = self.cursor.current_point.get_current_point_item(func_tag).patch_category.index
            while True:
                self.counter = 0
                params = {"start": index, "count": self.count, "category_730_PatchCategory[]": f"tag_{tag}"}
                params.update(query)
                markets_spu_array = self.get_steam_market_spu(params)
                if not markets_spu_array:
                    logger.warning(f"布章类型PatchCategory：{tag} => 没有数据了。")
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).patch_category.index = 0
                    self.cursor.save(point)
                    break

                for markets_spu in markets_spu_array:
                    markets_spu.query_item.patch_category = tag

                self.mongo.update_patch_category(markets_spu_array)
                index += self.count

                point = self.cursor.current_point
                point.get_current_point_item(func_tag).patch_category.index = index
                self.cursor.save(point)

                if len(markets_spu_array) < self.count:
                    point = self.cursor.current_point
                    point.get_current_point_item(func_tag).patch_category.index = 0
                    self.cursor.save(point)
                    break

    @bind_tag("CSGO_Type_Pistol")
    def gem_weapon_pistol_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        手枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        point_tag_name = "csgo_type_pistol"
        query: dict = self.base_query(self.gem_weapon_pistol_spu)
        logger.info(f"query => {query}")

        self.counter = 0

        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_pistol.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        """
        执行前，获取到point.csgo_type_pistol.item_set
        """

        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

        # 查询并更新职业选手
        self.update_spu_pro_player(query, ignore_breakpoint, point_tag_name)

    @bind_tag("CSGO_Type_SMG")
    def gem_weapon_smg_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        微型冲锋枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        point_tag_name = "csgo_type_smg"
        query: dict = self.base_query(self.gem_weapon_smg_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_smg.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

        # 查询并更新职业选手
        self.update_spu_pro_player(query, ignore_breakpoint, point_tag_name)

    @bind_tag("CSGO_Type_Rifle")
    def gem_weapon_rifle_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        步枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        point_tag_name = "csgo_type_rifle"
        query: dict = self.base_query(self.gem_weapon_rifle_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_rifle.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

        # 查询并更新职业选手
        self.update_spu_pro_player(query, ignore_breakpoint, point_tag_name)

    @bind_tag("CSGO_Type_SniperRifle")
    def gem_weapon_sniper_rifle_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        狙击步枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        point_tag_name = "csgo_type_sniper_rifle"
        query: dict = self.base_query(self.gem_weapon_sniper_rifle_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_sniper_rifle.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

        # 查询并更新职业选手
        self.update_spu_pro_player(query, ignore_breakpoint, point_tag_name)

    @bind_tag("CSGO_Type_Shotgun")
    def gem_weapon_shotgun_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        霰弹枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        point_tag_name = "csgo_type_shotgun"
        query: dict = self.base_query(self.gem_weapon_shotgun_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_shotgun.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

        # 查询并更新职业选手
        self.update_spu_pro_player(query, ignore_breakpoint, point_tag_name)

    @bind_tag("CSGO_Type_Machinegun")
    def gem_weapon_machinegun_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        机枪
         -可解析： 类型，品质，类别，武器名，外观
         -需查询： 收藏品，锦标赛，战队，职业选手
        """
        point_tag_name = "csgo_type_machinegun"
        query: dict = self.base_query(self.gem_weapon_machinegun_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_machinegun.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

        # 查询并更新职业选手
        self.update_spu_pro_player(query, ignore_breakpoint, point_tag_name)

    @bind_tag("CSGO_Type_WeaponCase")
    def gem_weapon_case_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        武器箱
         -可解析： 类型，品质，类别
         -需查询： 收藏品
        """
        point_tag_name = "csgo_type_weapon_case"
        query: dict = self.base_query(self.gem_weapon_case_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_weapon_case.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

    @bind_tag("Type_CustomPlayer")
    def gem_custom_player_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        探员
         -可解析： 类型，品质，类别
         -需查询： 收藏品
        """
        point_tag_name = "csgo_type_custom_player"
        query: dict = self.base_query(self.gem_custom_player_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_custom_player.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 查询并更新收藏品
        self.update_spu_item_set(query, ignore_breakpoint, point_tag_name)

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
            logger.info(f"本次执行，从index={index}开始请求。")
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
    def gem_sticker_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        印花
         -可解析： 类型，品质，类别
         -需查询： 印花收藏品，印花类型，锦标赛，战队，职业选手
        """
        point_tag_name = "csgo_type_sticker"
        query: dict = self.base_query(self.gem_sticker_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_sticker.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 更新印花收藏品
        self.update_spu_sticker_capsule(query, ignore_breakpoint, point_tag_name)

        # 更新印花类型
        self.update_spu_sticker_category(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

        # 查询并更新职业选手
        self.update_spu_pro_player(query, ignore_breakpoint, point_tag_name)

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
            logger.info(f"本次执行，从index={index}开始请求。")
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
    def gem_spray_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        涂鸦
         -可解析： 类型，品质，类别
         -需查询： 涂鸦收藏品，涂鸦类型，涂鸦颜色，锦标赛，战队
        """
        point_tag_name = "csgo_type_spray"
        query: dict = self.base_query(self.gem_spray_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_spray.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 更新涂鸦收藏品
        self.update_spu_spray_capsule(query, ignore_breakpoint, point_tag_name)

        # 更新涂鸦类型
        self.update_spu_spray_category(query, ignore_breakpoint, point_tag_name)

        # 更新涂鸦颜色
        self.update_spu_spray_color_category(query, ignore_breakpoint, point_tag_name)

        # 查询并更新锦标赛
        self.update_spu_tournament(query, ignore_breakpoint, point_tag_name)

        # 查询并更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

    @bind_tag("CSGO_Tool_Patch")
    def gem_patch_spu(self, only_update: bool = None, ignore_breakpoint: bool = None):
        """
        布章
         -可解析： 类型，品质，类别
         -需查询： 布章收藏品，布章类型， 战队
        """
        point_tag_name = "csgo_type_patch"
        query: dict = self.base_query(self.gem_patch_spu)
        logger.info(f"query => {query}")

        self.counter = 0
        only_update: bool = only_update if only_update is not None else self.only_update
        if not only_update:
            index = self.cursor.current_point.csgo_type_patch.index
            logger.info(f"本次执行，从index={index}开始请求。")
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

        ignore_breakpoint: bool = ignore_breakpoint if ignore_breakpoint is not None else self.ignore_breakpoint

        # 更新布章收藏品
        self.update_spu_patch_capsule(query, ignore_breakpoint, point_tag_name)

        # 更新布章类型
        self.update_spu_patch_category(query, ignore_breakpoint, point_tag_name)

        # 更新战队
        self.update_spu_tournament_team(query, ignore_breakpoint, point_tag_name)

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
            logger.info(f"本次执行，从index={index}开始请求。")
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
            logger.info(f"本次执行，从index={index}开始请求。")
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
            logger.info(f"本次执行，从index={index}开始请求。")
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
            logger.info(f"本次执行，从index={index}开始请求。")
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
            logger.info(f"本次执行，从index={index}开始请求。")
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
            logger.info(f"本次执行，从index={index}开始请求。")
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
            logger.info(f"本次执行，从index={index}开始请求。")
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
