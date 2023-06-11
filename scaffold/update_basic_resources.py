import re
import json
import time
import os.path
import requests
from pathlib import Path

import settings

logger = settings.get_logger()

filterPattern: re.Pattern = re.compile(r".*var g_rgFilterData = ({.*});.*", flags=re.DOTALL)


def generate_730_basic_resources():
    """
    更新resource的基础数据，并且删除cache
    """
    url = "https://steamcommunity.com/market/search"
    params = {"appid": 730}
    headers = {"accept-language": "zh-CN,zh"}

    resp: requests.Response = requests.get(url, params=params, headers=headers, proxies=settings.PROXY_POOL)

    # var g_rgFilterData = {...};
    html_content: str = resp.text

    match_obj: re.Match = filterPattern.match(html_content)

    if match_obj is None:
        logger.error(f"更新基础数据失败，解析失败，请检查网页数据。。。")
        return

    group_text: str = match_obj.group(1)
    filter_data: dict = eval(group_text)

    tmp_file = settings.RESOURCES.joinpath(settings.BASIC_RESOURCES)
    if tmp_file.exists():
        tmp_file.unlink(missing_ok=True)

    with open(tmp_file, mode="w", encoding="utf-8") as f:
        f.write(json.dumps(filter_data, ensure_ascii=False, indent=2))

    basic_resource: dict[str, dict] = json.loads(tmp_file.read_bytes())

    for name, resource in basic_resource.items():
        file_name = f"{settings.RESOURCES.joinpath(name)}.json"
        with open(file_name, mode="w", encoding="utf-8") as f:
            f.write(json.dumps(resource, ensure_ascii=False, indent=2))

    settings.RESOURCES.joinpath(settings.CACHE_NAME).unlink(missing_ok=True)


def gem_weapon_map(file: Path):
    new_map = {}
    weapon_data: dict = json.loads(file.read_bytes())["730_Weapon"]
    weapon_tags: dict = weapon_data.get("tags")

    for weapon_tag, weapon_desc in weapon_tags.items():
        weapon_name: str = weapon_desc.get("localized_name").strip()
        new_map[weapon_name] = weapon_tag

    with open("weapon_map.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps(new_map, ensure_ascii=False, indent=2))


def update_after_expire(file: Path):
    create_time = os.path.getctime(file)
    current_time = time.time()
    if settings.EXPIRE_TIME and isinstance(settings.EXPIRE_TIME, (int, float)):
        if current_time - create_time > settings.EXPIRE_TIME:
            generate_730_basic_resources()
            gem_weapon_map(file)


def init_basic_resources():
    # 判断文件是否存在
    basic_resources = settings.RESOURCES.joinpath(settings.BASIC_RESOURCES)
    if not basic_resources.exists():
        generate_730_basic_resources()

    # 更新
    update_after_expire(basic_resources)

    # 创建WEAPON_MAP
    weapon_tag_map: dict[str, dict] = json.loads(settings.RESOURCES.joinpath("730_Weapon.json").read_bytes())['tags']

    weapon_map: dict[str, str] = {}
    for weapon_tag, tag_map in weapon_tag_map.items():
        localized_name: str = tag_map.get("localized_name")
        weapon_map[localized_name] = weapon_tag

    with open(settings.RESOURCES.joinpath(settings.WEAPON_MAP_NAME), mode="w", encoding="utf-8") as f:
        f.write(json.dumps(weapon_map, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    init_basic_resources()
