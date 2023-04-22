import json
import re
import time

import urllib3.exceptions
import urllib.parse
import requests
from datetime import datetime, date

from spider.utils import handle_cargo_type, handler_weapon_asset
from databases.mysql_utils import engine, SQLStatement
from spider import type_mapping

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
g_rgAppContextData = re.compile(r".*var g_rgAppContextData = (.*);")
g_rgAssets = re.compile(r'.*var g_rgAssets = (.*);')
g_rgListingInfo = re.compile(r".*var g_rgListingInfo = (.*?});")
var_line1 = re.compile(r".*var line1.*(\[\[.*?]]);")


def insert_spu_tag_by_localized_name(spu_id: int, localized_name: str):
    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.query_tag_by_localized_name, [{"localized_name": localized_name}])
        result = cursor.fetchone()
        tag_id: int = int(result[0])
    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.query_spu_tag, [{"spu_id": spu_id, "tag_id": tag_id}])
        result = cursor.fetchone()
        if not result:
            connection.execute(SQLStatement.insert_spu_tag, [{"spu_id": spu_id, "tag_id": tag_id}])


def insert_spu_tag_by_name(spu_id: int, name: str):
    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.query_tag_by_name, [{"name": name}])
        result = cursor.fetchone()
        tag_id: int = int(result[0])
    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.query_spu_tag, [{"spu_id": spu_id, "tag_id": tag_id}])
        result = cursor.fetchone()
        if not result:
            connection.execute(SQLStatement.insert_spu_tag, [{"spu_id": spu_id, "tag_id": tag_id}])


def craw_steam_cargo_detail(spu_id: int, market_hash_name: str):
    """
    非常重要的功能，核心更新
    1. 通过hash_name,获取到detail，解析detail信息
    2. 获取到货物的属性。前提是必须有货物，
    3. 解析货物的属性，根据class_id添加到关联数据库
    4. 逐条读取，分次插入，效率非常低。但是很精准
    5. 能提供武器，分类，品质，稀有度，外观
    """
    parse_hash_name: str = urllib.parse.quote(market_hash_name)
    url = f"https://steamcommunity.com/market/listings/730/{parse_hash_name}"
    headers = {
        "accept-language": "zh-CN,zh"
    }
    r = requests.get(url, verify=False, headers=headers)
    assert r.status_code == 200
    crop_cargo_asset_info(spu_id, r.text)
    # crop_cargo_price_record(spu_id, r.text)


def crop_cargo_asset_info(spu_id: int, html_text: str):
    m = g_rgAssets.search(html_text)
    if not m:
        return
    raw: str = m.group(1)
    try:
        asset_info: dict = json.loads(raw)["730"]["2"]
        cargo_asset = list(asset_info.values())[0]
    except Exception:
        asset_info: list = json.loads(raw)["730"][0]
        cargo_asset = asset_info[0]

    # 更新description
    descriptions: str = json.dumps(cargo_asset["descriptions"], ensure_ascii=False)
    with engine.connect() as connection:
        connection.execute(SQLStatement.update_spu_desc, [{"descriptions": descriptions, "id": spu_id}])

    print(cargo_asset)
    # icon_url_large
    icon_url_large = cargo_asset.get("icon_url_large", "")
    with engine.connect() as connection:
        connection.execute(SQLStatement.update_spu_icon, [{"icon_url_large": icon_url_large, "id": spu_id}])

    cargo_type: str = cargo_asset["type"]
    market_name: str = cargo_asset["market_name"]

    quality, rarity, type_ = handle_cargo_type(cargo_type)
    print(quality, rarity, type_)
    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.query_tag)
        results: list[tuple] = cursor.fetchall()
        localized_name_array: list[str] = [str(item[0]) for item in results if item]

    if type_ not in localized_name_array:
        # 如果出现新的type，直接返回，等下次在执行检查
        return

    # 15,Type,类型
    insert_spu_tag_by_localized_name(spu_id, type_)  # 探员，印花，武器箱

    # 6,Quality,类别
    insert_spu_tag_by_localized_name(spu_id, quality)  # 工业级，大师
    rarity_map: dict = type_mapping.get_rarity_by_type(type_)
    rarity_name: str = rarity_map[rarity]
    # 7,Rarity,品质
    insert_spu_tag_by_name(spu_id, rarity_name)  # 纪念品，普通

    # 武器名， 外观
    if type_ in ("微型冲锋枪", "狙击步枪", "步枪", "霰弹枪", "手枪", "机枪", "匕首", "手套"):
        weapon_name, appearance = handler_weapon_asset(market_name)
        print(weapon_name, appearance)

        # 16,Weapon,武器
        insert_spu_tag_by_localized_name(spu_id, weapon_name)

        # 1,Exterior,外观
        insert_spu_tag_by_localized_name(spu_id, appearance)


def crop_cargo_price_record(spu_id: int, html_text: str):
    # 物品价格记录
    match = var_line1.search(html_text)
    price_trends = json.loads(match.group(1))
    for item in price_trends:
        date_time: date = datetime.strptime(item[0], '%b %d %Y %H: +0').date()
        price: float = round(float(item[1]), 2)
        number: int = int(item[2])
        item[0] = date_time
        item[1] = price
        item[2] = number

    print({spu_id: price_trends})


if __name__ == '__main__':
    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.query_spu_all)
        results: list[tuple[int, str]] = cursor.fetchall()

    for spu_id, market_hash_name in results:
        if spu_id >= 1499:
            print(spu_id, market_hash_name)
            craw_steam_cargo_detail(spu_id, market_hash_name)
            time.sleep(11)
