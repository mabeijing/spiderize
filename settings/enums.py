from enum import Enum


class QualityItem(str, Enum):
    normal = "normal"  # "普通"
    tournament = "tournament"  # "纪念品"
    strange = "strange"  # "StatTrak™"
    unusual = "unusual"  # "★"
    unusual_strange = "unusual_strange"  # "★ StatTrak™"
