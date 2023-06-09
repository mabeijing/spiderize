from typing import Optional
from pydantic import BaseModel, fields


class QueryItems(BaseModel):
    """
    和mongo的交互数据类型
    1. 字段是数组的 => tournament, pro_player, tournament_team, sticker_capsule, spray_capsule, patch_capsule
    2. 其他字段都是基本类型。
    """
    rarity: Optional[str] = fields.Field(None)  # 品质 唯一属性
    quality: Optional[str] = fields.Field(None)  # 类别   唯一属性
    spu_type: Optional[str] = fields.Field(None, alias='type')  # 类型 唯一属性
    weapon: Optional[str] = fields.Field(None)  # 武器名   唯一属性
    exterior: Optional[str] = fields.Field(None)  # 外观  唯一属性
    item_set: Optional[str] = fields.Field(None)  # 收藏品 唯一属性
    tournament: list[Optional[str]] = fields.Field([])  # 锦标赛 多属性
    pro_player: list[Optional[str]] = fields.Field([])  # 职业选手 多属性
    tournament_team: list[Optional[str]] = fields.Field([])  # 战队 多属性
    sticker_category: Optional[str] = fields.Field(None)  # 印花类型 唯一属性
    sticker_capsule: list[Optional[str]] = fields.Field([])  # 印花收藏品  多属性
    spray_capsule: list[Optional[str]] = fields.Field([])  # 涂鸦收藏品  多属性
    spray_category: Optional[str] = fields.Field(None)  # 涂鸦类型  唯一属性
    spray_color_category: Optional[str] = fields.Field(None)  # 涂鸦颜色    唯一属性
    patch_capsule: list[Optional[str]] = fields.Field([])  # 布章收藏品  多属性
    patch_category: Optional[str] = fields.Field(None)  # 布章类型  唯一属性


class AssetDescription(BaseModel):
    classid: str = fields.Field()
    instanceid: str = fields.Field()
    background_color: str = fields.Field()
    icon_url: str = fields.Field()
    icon_url_large: str = fields.Field("")
    name_color: str = fields.Field()
    asset_type: str = fields.Field(alias='type')
    market_hash_name: str = fields.Field()


class MarketSPU(BaseModel):
    name: str = fields.Field()
    hash_name: str = fields.Field()
    sell_listings: int = fields.Field()
    sell_price_text: str = fields.Field()
    asset_description: AssetDescription = fields.Field(default={})
    descriptions: list[dict] = fields.Field(default=[])
    query_item: QueryItems = fields.Field(default=QueryItems())


if __name__ == '__main__':
    data = {
        "name": "封装的涂鸦 | 加利尔AR压枪 (棕褐)",
        "hash_name": "Sealed Graffiti | Recoil Galil AR (Desert Amber)",
        "sell_listings": 6,
        "sell_price": 174,
        "sell_price_text": "$1.74",
        "app_icon": "https://media.st.dl.eccdnx.com/steamcommunity/public/images/apps/730/69f7ebe2735c366c65c0b33dae00e12dc40edbe4.jpg",
        "app_name": "Counter-Strike: Global Offensive",
        "asset_description": {
            "appid": 730,
            "classid": "4149732445",
            "instanceid": "519977179",
            "background_color": "",
            "icon_url": "IzMF03bi9WpSBq-S-ekoE33L-iLqGFHVaU25ZzQNQcXdB2ozio1RrlIWFK3UfvMYB8UsvjiMXojflsZalyxSh31CIyHz2GZ-KuFpPsrTzBGp8bDdU3P2ZD7IYSeOGlg7H7YIYT6I-Dr25O2cFznMFLt5FVpRLPFX8mBIaJqMP0Zv1NIVu2u_0UdyEhk6f9BKZAarxm1OMLh9m3IWeZrWsjk",
            "tradable": 1,
            "name": "封装的涂鸦 | 加利尔AR压枪 (棕褐)",
            "name_color": "D2D2D2",
            "type": "普通级 涂鸦",
            "market_name": "封装的涂鸦 | 加利尔AR压枪 (棕褐)",
            "market_hash_name": "Sealed Graffiti | Recoil Galil AR (Desert Amber)",
            "commodity": 1
        },
        "sale_price_text": "$1.67"
    }
    spu = MarketSPU.validate(data)
    # spu.query_item.exterior = "dscsdcsdcsdc"
    # print(spu.dict(by_alias=True))

    print(spu.dict(by_alias=True))
