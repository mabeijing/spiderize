"""
将mongo的数据，转化成mysql数据表的映射关系

1. 需要mysql的基础数据，查询出来。
2. 先将mongo的数据，读取出来，转成mysql需要的字段插入
3. 在根据hash_name，从mongo查询出spu的所有属性，在去mysql查询，有就不动，没有就新增，None的就删除
"""
