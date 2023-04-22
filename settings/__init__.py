import logging
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent

STATIC_DIR = ROOT.joinpath("static")

SETTINGS = ROOT.joinpath("settings")

logger = logging.getLogger()


def db_config(env="dev") -> dict:
    configuration: dict = yaml.safe_load(SETTINGS.joinpath(f"settings_{env}.yaml").read_bytes())
    return configuration["MYSQL_DATABASES"]


if __name__ == '__main__':
    print(db_config())
