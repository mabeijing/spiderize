import json
import re
import logging
import logging.config
from pathlib import Path
from functools import lru_cache

import yaml

VARIABLE_PATTERN: re.Pattern = re.compile(r'^\$\{(.*)}$')

ROOT = Path(__file__).parent.parent

SETTINGS = ROOT.joinpath("settings")

RESOURCES = ROOT.joinpath("resources")

MONGO_URI = "mongodb://root:example@localhost:27017"

MONGO_DB = "tms_db"
MONGO_COLLECTION = "steam_spu"


def db_config(env="dev") -> dict:
    configuration: dict = yaml.safe_load(SETTINGS.joinpath(f"settings_{env}.yaml").read_bytes())
    return configuration["MYSQL_DATABASES"]


def get_logger(config_yaml: str = "logging.yaml") -> logging.Logger:
    config: dict = yaml.safe_load(SETTINGS.joinpath(config_yaml).read_bytes())
    logging.config.dictConfig(config)
    return logging.getLogger('spiderize')


@lru_cache()
def get_resources_map(name: str) -> dict[str, dict]:
    tags: dict[str, dict] = json.loads(RESOURCES.joinpath(name).read_bytes())["tags"]
    return tags


if __name__ == '__main__':
    import time

    tsp = time.time()
    for _ in range(1000):
        get_resources_map("730_ItemSet.json")

    cost = time.time() - tsp
    print(cost)
