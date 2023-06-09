"""
比较重要的映射关系，并且，需要人工维护，因为卓越，非凡，高级，有重名属性

武器类 6
  [CSGO_Type_Pistol, CSGO_Type_SMG, CSGO_Type_Rifle, CSGO_Type_SniperRifle, CSGO_Type_Shotgun, CSGO_Type_Machinegun]
  [CSGO_Type_Knife: 都是隐秘]
    => Rarity_Common_Weapon 消费级
    => Rarity_Rare_Weapon 军规级
    => Rarity_Mythical_Weapon 受限
    => Rarity_Uncommon_Weapon 工业级
    => Rarity_Legendary_Weapon 保密
    => Rarity_Ancient_Weapon 隐秘

探员 4
[Type_CustomPlayer]
    63
    => Rarity_Mythical_Character 卓越 16
    => Rarity_Legendary_Character 非凡 15
    => Rarity_Ancient_Character 大师 16
    => Rarity_Rare_Character 高级 16

其他 6
[CSGO_Type_WeaponCase, CSGO_Tool_Sticker， Type_Hands， CSGO_Type_Spray，CSGO_Type_MusicKit，CSGO_Type_Collectible, ]
[Type_Hands]
    => Rarity_Common 普通级
    => Rarity_Ancient 非凡
    => Rarity_Rare 高级
    => Rarity_Mythical 卓越
    => Rarity_Legendary 奇异
    => Rarity_Contraband 违禁


"""

# 非常重要的分类表。需要手工分类
WEAPON_TYPE = (
    'CSGO_Type_Pistol',
    'CSGO_Type_SMG',
    'CSGO_Type_Rifle',
    'CSGO_Type_SniperRifle',
    'CSGO_Type_Shotgun',
    'CSGO_Type_Machinegun',
    'CSGO_Type_Knife'
)

# 非常重要的分类表。需要手工分类
CHARACTER_TYPE = (
    'Type_CustomPlayer',
)

# 非常重要的分类表。需要手工分类
OTHER_TYPE = (
    'CSGO_Type_WeaponCase',
    'CSGO_Tool_Sticker',
    'Type_Hands',
    'CSGO_Type_Spray',
    'CSGO_Type_MusicKit',
    'CSGO_Tool_Patch',
    'CSGO_Type_Collectible',
    'CSGO_Tool_WeaponCase_KeyTag',
    'CSGO_Type_Ticket',
    'CSGO_Tool_GiftTag',
    'CSGO_Tool_Name_TagTag',
    'CSGO_Type_Tool'
)

# 非常重要的分类表。需要手工分类
SUPPORT_ASSET_MAP = {
    "CSGO_Type_Pistol": {"weapon": True, "exterior": True},
    "CSGO_Type_SMG": {"weapon": True, "exterior": True},
    "CSGO_Type_Rifle": {"weapon": True, "exterior": True},
    "CSGO_Type_SniperRifle": {"weapon": True, "exterior": True},
    "CSGO_Type_Shotgun": {"weapon": True, "exterior": True},
    "CSGO_Type_Machinegun": {"weapon": True, "exterior": True},
    "CSGO_Type_Knife": {"weapon": True, "exterior": True},
    "Type_Hands": {"weapon": False, "exterior": True}
}

# 非常重要的分类表。需要手工分类
WEAPON_NAME_MAP = {
    "P250": "weapon_p250",
    "PP-野牛": "weapon_bizon",
    "MAC-10": "weapon_mac10",
    "AUG": "weapon_aug",
    "Tec-9": "weapon_tec9",
    "MP7": "weapon_mp7",
    "SG 553": "weapon_sg556",
    "格洛克 18 型": "weapon_glock",
    "SSG 08": "weapon_ssg08",
    "R8 左轮手枪": "weapon_revolver",
    "新星": "weapon_nova",
    "MAG-7": "weapon_mag7",
    "AK-47": "weapon_ak47",
    "P90": "weapon_p90",
    "UMP-45": "weapon_ump45",
    "G3SG1": "weapon_g3sg1",
    "MP9": "weapon_mp9",
    "AWP": "weapon_awp",
    "SCAR-20": "weapon_scar20",
    "FN57": "weapon_fiveseven",
    "沙漠之鹰": "weapon_deagle",
    "双持贝瑞塔": "weapon_elite",
    "截短霰弹枪": "weapon_sawedoff",
    "XM1014": "weapon_xm1014",
    "M4A4": "weapon_m4a1",
    "法玛斯": "weapon_famas",
    "P2000": "weapon_hkp2000",
    "加利尔 AR": "weapon_galilar",
    "M4A1 消音型": "weapon_m4a1_silencer",
    "MP5-SD": "weapon_mp5sd",
    "内格夫": "weapon_negev",
    "CZ75": "weapon_cz75a",
    "M249": "weapon_m249",
    "USP 消音版": "weapon_usp_silencer",
    "暗影双匕": "weapon_knife_push",
    "弯刀": "weapon_knife_falchion",
    "穿肠刀": "weapon_knife_gut",
    "折刀": "weapon_knife_gypsy_jackknife",
    "鲍伊猎刀": "weapon_knife_survival_bowie",
    "猎杀者匕首": "weapon_knife_tactical",
    "折叠刀": "weapon_knife_flip",
    "刺刀": "weapon_bayonet",
    "熊刀": "weapon_knife_ursus",
    "求生匕首": "weapon_knife_canis",
    "系绳匕首": "weapon_knife_cord",
    "锯齿爪刀": "weapon_knife_widowmaker",
    "短剑": "weapon_knife_stiletto",
    "海豹短刀": "weapon_knife_css",
    "M9 刺刀": "weapon_knife_m9_bayonet",
    "蝴蝶刀": "weapon_knife_butterfly",
    "爪子刀": "weapon_knife_karambit",
    "流浪者匕首": "weapon_knife_outdoor",
    "骷髅匕首": "weapon_knife_skeleton"
}


