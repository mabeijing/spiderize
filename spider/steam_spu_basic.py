import time
from typing import Optional

import requests

from databases.mysql_utils import engine, SQLStatement


# engine.dispose()


def insert_spu_if_not_exist(data: dict) -> bool:
    market_hash_name: str = data["market_hash_name"]

    with engine.connect() as connection, connection.begin():
        cursor = connection.execute(SQLStatement.query_spu, [{"market_hash_name": market_hash_name}])
        result = cursor.fetchone()
        if not result:
            connection.execute(SQLStatement.insert_spu, [data])
            return True
        return False


def insert_spu_tag(class_id: int, tag_id: int):
    with engine.connect() as connection:
        connection.execute()


def craw_steam_store_cargo():
    url = "https://steamcommunity.com/market/search/render/"
    headers = {
        "accept-language": "zh-CN,zh"
    }
    paginate_params = {
        "query": "",
        "start": 0,
        "count": 10,
        "search_descriptions": 1,
        "sort_column": "name",
        "sort_dir": "asc",
        "appid": 730,
        "category_730_ItemSet[]": "any",
        "category_730_ProPlayer[]": "any",
        "category_730_StickerCapsule[]": "any",
        "category_730_TournamentTeam[]": "any",
        "category_730_Weapon[]": "any",
        "norender": 1
    }

    index: int = 18900
    count: int = 100
    while True:
        print(f"执行读取从第{index}开始的100条。。。")
        paginate_params["start"] = index
        paginate_params["count"] = count
        resp = requests.get(url, params=paginate_params, headers=headers)
        if resp.status_code != 200:
            time.sleep(300)
            continue

        results: dict = resp.json()
        cargo_array: list[Optional[dict]] = results["results"]
        if not cargo_array:
            break

        for cargo in cargo_array:
            parameter: dict = steam_spu_basic(cargo)
            insert_spu_if_not_exist(parameter)
        time.sleep(30)
        index += count


def steam_spu_basic(cargo: dict) -> dict:
    """
    从steam爬取商品分类信息，入库eoc_goods_spu
    """

    classid: int = cargo["asset_description"]["classid"]
    name: str = cargo["name"]
    name_color: str = cargo["asset_description"]["name_color"]
    market_name: str = cargo["asset_description"]["market_name"]
    market_hash_name: str = cargo["asset_description"]["market_hash_name"]
    icon_url: str = cargo["asset_description"]["icon_url"]
    # icon_url_large: str = cargo["asset_description"]["icon_url_large"]
    icon_url_large: str = ""
    # descriptions: str = json.dumps(cargo["asset_description"]["descriptions"], ensure_ascii=False)
    descriptions: str = ""
    _price: str = cargo["sell_price_text"][1:]  # like 1,265.00
    price: float = float(''.join(_price.split(',')))

    return {
        "classid": classid,
        "name": name,
        "name_color": name_color,
        "market_name": market_name,
        "market_hash_name": market_hash_name,
        "icon_url": icon_url,
        "icon_url_large": icon_url_large,
        "descriptions": descriptions,
        "price": price
    }


if __name__ == '__main__':
    craw_steam_store_cargo()
