from enum import Enum


class QualityItem(str, Enum):
    normal = "normal"  # "普通"
    tournament = "tournament"  # "纪念品"
    strange = "strange"  # "StatTrak™"
    unusual = "unusual"  # "★"
    unusual_strange = "unusual_strange"  # "★ StatTrak™"


class TypeItem(str, Enum):
    CSGO_Type_Pistol = "CSGO_Type_Pistol"  # 手枪
    CSGO_Type_SMG = "CSGO_Type_SMG"  # 微型冲锋枪
    CSGO_Type_Rifle = "CSGO_Type_Rifle"  # 步枪
    CSGO_Type_SniperRifle = "CSGO_Type_SniperRifle"  # 狙击步枪
    CSGO_Type_Shotgun = "CSGO_Type_Shotgun"  # 霰弹枪
    CSGO_Type_Machinegun = "CSGO_Type_Machinegun"  # 机枪
    CSGO_Type_WeaponCase = "CSGO_Type_WeaponCase"  # 武器箱
    Type_CustomPlayer = "Type_CustomPlayer"  # 探员
    CSGO_Type_Knife = "CSGO_Type_Knife"  # 匕首
    CSGO_Tool_Sticker = "CSGO_Tool_Sticker"  # 印花
    Type_Hands = "Type_Hands"  # 手套
    CSGO_Type_Spray = "CSGO_Type_Spray"  # 涂鸦
    CSGO_Type_MusicKit = "CSGO_Type_MusicKit"  # 音乐盒
    CSGO_Tool_Patch = "CSGO_Tool_Patch"  # 布章
    CSGO_Type_Collectible = "CSGO_Type_Collectible"  # 收藏品
    CSGO_Tool_WeaponCase_KeyTag = "CSGO_Tool_WeaponCase_KeyTag"  # 钥匙
    CSGO_Type_Ticket = "CSGO_Type_Ticket"  # 通行证
    CSGO_Tool_GiftTag = "CSGO_Tool_GiftTag"  # 礼物
    CSGO_Tool_Name_TagTag = "CSGO_Tool_Name_TagTag"  # 标签
    CSGO_Type_Tool = "CSGO_Type_Tool"  # 工具
