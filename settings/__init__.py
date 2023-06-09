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

# ------------------------- 运行配置参数 ----------------------

# 缓存名字，默认无需改动。用于断点执行
CACHE_NAME = '.cache'

# 更新基础数据 用于判断是否需要更新
BASIC_RESOURCES = '_basic_730_resources.json'

# 基础数据更新时间 默认不更新， 如要更新EXPIRE_TIME = 7 * 24 * 60 * 60
EXPIRE_TIME = None

# ------------------------- 爬虫配置参数 ----------------------

# steam 市场URL
MARKET_URL = "https://steamcommunity.com/market/search/render"
# 请求是否加代理
# PROXY_POOL = None
PROXY_POOL = {'http': 'http://proxy.vmware.com:3128', 'https': 'http://proxy.vmware.com:3128'}

# 请求被拦截后等待多久再次请求， 最少5分钟，请求默认25次后，会被限制，5分钟后解除
DELAY_TIME = 300

# 每次获取数据量， 目前最大100，超过100不生效
COUNT = 100

# ------------------------- 数据库配置参数 ----------------------

# 数据库配置
MONGO_URI = "mongodb://root:example@localhost:27017"
MONGO_DB = "steam_db"
MONGO_COLLECTION = "steam_spu"


def db_config(env="dev") -> dict:
    configuration: dict = yaml.safe_load(SETTINGS.joinpath(f"settings_{env}.yaml").read_bytes())
    return configuration["MYSQL_DATABASES"]


def get_logger(config_yaml: str = "logging.yaml", **kwargs) -> logging.Logger:
    config: dict = yaml.safe_load(SETTINGS.joinpath(config_yaml).read_bytes())
    log_dir = ROOT.joinpath('logs')
    if not log_dir.exists():
        log_dir.mkdir()
    default_kwargs = {"logfile": f"{ROOT.joinpath('logs', 'running.log')}"}
    default_kwargs.update(kwargs)
    parsed_config = _parser(config, default_kwargs)
    logging.config.dictConfig(parsed_config)
    return logging.getLogger('spiderize')


@lru_cache()
def get_sorted_resources(name: str) -> list[str]:
    tags: dict[str, dict] = json.loads(RESOURCES.joinpath(name).read_bytes())["tags"]
    return sorted(tags)


def _parser(config, kwargs: dict):
    # 用于增强yaml配置。支持key，value的参数化
    if isinstance(config, list):
        for index, element in enumerate(config):
            config[index] = _parser(element, kwargs)
    if isinstance(config, dict):
        # 如果key满足${}格式，就解析
        new_config = {}
        for k, v in config.items():
            match: Optional[re.Match] = _variable_pattern.match(k)
            if match:
                k = kwargs.get(match.group(1))
                if k is None:
                    raise ValueError(f"{k} not a valid key for the {kwargs}")
            new_config[k] = _parser(v, kwargs)
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


if __name__ == '__main__':
    get_logger()
