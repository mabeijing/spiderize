from sqlalchemy import URL
from sqlalchemy import create_engine
from sqlalchemy import text

import settings

url_instance = URL.create(**settings.db_config("dev"))

engine = create_engine(url_instance, max_overflow=20, pool_size=5, pool_recycle=1800, isolation_level="AUTOCOMMIT")


class SQLStatement:
    query_tag_type2 = text("select id, name from eoc_goods_tag where facet_id=:facet_id order by id;")
    query_spu_id = text("select id from eoc_goods_spu where market_hash_name=:market_hash_name;")
    insert_spu_tag = text("INSERT INTO eoc_goods_spu_tag (spu_id, tag_id) VALUES (:spu_id, :tag_id);")

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
    query_spu_tag = text("select id from eoc_goods_spu_tag where spu_id=:spu_id and tag_id=:tag_id;")
    update_spu_desc = text('UPDATE eoc_goods_spu SET descriptions=:descriptions WHERE id=:id and descriptions = ""')
    update_spu_icon = text(
        'UPDATE eoc_goods_spu SET icon_url_large=:icon_url_large where id=:id and icon_url_large ="";')
