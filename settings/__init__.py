import re
import json
import logging
import logging.config
from pathlib import Path
from typing import Optional
from functools import lru_cache

import yaml

_variable_pattern: re.Pattern = re.compile(r'^\$\{(.*)}$')

ROOT = Path(__file__).parent.parent

SETTINGS = ROOT.joinpath("settings")

RESOURCES = ROOT.joinpath("resources")

MONGO_URI = "mongodb://root:example@localhost:27017"
MONGO_DB = "tms_db"
MONGO_COLLECTION = "steam_spu"


def db_config(env="dev") -> dict:
    configuration: dict = yaml.safe_load(SETTINGS.joinpath(f"settings_{env}.yaml").read_bytes())
    return configuration["MYSQL_DATABASES"]


def get_logger(config_yaml: str = "logging.yaml", **kwargs) -> logging.Logger:
    config: dict = yaml.safe_load(SETTINGS.joinpath(config_yaml).read_bytes())
    default_kwargs = {"logfile": f"{ROOT.joinpath('logs', 'running.log')}"}
    default_kwargs.update(kwargs)
    parsed_config = parser(config, default_kwargs)
    logging.config.dictConfig(parsed_config)
    return logging.getLogger('spiderize')


@lru_cache()
def get_resources_map(name: str) -> dict[str, dict]:
    tags: dict[str, dict] = json.loads(RESOURCES.joinpath(name).read_bytes())["tags"]
    return tags


def parser(config, kwargs: dict):
    # 用于增强yaml配置。支持key，value的参数化
    if isinstance(config, list):
        for index, element in enumerate(config):
            config[index] = parser(element, kwargs)
    if isinstance(config, dict):
        # 如果key满足${}格式，就解析
        new_config = {}
        for k, v in config.items():
            match: Optional[re.Match] = _variable_pattern.match(k)
            if match:
                k = kwargs.get(match.group(1))
                if k is None:
                    raise ValueError(f"{k} not a valid key for the {kwargs}")
            new_config[k] = parser(v, kwargs)
        return new_config
    if isinstance(config, (int, float)):
        return config
    if isinstance(config, str):
        # 如果value满足${}格式，就解析
        match: Optional[re.Match] = _variable_pattern.match(config)
        if match:
            value = kwargs.get(match.group(1))
            if value is None:
                raise ValueError(f"{config} not a valid key for the {kwargs}")
            return value
    return config
