other_rarity = {
    "普通级": "Rarity_Common",
    "卓越": "Rarity_Mythical",
    "奇异": "Rarity_Legendary",
    "高级": "Rarity_Rare",
    "非凡": "Rarity_Ancient",
    "违禁": "Rarity_Contraband"
}

character_rarity = {
    "高级": "Rarity_Rare_Character",
    "非凡": "Rarity_Legendary_Character",
    "卓越": "Rarity_Mythical_Character",
    "大师": "Rarity_Ancient_Character"
}

weapon_rarity = {
    "工业级": "Rarity_Uncommon_Weapon",
    "消费级": "Rarity_Common_Weapon",
    "军规级": "Rarity_Rare_Weapon",
    "受限": "Rarity_Mythical_Weapon",
    "保密": "Rarity_Legendary_Weapon",
    "隐秘": "Rarity_Ancient_Weapon"
}

quality_rarity = {
    "": "normal",
    "普通": "normal",
    "纪念品": "tournament",
    "StatTrak™": "strange",
    "★": "unusual",
    "★ StatTrak™": "unusual_strange"
}

weapon_type = [
    "狙击步枪",
    "步枪",
    "手枪",
    "微型冲锋枪",
    "霰弹枪",
    "机枪",
    "匕首"
]


def get_rarity_by_type(type_: str) -> dict:
    if type_ in weapon_type:
        return weapon_rarity
    elif type_ == "探员":
        return character_rarity
    else:
        return other_rarity
