from spider import Spider

if __name__ == '__main__':
    spider = Spider()
    # 探员
    # spider.gem_custom_player_spu(only_update=True, ignore_breakpoint=True)

    # 涂鸦
    # spider.gem_spray_spu(only_update=False, ignore_breakpoint=True)

    # 机枪
    # spider.gem_weapon_machinegun_spu(only_update=False, ignore_breakpoint=True)

    # spider.gem_weapon_smg_spu(only_update=False, ignore_breakpoint=True)
    spider.convert_tools.update_goods_spu()
