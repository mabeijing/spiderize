import time
from typing import Optional

import requests
from databases.mysql_utils import engine, SQLStatement


def read_item_type(facet_id: int) -> list[tuple[int, str]]:
    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.query_tag_type2, [{"facet_id": facet_id}])
        results: list[tuple[int, str]] = cursor.fetchall()
    return [(int(item[0]), f"tag_{item[1]}") for item in results if item]


def craw_steam_cargo_asset(tag_id: int, extra_param: dict):
    """
    1.这个函数主要解决 收藏品，战队，选手，印花收藏品，布章收藏品，布章类型，涂鸦收藏品，涂鸦类型，涂鸦颜色，印花类型，锦标赛，
    2.非常的多
    从tag读取一个类别下的每一个name，然后进行迭代

    收藏品:2
    布章收藏品：3
    布章类型：4
    选手：5
    涂鸦收藏品：8
    涂鸦类型：9
    涂鸦颜色：10
    印花收藏品：11
    印花类型：12
    锦标赛：13
    战队：14

    通过facet_id查询到对应类别，遍历查询，
    """
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
    paginate_params.update(extra_param)

    index: int = 0
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
        print(f"获取的cargo长度=> {len(cargo_array)}")
        if not cargo_array:
            time.sleep(15)
            break

        for cargo in cargo_array:
            market_hash_name: str = cargo["asset_description"]["market_hash_name"]
            with engine.connect() as connection:
                cursor = connection.execute(SQLStatement.query_spu_id, [{"market_hash_name": market_hash_name}])
                result = cursor.fetchone()
            if not result:
                print(f"{market_hash_name} 不在spu表中。跳过本次")
                continue
            spu_id: int = result[0]
            with engine.connect() as connection:
                cursor = connection.execute(SQLStatement.query_spu_tag, [{"spu_id": spu_id, "tag_id": tag_id}])
                result = cursor.fetchone()
                print(f"关联关系spu_tag，{result}")
                if not result:
                    connection.execute(SQLStatement.insert_spu_tag, [{"spu_id": spu_id, "tag_id": tag_id}])
        time.sleep(15)
        index += count


def run():
    # # 2,ItemSet,收藏品
    # asset_items = read_item_type(2)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_ItemSet[]": name}
    #     print(tag_id)
    #     craw_steam_cargo_asset(tag_id, extra)

    # # 3,PatchCapsule,布章收藏品
    # asset_items = read_item_type(3)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_PatchCapsule[]": name}
    #     print(tag_id)
    #     craw_steam_cargo_asset(tag_id, extra)

    # # 4,PatchCategory,布章类型
    # asset_items = read_item_type(4)
    # for tag_id, name in asset_items:
    #     print(tag_id)
    #     extra = {"category_730_PatchCategory[]": name}
    #     craw_steam_cargo_asset(tag_id, extra)

    # 5,ProPlayer,职业选手
    # asset_items = read_item_type(5)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_ProPlayer[]": name}
    #
    #     print(tag_id)
    #     if tag_id >= 220:
    #         craw_steam_cargo_asset(tag_id, extra)

    # # 8,SprayCapsule,涂鸦收藏品
    # asset_items = read_item_type(8)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_SprayCapsule[]": name}
    #     craw_steam_cargo_asset(tag_id, extra)
    #
    # # 9,SprayCategory,涂鸦类型
    # asset_items = read_item_type(9)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_SprayCategory[]": name}
    #     craw_steam_cargo_asset(tag_id, extra)

    # # 10,SprayColorCategory,涂鸦颜色
    # asset_items = read_item_type(10)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_SprayColorCategory[]": name}
    #     print(tag_id)
    #     craw_steam_cargo_asset(tag_id, extra)

    # # 11,StickerCapsule,印花收藏品
    # asset_items = read_item_type(11)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_StickerCapsule[]": name}
    #     print(tag_id)
    #     craw_steam_cargo_asset(tag_id, extra)

    # # 12,StickerCategory,印花类型
    # asset_items = read_item_type(12)
    # for tag_id, name in asset_items:
    #     extra = {"category_730_StickerCategory[]": name}
    #     print(tag_id)
    #     craw_steam_cargo_asset(tag_id, extra)
    #
    # # 13,Tournament,锦标赛
    # asset_items = read_item_type(13)
    # for tag_id, name in asset_items:
    #     print(tag_id)
    #     extra = {"category_730_Tournament[]": name}
    #     craw_steam_cargo_asset(tag_id, extra)

    # 14,TournamentTeam,战队
    asset_items = read_item_type(14)
    for tag_id, name in asset_items:
        extra = {"category_730_TournamentTeam[]": name}
        print(tag_id)
        craw_steam_cargo_asset(tag_id, extra)


if __name__ == '__main__':
    run()
