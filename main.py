import settings
from spider import Spider

logger = settings.get_logger()

if __name__ == '__main__':
    logger.info("start...")
    spider = Spider(only_update=False)
    spider.gem_weapon_smg_spu()
