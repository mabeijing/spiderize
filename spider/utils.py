import re
import json
from typing import Optional

xml_pattern = re.compile(r'.*(<div id="sticker_info".*</div>)')
sticker_img_pattern = re.compile(r'<img.*?src="(.*?png)">')
sticker_name_pattern = re.compile(r'.*<br>印花: (.*?)</center></div>.*')
patch_name_pattern = re.compile(r".*<br>布章: (.*?)</center></div>.*")
tips_pattern = re.compile(r"<i>(.*)</i>")


def handle_description(description: list[Optional[dict]]) -> tuple[Optional[str], Optional[str], Optional[str], str]:
    group: Optional[str] = None  # 收藏品
    stamp: Optional[str] = None  # 印花 布章
    tips: Optional[str] = None  # <i></i>

    # 剔除空描述
    description: list[Optional[dict]] = [item for item in description if item.get("value").strip()]

    # 找到收藏品，从desc中提出
    for index, item in enumerate(description):
        if item.get("color", "") == "9da1a9":
            description.pop(index)
            group: str = item.get("value")
            break

    # 剔除外观描述：外观：
    for index, item in enumerate(description):
        if item.get("value", "").startswith("外观： "):
            description.pop(index)
            break

    # 处理印花
    for index, item in enumerate(description):
        xml_or_string: str = item.get("value", "")
        may_match_stamp = xml_pattern.search(xml_or_string)
        if may_match_stamp:  # 说明有关联印花
            description.pop(index)
            xml_source: str = may_match_stamp.group(1)
            img_array: list[Optional[str]] = sticker_img_pattern.findall(xml_source)  # 印花图片列表
            m = sticker_name_pattern.search(xml_source)
            if m:  # 印花
                _name: str = m.group(1)
                name_array: list[str] = [n.strip() for n in _name.split(',')]
                stamp: str = json.dumps(dict(zip(name_array, img_array)))
            p = patch_name_pattern.search(xml_source)
            if p:  # 布章
                _name: str = p.group(1)
                name_array: list[str] = [n.strip() for n in _name.split(',')]
                stamp: str = json.dumps(dict(zip(name_array, img_array)))
            if p and m:
                print(f"布章和印花不能同时存在！-> {xml_source}")
            break

    # 处理口语
    for item in description:
        xml_or_string: str = item.get("value", "")
        may_match_tips = tips_pattern.search(xml_or_string)  # 不管有没有印花元素，都要在踢掉tip
        if may_match_tips:  # 说明匹配到i标签
            tips: str = may_match_tips.group(1).strip()
            _start, _stop = may_match_tips.span()
            item["value"] = xml_or_string[:_start].strip() + xml_or_string[_stop:].strip()  # 从desc中踢掉tips
            break

    # 将剩余信息拼接成描述
    desc: str = ','.join([item["value"] for item in description])
    return group, stamp, tips, desc


def handle_cargo_type(cargo_type: str) -> tuple[str, str, str]:
    _desc_type_array: list[str] = cargo_type.strip().split(' ')

    if len(_desc_type_array) == 2:
        #  普通级 武器箱
        type_: str = _desc_type_array[1].strip()  # 类型，手枪，武器箱，印花，理论上一定存在
        rarity: str = _desc_type_array[0].strip()
        quality: str = "普通"

    elif len(_desc_type_array) == 3:
        # StatTrak™ 普通级 武器箱
        # ★ 普通级 武器箱
        type_: str = _desc_type_array[2].strip()
        rarity: str = _desc_type_array[1].strip()
        quality: str = _desc_type_array[0].strip()
    else:
        # ★ StatTrak™ 普通级 武器箱
        type_: str = _desc_type_array[-1].strip()
        rarity: str = _desc_type_array[-2].strip()
        quality: str = ' '.join(_desc_type_array[:2]).strip()

    return quality, rarity, type_


def handler_cargo_asset(market_name: str, type_: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    _compose_name_array: list[str] = market_name.strip().split('|')

    weapon: Optional[str] = None
    skin: Optional[str] = None
    appearance: Optional[str] = None

    if len(_compose_name_array) == 1:
        # 胶囊 or 武器箱 or 工具 or 收藏品 or 标签 or 钥匙  or 通行证 or 匕首 or 礼物
        if type_ not in ("胶囊", "武器箱", "工具", "收藏品", "标签", "钥匙", "通行证", "匕首", "礼物"):
            print(
                f"the name -> {market_name}, not in (胶囊 or 武器箱 or 工具 or 收藏品 or 标签 or 钥匙  or 通行证 or 匕首 or 礼物)")

    elif len(_compose_name_array) == 2:
        # P250 | X 射线 包裹 很特殊的武器箱
        # 音乐盒 or 武器 or 印花 or 探员 or 涂鸦 or 布章 or 匕首 or 手套
        if type_ not in (
                "微型冲锋枪", "狙击步枪", "步枪", "霰弹枪", "手枪", "机枪", "匕首", "手套", "音乐盒", "印花", "探员",
                "涂鸦", "布章", "武器箱"):
            print(
                f"the name -> {market_name}, not in (音乐盒 or 武器 or 印花 or 探员 or 涂鸦 or 布章 or 匕首 or 手套 or 武器箱)")

        if type_ in ("微型冲锋枪", "狙击步枪", "步枪", "霰弹枪", "手枪", "机枪", "匕首", "手套"):
            # 武器，有名字，外观，皮肤，印章，tips，和groups
            weapon_or_quality: str = _compose_name_array[0].strip()
            _index: int = weapon_or_quality.rfind("（")
            if _index != -1:
                weapon: str = weapon_or_quality[:_index].strip()  # 武器名
            else:
                weapon: str = weapon_or_quality

            skin_and_appear: str = _compose_name_array[1].strip()
            _index: int = skin_and_appear.rfind("(")
            if _index != -1:
                skin: str = skin_and_appear[:_index].strip()  # 皮肤
                appearance: str = skin_and_appear[_index + 1:-1]  # 外观

    elif len(_compose_name_array) == 3:  # 印花 or 涂鸦 or 布章 or 胶囊
        if type_ not in ("印花", "涂鸦", "布章", "胶囊"):
            print(f"the name => {market_name}, not in (印花 or 涂鸦 or 布章 or 胶囊)")

    else:
        raise ValueError(f"未处理过的数据类型 -> {market_name}")

    return weapon, skin, appearance


def handler_weapon_asset(market_name: str) -> tuple[str, str]:
    _compose_name_array: list[str] = market_name.strip().split('|')

    appearance: str = "无涂装"

    weapon_or_quality: str = _compose_name_array[0].strip()
    _index: int = weapon_or_quality.rfind("（")
    if _index != -1:
        weapon: str = weapon_or_quality[:_index].strip()  # 武器名
    else:
        weapon: str = weapon_or_quality

    skin_and_appear: str = _compose_name_array[1].strip()
    _index: int = skin_and_appear.rfind("(")
    if _index != -1:
        appearance: str = skin_and_appear[_index + 1:-1]  # 外观

    return weapon, appearance
