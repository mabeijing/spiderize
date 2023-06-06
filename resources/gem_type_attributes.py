"""
该模块，主要用于生成type_attributes.json

1. 需要获取物品种类，和属性种类。和当前对比。
    一共有物品20种， 一共有属性16种。 需要确认每个物品有多少种属性。

2. 属性16种：按照物品所有分类
    2.1 类型，品质，类别，武器名，外观 这5个是可以解析出来的。 => all
        武器名 => 武器 + 匕首
        外观 => 武器 + 匕首 + 手套
    2.2 收藏品 => 武器 + 印花 + 探员
        待确认 布章，涂鸦，手套，匕首是否支持该属性
    2.3 锦标赛 => 武器，印花， 武器箱， 涂鸦
        待确认 布章，涂鸦，手套，匕首是否支持该属性
    2.4 战队 => 武器，印花，布章
        待确认 布章，涂鸦，手套，匕首是否支持该属性
    2.5 职业选手 => 武器，印花
        待确认 布章，涂鸦，手套，匕首是否支持该属性
    2.6 剩余7个 印花收藏品，布章收藏品，涂鸦收藏品，布章类型，涂鸦类型，印花类型，涂鸦颜色 都是特定的


3. 种类20，按照属性分类：
    3.1 武器类(6) => [类型，品质，类别，武器名，外观，收藏品，锦标赛，战队，职业选手] 9个
        -可解析： 类型，品质，类别，武器名，外观
        -需查询： 收藏品，锦标赛，战队，职业选手 最少查询6*5 = 30次大查询

    3.2 匕首  => [类型，品质，类别，武器名，外观] 5个 最少查询1次大查询
        - 可解析： 类型，品质，类别，武器名，外观

    3.3 手套  => [类型，品质，类别，外观]] 4个 最少查询1次大查询
        - 可解析： 类型，品质，类别，外观

    3.4 探员  => [类型，品质，类别, 收藏品] 4个
        -可解析： 类型，品质，类别
        -需查询： 收藏品   最少查询2次大查询

    3.5 武器箱 => [类型，品质，类别, 收藏品] 4个
        -可解析： 类型，品质，类别
        -需查询： 收藏品   最少查询2次大查询

    3.6 工具,标签,礼物,通行证,药匙,收藏品,音乐(7) => [类型，品质，类别] 3个 最少查询1次大查询
        -可解析： 类型，品质，类别

    3.7 印花 => [类型，品质，类别，印花收藏品，印花类型，锦标赛，战队，职业选手] 8个
        -可解析： 类型，品质，类别
        -需查询： 印花收藏品，印花类型，锦标赛，战队，职业选手 最少查询6次大查询

    3.8 涂鸦 => [类型，品质，类别，涂鸦收藏品，涂鸦类型，涂鸦颜色，锦标赛，战队] 8个
        -可解析： 类型，品质，类别
        -需查询： 涂鸦收藏品，涂鸦类型，涂鸦颜色，锦标赛，战队 最少查询6次大查询

    3.9 布章 => [类型，品质，类别，布章收藏品，布章类型， 战队] 6个
        -可解析： 类型，品质，类别
        -需查询： 布章收藏品，布章类型， 战队 最少查询4次大查询

"""
import json
import time

import requests
from pathlib import Path

resource = Path(__file__).parent


def gem_spu(params: dict):
    url = "https://steamcommunity.com/market/search/render"
    headers = {"accept-language": "zh-CN,zh"}
    proxies = {'http': 'http://proxy.vmware.com:3128', 'https': 'http://proxy.vmware.com:3128'}

    resp: requests.Response = requests.get(url, params=params, headers=headers, proxies=proxies)

    if resp.status_code != 200:
        print(f"resp.status_code => {resp.status_code}")
        time.sleep(300)
        return gem_spu(params)

    try:
        result = resp.json()
        print("requests success")
        return result
    except Exception:
        result = None

    if result is None:
        print(f"resp.test = > {resp.text}")
        time.sleep(300)
        return gem_spu(params)


def get_pro_players_array(extra: dict):
    # 职业选手 查询
    players: dict[str, dict] = json.loads(resource.joinpath("730_ProPlayer.json").read_bytes())["tags"]
    for player in players:
        params = {"appid": 730, "norender": 1, "category_730_ProPlayer[]": f"tag_{player}"}
        params.update(extra)
        resp: dict = gem_spu(params)



def main():
    # 涂鸦 CSGO_Type_Spray 没有职业选手。
    # 布章，应该也没有
    # 音乐盒 CSGO_Type_MusicKit
    # 没连续请求25个默认就会被制裁， 等180秒没鸟用，等300秒肯定有用 但是太长，尝试240秒。。。
    # 每12秒请求一次，也行
    extra = {"category_730_Type[]": "tag_CSGO_Type_MusicKit"}


if __name__ == '__main__':
    main()
