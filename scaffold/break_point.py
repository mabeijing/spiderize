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

    csgo_type_pistol: PointItem = fields.Field(PointItem())


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
    cursor = Cursor()

    point = cursor.current_point
    point.item_set.localized_key = "asdc"
    cursor.save(point)

    print(cursor.current_point.dict())

    import re

    str1 = "export const allLocales_(en)"
    pattern = re.compile(r".*allLocales_\((.*)\)$")

    match = pattern.match(str1)
    print(match.regs[0])
    start, end = match.regs[0]
    print(str1[start: end])

    # def cut(r: re.Match):
    #     s, e = r.regs[0]
    #     prefix = str1[s, e]
    #     return str(r.regs)
    #
    #
    # s = re.sub(pattern, cut, str1)
    # print(s)
    # print(str1)
