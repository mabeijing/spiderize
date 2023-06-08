"""
断点记录器，用于记录脚本当前执行进度

1. 需要基础数据爬取器，先生成基础数据
2. 创建执行器的游标

"""
import json
from typing import Optional
from pydantic import BaseModel, fields

import settings


class PointItem(BaseModel):
    localized_key: str = fields.Field("")
    index: int = fields.Field(0)


class Point(BaseModel):
    exterior: PointItem = fields.Field(PointItem())

    item_set: PointItem = fields.Field(PointItem())
    tournament: PointItem = fields.Field(PointItem())
    tournament_team: PointItem = fields.Field(PointItem())
    pro_player: PointItem = fields.Field(PointItem())
    sticker_capsule: PointItem = fields.Field(PointItem())
    sticker_category: PointItem = fields.Field(PointItem())
    spray_capsule: PointItem = fields.Field(PointItem())
    spray_category: PointItem = fields.Field(PointItem())
    spray_color_category: PointItem = fields.Field(PointItem())
    patch_capsule: PointItem = fields.Field(PointItem())
    patch_category: PointItem = fields.Field(PointItem())

    csgo_type_pistol: PointItem = fields.Field(PointItem())
    csgo_type_smg: PointItem = fields.Field(PointItem())
    csgo_type_rifle: PointItem = fields.Field(PointItem())
    csgo_type_sniper_rifle: PointItem = fields.Field(PointItem())
    csgo_type_shotgun: PointItem = fields.Field(PointItem())
    csgo_type_machinegun: PointItem = fields.Field(PointItem())
    csgo_type_weapon_case: PointItem = fields.Field(PointItem())
    csgo_type_custom_player: PointItem = fields.Field(PointItem())
    csgo_type_knife: PointItem = fields.Field(PointItem())
    csgo_type_sticker: PointItem = fields.Field(PointItem())
    csgo_type_hands: PointItem = fields.Field(PointItem())
    csgo_type_spray: PointItem = fields.Field(PointItem())
    csgo_type_music_kit: PointItem = fields.Field(PointItem())
    csgo_type_patch: PointItem = fields.Field(PointItem())
    csgo_type_collectible: PointItem = fields.Field(PointItem())
    csgo_type_weapon_case_key: PointItem = fields.Field(PointItem())
    csgo_type_ticket: PointItem = fields.Field(PointItem())
    csgo_type_gift: PointItem = fields.Field(PointItem())
    csgo_type_name_tag: PointItem = fields.Field(PointItem())
    csgo_type_tool: PointItem = fields.Field(PointItem())


class Cursor:
    """
    1.spider运行前load()，解析。执行器根据这个，去找到上次的断点
    2.每次即将执行一个新的item。就更新point，并且save()。
    """

    def __init__(self):
        self.cache_file = settings.RESOURCES.joinpath('.cache')
        self.point = Point
        self._init_cache()

    def _init_cache(self):
        if not self.cache_file.exists():
            self.cache_file.touch()

    def save(self, point: Point):
        # 用于记录当前执行状态
        with open(self.cache_file, mode="w", encoding="utf-8") as f:
            f.write(json.dumps(point.dict(), ensure_ascii=False, indent=2))
            f.flush()

    def load(self) -> dict:
        with open(self.cache_file, mode="r", encoding="utf-8") as f:
            return json.load(f)

    @property
    def current_point(self) -> Point:
        cache_data: str = self.cache_file.read_bytes() if self.cache_file.read_bytes() else self.point().json()
        return self.point.validate(json.loads(cache_data))


if __name__ == '__main__':
    pass
