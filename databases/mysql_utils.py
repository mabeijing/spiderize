import json

from sqlalchemy import URL
from sqlalchemy import create_engine
from sqlalchemy import text

from pydantic import BaseModel, fields
import pymongo
import settings

url_instance = URL.create(**settings.db_config("dev"))
mongo_db = "steam_db"
mongo_collection = "steam_spu"
engine = create_engine(url_instance, max_overflow=20, pool_size=5, pool_recycle=1800, isolation_level="AUTOCOMMIT")
client = pymongo.MongoClient(settings.MONGO_URI, connect=False)


class SQLStatement:
    query_tag_type2 = text("select id, name from eoc_goods_tag where facet_id=:facet_id order by id;")
    query_spu_id = text("select id from eoc_goods_spu where market_hash_name=:market_hash_name;")
    insert_spu_tag = text("INSERT INTO eoc_goods_spu_tag (spu_id, tag_id) VALUES (:spu_id, :tag_id);")
    query_spu_tag = text("SELECT id FROM eoc_goods_spu_tag WHERE spu_id=:spu_id AND tag_id=:tag_id;")

    select_eoc_goods_facet_by_name = "select id from eoc_goods_facet where name = %s;"
    insert_eoc_goods_facet = "INSERT INTO eoc_goods_facet (name, localized_name) VALUES (%s,%s);"
    select_eoc_goods_tag_by_facetId = "select name from eoc_goods_tag where facet_id = %s;"
    insert_eoc_goods_tag = "INSERT INTO eoc_goods_tag (facet_id, name, localized_name) VALUES (%s, %s, %s);"

    query_spu = text(
        "select id from eoc_goods_spu where market_hash_name=:market_hash_name for update;")
    insert_spu = text("INSERT INTO eoc_goods_spu (classid, name, name_color, market_name, market_hash_name, icon_url, "
                      "icon_url_large,descriptions, price) VALUES (:classid, :name, :name_color, :market_name, "
                      ":market_hash_name, :icon_url, :icon_url_large, :descriptions,:price)")

    query_spu_all = text("select id, market_hash_name from eoc_goods_spu order by id;")
    query_tag = text("select localized_name from eoc_goods_tag where facet_id=15;")
    query_tag_by_localized_name = text("select id from eoc_goods_tag where localized_name=:localized_name")
    query_tag_by_name = text("select id from eoc_goods_tag where name=:name")
    # query_spu_tag = text("select id from eoc_goods_spu_tag where spu_id=:spu_id and tag_id=:tag_id;")
    update_spu_desc = text('UPDATE eoc_goods_spu SET descriptions=:descriptions WHERE id=:id and descriptions = ""')
    update_spu_icon = text(
        'UPDATE eoc_goods_spu SET icon_url_large=:icon_url_large where id=:id and icon_url_large ="";')

    goods_spu_descriptions = text('SELECT market_hash_name, icon_url_large, descriptions from eoc_goods_spu;')


class UpdateSPU(BaseModel):
    hash_name: str = fields.Field()
    icon_url_large: str = fields.Field("")
    descriptions: list[dict] = fields.Field([])


# with engine.connect() as connect:
#     sql = "select * from eoc_goods_spu"
#     cursor = connect.execute(SQLStatement.goods_spu_descriptions)
#
#     data_array = cursor.fetchall()
#
#     update_spu: list[UpdateSPU] = []
#     for data in data_array:
#         hash_name, icon_url_large, _descriptions = data
#         _descriptions: str = _descriptions if _descriptions else "[]"
#
#         descriptions = json.loads(_descriptions)
#
#         spu = UpdateSPU.validate({
#             "hash_name": hash_name,
#             "icon_url_large": icon_url_large,
#             "descriptions": descriptions
#         })
#         update_spu.append(spu)
#
# db = client.get_database(mongo_db)
# collection = db.get_collection(mongo_collection)
# for spu in update_spu:
#     print(spu.hash_name)
#     result = collection.update_one(
#         {"hash_name": spu.hash_name},
#         {"$set": {"asset_description.icon_url_large": spu.icon_url_large, "descriptions": spu.descriptions}}
#     )
#     print(f"更新结果=>{result.acknowledged} and {result.modified_count}")
