import pymysql
import requests

import settings


def get_category_options_from_steam() -> dict[dict]:
    url = "https://steamcommunity.com/market/appfilters/730"
    params = {"l": "schinese"}
    resp = requests.get(url, params=params)
    assert resp.status_code == 200
    return resp.json()["facets"]


class SQLStatement:
    select_eoc_goods_facet_by_name = "select id from eoc_goods_facet where name = %s;"
    insert_eoc_goods_facet = "INSERT INTO eoc_goods_facet (name, localized_name) VALUES (%s,%s);"
    select_eoc_goods_tag_by_facetId = "select name from eoc_goods_tag where facet_id = %s;"
    insert_eoc_goods_tag = "INSERT INTO eoc_goods_tag (facet_id, name, localized_name) VALUES (%s, %s, %s);"


class CategoryOption:

    def __init__(self):
        self.connect = pymysql.connect(**settings.db_config("dev"))

    def insert_facet_and_tag_if_not_exist(self, facet: dict):
        name: str = facet["name"]
        localized_name: str = facet["localized_name"]
        tags: dict[str, dict] = facet["tags"]

        with self.connect.cursor() as cursor:
            cursor.execute(SQLStatement.select_eoc_goods_facet_by_name, args=(name,))
            result: tuple[int] | None = cursor.fetchone()

        if result is None:
            # 插入facet表
            with self.connect.cursor() as cursor:
                cursor.execute(SQLStatement.insert_eoc_goods_facet, args=(name, localized_name))
            with self.connect.cursor() as cursor:
                cursor.execute(SQLStatement.select_eoc_goods_facet_by_name, args=(name,))
                result: tuple[int] | None = cursor.fetchone()

        fid: int = int(result[0])
        with self.connect.cursor() as cursor:
            cursor.execute(SQLStatement.select_eoc_goods_tag_by_facetId, args=(fid,))
            results: tuple[tuple[...]] = cursor.fetchall()
            goods_tags: list[str] = [tag[0] for tag in results if tag]
            for tag, value in tags.items():
                localized_name: str = value["localized_name"]
                if tag not in goods_tags:
                    cursor.execute(SQLStatement.insert_eoc_goods_tag, args=(fid, tag, localized_name))

    def run(self):
        options: dict[dict] = get_category_options_from_steam()
        for facet in options.values():
            self.insert_facet_and_tag_if_not_exist(facet)

    def __del__(self):
        try:
            self.connect.close()
        except Exception:
            pass


if __name__ == '__main__':
    category_option = CategoryOption()
    category_option.run()