def _weapon_rarity_duplex_map(rarity_tag: str = None, localized_name: str = None):
    """
    => Rarity_Common_Weapon 消费级
    => Rarity_Rare_Weapon 军规级
    => Rarity_Mythical_Weapon 受限
    => Rarity_Uncommon_Weapon 工业级
    => Rarity_Legendary_Weapon 保密
    => Rarity_Ancient_Weapon 隐秘
    """
    if localized_name == "消费级":
        return "Rarity_Common_Weapon"
    if localized_name == "军规级":
        return "Rarity_Rare_Weapon"
    if localized_name == "受限":
        return "Rarity_Mythical_Weapon"
    if localized_name == "工业级":
        return "Rarity_Uncommon_Weapon"
    if localized_name == "保密":
        return "Rarity_Legendary_Weapon"
    if localized_name == "隐秘":
        return "Rarity_Ancient_Weapon"

    if rarity_tag == "Rarity_Common_Weapon":
        return "消费级"
    if rarity_tag == "Rarity_Rare_Weapon":
        return "军规级"
    if rarity_tag == "Rarity_Mythical_Weapon":
        return "受限"
    if rarity_tag == "Rarity_Uncommon_Weapon":
        return "工业级"
    if rarity_tag == "Rarity_Legendary_Weapon":
        return "保密"
    if rarity_tag == "Rarity_Ancient_Weapon":
        return "隐秘"


def _character_rarity_duplex_map(rarity_tag: str = None, localized_name: str = None):
    """
    => Rarity_Mythical_Character 卓越 16
    => Rarity_Legendary_Character 非凡 15
    => Rarity_Ancient_Character 大师 16
    => Rarity_Rare_Character 高级 16
    """
    if localized_name == "高级":
        return "Rarity_Rare_Character"
    if localized_name == "大师":
        return "Rarity_Ancient_Character"
    if localized_name == "非凡":
        return "Rarity_Legendary_Character"
    if localized_name == "卓越":
        return "Rarity_Mythical_Character"

    if rarity_tag == "Rarity_Rare_Character":
        return "高级"
    if rarity_tag == "Rarity_Ancient_Character":
        return "大师"
    if rarity_tag == "Rarity_Legendary_Character":
        return "非凡"
    if rarity_tag == "Rarity_Mythical_Character":
        return "卓越"


def _other_rarity_duplex_map(rarity_tag: str = None, localized_name: str = None):
    """
    => Rarity_Common 普通级
    => Rarity_Ancient 非凡
    => Rarity_Rare 高级
    => Rarity_Mythical 卓越
    => Rarity_Legendary 奇异
    => Rarity_Contraband 违禁
    """
    if localized_name == "普通级":
        return "Rarity_Common"
    if localized_name == "非凡":
        return "Rarity_Ancient"
    if localized_name == "高级":
        return "Rarity_Rare"
    if localized_name == "卓越":
        return "Rarity_Mythical"
    if localized_name == "奇异":
        return "Rarity_Legendary"
    if localized_name == "违禁":
        return "Rarity_Contraband"

    if rarity_tag == "Rarity_Common":
        return "普通级"
    if rarity_tag == "Rarity_Ancient":
        return "非凡"
    if rarity_tag == "Rarity_Rare":
        return "高级"
    if rarity_tag == "Rarity_Mythical":
        return "卓越"
    if rarity_tag == "Rarity_Legendary":
        return "奇异"
    if rarity_tag == "Rarity_Contraband":
        return "违禁"


# 对外方法
def get_rarity_asset(spu_type: str, rarity_tag: str = None, localized_name: str = None) -> str:
    if spu_type in WEAPON_TYPE:
        return _weapon_rarity_duplex_map(rarity_tag, localized_name)

    if spu_type in CHARACTER_TYPE:
        return _character_rarity_duplex_map(rarity_tag, localized_name)

    if spu_type in OTHER_TYPE:
        return _other_rarity_duplex_map(rarity_tag, localized_name)


if __name__ == '__main__':
    rarity = get_rarity_asset("CSGO_Tool_Sticker", localized_name="普通级")
    print(rarity)
