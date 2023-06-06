import settings
from spider import Spider

logger = settings.get_logger()

if __name__ == '__main__':
    logger.info("start...")
    spider = Spider()
    spider.gem_weapon_spu()
