"""
将mongo的数据，转化成mysql数据表的映射关系

1. 需要mysql的基础数据，查询出来。
    先查询faect表，拿到16个属性大类

    在查询tag表，拿到大类对应的具体属性。这个属性要绑定到spu上
    实际绑定的时候，是绑定的spu_id和tag_id

2. 拆分成


先获取mongo的数据，根据hash_name查询是否在数据库中，
    如果在，删除spu_tag关联数据表，更新mongo中的表关系
    如果不在，直接更新mongo中的表关系


功能1. 初始化mysql
功能2. 更新goods_spu
功能3. 更新spu_tag关系

"""
import json
from typing import Optional
import pymongo
from sqlalchemy import URL
from sqlalchemy import create_engine
from sqlalchemy import text
import settings

from spider.models import MarketSPU

logger = settings.get_logger()


class SQLStatement:
    # 查询eoc_goods_tag
    query_goods_tag = text(
        'SELECT id, name from eoc_goods_tag;'
    )

    # 根据hash_name查询goods_spu
    query_goods_spu_by_hash_name = text(
        'SELECT id from eoc_goods_spu WHERE  market_hash_name = :market_hash_name;'
    )

    # 向eoc_goods_spu表插数据
    insert_goods_spu = text(
        "INSERT INTO eoc_goods_spu (classid, name, name_color, market_name, market_hash_name, icon_url, "
        "icon_url_large,descriptions, price) VALUES (:classid, :name, :name_color, :market_name, "
        ":market_hash_name, :icon_url, :icon_url_large, :descriptions,:price)"
    )

    # 删除eoc_goods_spu_tag
    delete_goods_spu_tag = text(
        'DELETE FROM eoc_goods_spu_tag WHERE spu_id = :spu_id;'
    )

    # 插入eoc_goods_spu_tag
    insert_goods_spu_tag = text(
        'INSERT INTO eoc_goods_spu_tag (spu_id, tag_id) VALUES (:spu_id, :tag_id);'
    )


class ConvertTools:

    def __init__(self, client: pymongo.MongoClient):
        self.engine = create_engine(
            URL.create(**settings.db_config("dev")),
            max_overflow=20, pool_size=5, pool_recycle=1800,
            isolation_level="AUTOCOMMIT"
        )
        self.client = client

        self.tag_map: dict[str, int] = self._init_eoc_goods_tag()

    def _init_eoc_goods_tag(self) -> dict[str, int]:
        # 获取一次，避免交互数据库
        with self.engine.connect() as connect:
            cursor = connect.execute(SQLStatement.query_goods_tag)
            tag_map: dict = {_tag: _id for (_id, _tag) in cursor.fetchall()}
            return tag_map

    def update_goods_spu(self):
        # 将数据，更新或者插入到mysql
        db = self.client.get_database(settings.MONGO_DB)
        collection = db.get_collection(settings.MONGO_COLLECTION)
        cursor = collection.find()
        for data in cursor:
            spu = MarketSPU.validate(data)
            print(spu.name)
            goods_spu_id: int = self._insert_to_goods_spu(spu)
            print(goods_spu_id)
            # 删除spu_tag绑定关系
            self._delete_goods_spu_tag(goods_spu_id)
            # 创建新的spu_tag关系
            condition: list[dict] = self._generate_condition(goods_spu_id, spu)
            self._batch_create_relationship_spu_tag(condition)
            return

    def _insert_to_goods_spu(self, spu: MarketSPU) -> int:
        # 如果spu不在goods_spu表中，插入返回id，如果存在，直接返回id
        with self.engine.connect() as connect:
            condition = [{"market_hash_name": spu.hash_name}]
            cursor = connect.execute(SQLStatement.query_goods_spu_by_hash_name, condition)
            data: Optional[tuple] = cursor.fetchone()
            if data:
                logger.debug(f"goods_spu表中已存在 {spu.hash_name}, id为{data}")
                return data[0]

            # 如果mysql中不存在，则直接新增
            condition = [{
                "classid": int(spu.asset_description.classid),
                "name": spu.name,
                "name_color": spu.asset_description.name_color,
                "market_name": spu.name,
                "market_hash_name": spu.hash_name,
                "icon_url": spu.asset_description.icon_url,
                "icon_url_large": spu.asset_description.icon_url_large,
                "descriptions": json.dumps(spu.descriptions, ensure_ascii=False),
                "price": float(spu.sell_price_text[1:])  # 删除$符号
            }]
            connect.execute(SQLStatement.insert_goods_spu, condition)

            # 再次查询返回id
            condition = [{"market_hash_name": spu.hash_name}]
            cursor = connect.execute(SQLStatement.query_goods_spu_by_hash_name, condition)
            data: Optional[tuple] = cursor.fetchone()
            return data[0]

    def _delete_goods_spu_tag(self, goods_spu_id: int):
        with self.engine.connect() as connect:
            condition = [{"spu_id": goods_spu_id}]
            connect.execute(SQLStatement.delete_goods_spu_tag, condition)

    def _generate_condition(self, good_spu_id: int, spu: MarketSPU) -> list[dict]:
        condition: list[dict] = []

        if spu.query_item.rarity:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.rarity)})
        if spu.query_item.quality:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.quality)})
        if spu.query_item.weapon:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.weapon)})
        if spu.query_item.exterior:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.exterior)})
        if spu.query_item.item_set:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.item_set)})
        if spu.query_item.sticker_category:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.sticker_category)})
        if spu.query_item.spray_category:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.spray_category)})
        if spu.query_item.spray_color_category:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.spray_color_category)})
        if spu.query_item.patch_category:
            condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(spu.query_item.patch_category)})

        if spu.query_item.tournament:
            for item in spu.query_item.tournament:
                condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(item)})
        if spu.query_item.pro_player:
            for item in spu.query_item.pro_player:
                condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(item)})
        if spu.query_item.tournament_team:
            for item in spu.query_item.tournament_team:
                condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(item)})
        if spu.query_item.sticker_capsule:
            for item in spu.query_item.sticker_capsule:
                condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(item)})
        if spu.query_item.spray_capsule:
            for item in spu.query_item.spray_capsule:
                condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(item)})
        if spu.query_item.patch_capsule:
            for item in spu.query_item.patch_capsule:
                condition.append({"spu_id": good_spu_id, "tag_id": self.tag_map.get(item)})

        return condition

    def _batch_create_relationship_spu_tag(self, condition: list[dict]):
        with self.engine.connect() as connect:
            connect.execute(SQLStatement.insert_goods_spu_tag, condition)


if __name__ == '__main__':
    c = pymongo.MongoClient(settings.MONGO_URI, connect=False)
    convert = ConvertTools(c)
    print(convert.tag_map)
    convert.update_goods_spu()
