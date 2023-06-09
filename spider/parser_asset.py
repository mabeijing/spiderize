import re

from settings import enums
from spider.models import MarketSPU
from settings import get_logger
from spider.mapping import get_rarity_asset

logger = get_logger()
exterior_pattern: re.Pattern = re.compile(r".*\((.*)\).*")


def _parse_quality_and_rarity(market_spu: MarketSPU):
    # 类别:Quality => 普通,纪念品,StatTrak™",★,★ StatTrak™", 都有，空表示普通
    # 品质:Rarity => 消费级，军规级，受限，工业级，普通级，保密，隐秘，高级，卓越。都有

    asset_items: list[str] = market_spu.asset_description.asset_type.split(" ")
    if len(asset_items) == 2:  # Quality:普通
        market_spu.query_item.quality = enums.QualityItem.normal
        localized_name = asset_items[0]
    elif len(asset_items) == 3:  # Quality:StatTrak™",★, 纪念品
        if asset_items[0] == "StatTrak™":
            market_spu.query_item.quality = enums.QualityItem.strange
        elif asset_items[0] == "纪念品":
            market_spu.query_item.quality = enums.QualityItem.tournament
        elif asset_items[0] == "★":
            market_spu.query_item.quality = enums.QualityItem.unusual
        else:
            logger.error(f"{asset_items} not parsed correct!")
        localized_name = asset_items[1]

    else:  # Quality: ★ StatTrak™"
        market_spu.query_item.quality = enums.QualityItem.unusual_strange
        localized_name = asset_items[2]

    rarity = get_rarity_asset(market_spu.query_item.spu_type, localized_name=localized_name)
    if not rarity:
        logger.error(f"Please check {market_spu.query_item.spu_type} has no {localized_name}")
    market_spu.query_item.rarity = rarity


def parser_market_spu(market_spu_array: list[MarketSPU], spu_type: str, weapon: bool, exterior: bool):
    # 类别:Quality => 普通,纪念品,StatTrak™",★,★ StatTrak™", 都有，空表示普通
    # 品质:Rarity => 消费级，军规级，受限，工业级，普通级，保密，隐秘，高级，卓越。都有
    # 武器名:Weapon => P250...
    # 外观:Exterior => 久经沙场，崭新出厂
    # "type": "普通级 涂鸦",  => 类别 品质 类型
    # "market_name": "P2000 | 廉价皮革 (略有磨损)", => 武器名 外观

    for market_spu in market_spu_array:
        market_spu.query_item.spu_type = spu_type

        _parse_quality_and_rarity(market_spu)

        asset_items: list[str] = [item.strip() for item in market_spu.name.split("|")]
        if len(asset_items) > 2:
            logger.warning(f"weapon length more 2 part => {asset_items}")

        if weapon:
            weapon_name: str = asset_items[0]
            market_spu.query_item.weapon = weapon_name

        if exterior:
            asset_exterior = asset_items[1]
            match = exterior_pattern.match(asset_exterior)
            if match is None:
                logger.error(f"weapon has no exterior => {asset_items}")
            else:
                exterior = match.group(1)
                market_spu.query_item.exterior = exterior
