"""
1. 根据现有数据库，和抓取基础数据，获取最新的查询条件

2. 根据查询条件，最少次数查询出需要的数据范围。
"""

import re
import json
import time
import os.path
import requests
from pathlib import Path


def generate_query_condition():
    url = "https://steamcommunity.com/market/search"
    headers = {"accept-language": "zh-CN,zh"}
    params = {"appid": 730}
    proxies = {'http': 'http://proxy.vmware.com:3128', 'https': 'http://proxy.vmware.com:3128'}

    resp: requests.Response = requests.get(url, params=params, headers=headers, proxies=proxies)

    html_content: str = resp.text

    # var g_rgFilterData = {...};

    filterPattern: re.Pattern = re.compile(r".*var g_rgFilterData = ({.*});.*", flags=re.DOTALL)

    match_obj: re.Match = filterPattern.match(html_content)

    if match_obj is None:
        return

    group_text: str = match_obj.group(1)

    filter_data: dict = eval(group_text)

    with open("query_condition.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps(filter_data, ensure_ascii=False, indent=2))


def update_after_expire(file: Path):
    # 1天有效期
    create_time = os.path.getctime(file)
    current_time = time.time()
    if current_time - create_time > 24 * 60 * 60:
        generate_query_condition()


def gem_weapon_map(file: Path) -> dict[str, str]:
    new_map = {}
    weapon_data: dict = json.loads(file.read_bytes())["730_Weapon"]
    weapon_tags: dict = weapon_data.get("tags")

    for weapon_tag, weapon_desc in weapon_tags.items():
        weapon_name: str = weapon_desc.get("localized_name").strip()
        new_map[weapon_name] = weapon_tag

    with open("weapon_map.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps(new_map, ensure_ascii=False, indent=2))
    return new_map


def main():
    # 判断文件是否存在
    condition_json_file = Path(__file__).parent.joinpath("query_condition.json")
    if not condition_json_file.exists():
        return

    # 更新
    update_after_expire(condition_json_file)

    # 对比当前数据库信息，如果不一样了，需要人工确认

    # 生成查询条件
    weapon_map = gem_weapon_map(condition_json_file)
    print(weapon_map)


if __name__ == '__main__':
    main()
