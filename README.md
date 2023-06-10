# spiderize



功能

1. 支持断点运行。脚本停止后，重新启动，会继续上次运行
   1. 可选参数，only_updated = True 不会爬取原始数据，只会更新数据的asset。
   2. 可选参数，ignore_breakpoint = False, 默认每个属性只会执行一轮，忽略断点可以重新开始执行更新属性



使用

1. 安装python3.9版本以上
```shell
   cd spiderize
   pip install -r requirements.txt
3. ```
2. 在spiderize文件夹下，main.py

   ```python
   # 默认是仅更新模式，不会执行爬取spu，只会更新现有spu的asset
   # 所有gem_开头的方法，都是需要执行爬取的种类，一共20个
   from spider import Spider
   
   if __name__ == '__main__':
       spider = Spider()
       spider.gem_weapon_pistol_spu()
   ```

2. ```python
   if __name__ == '__main__':
       spider = Spider(only_update=False)	# 可以开启爬取spu，并且更新spu的asset
       spider.gem_weapon_pistol_spu()
   ```

   

当前问题

1. steam返回数据，正常请求未被拦截是数据返回 [] ，没数据，导致判断数据已经返回结束。

   ```txt
   [2023-06-10 09:31:18,740] - [spiderize] - INFO - the 1 requests success. tag_CSGO_Type_Pistol => 718
   [2023-06-10 09:31:21,586] - [spiderize] - INFO - the 2 requests success. tag_CSGO_Type_Pistol => 718
   [2023-06-10 09:31:22,451] - [spiderize] - INFO - the 3 requests success. tag_CSGO_Type_Pistol => 0
   [2023-06-10 09:31:22,451] - [spiderize] - WARNING - 锦标赛Tournament：Tournament9 => 没有数据了。
   ```

2. 更新一个种类的asset的时候，需要手工修改要更新的属性



