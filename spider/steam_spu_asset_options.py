import requests

from databases.mysql_utils import engine, SQLStatement


def get_category_options_from_steam() -> dict[dict]:
    url = "https://steamcommunity.com/market/appfilters/730"
    params = {"l": "schinese"}
    resp = requests.get(url, params=params)
    assert resp.status_code == 200
    return resp.json()["facets"]


def insert_facet_and_tag_if_not_exist(facet: dict):
    name: str = facet["name"]
    localized_name: str = facet["localized_name"]
    tags: dict[str, dict] = facet["tags"]

    with engine.connect() as connection:
        cursor = connection.execute(SQLStatement.select_eoc_goods_facet_by_name, args=(name,))
        result: tuple[int] | None = cursor.fetchone()

    if result is None:
        # 插入facet表
        with engine.connect() as connection:
            connection.execute(SQLStatement.insert_eoc_goods_facet, args=(name, localized_name))

        with engine.connect() as connection:
            cursor = connection.execute(SQLStatement.select_eoc_goods_facet_by_name, args=(name,))
            result: tuple[int] | None = cursor.fetchone()

    fid: int = int(result[0])
    with engine.connect() as connection:

        cursor = connection.execute(SQLStatement.select_eoc_goods_tag_by_facetId, args=(fid,))
        results: tuple[tuple[...]] = cursor.fetchall()
        goods_tags: list[str] = [tag[0] for tag in results if tag]
        for tag, value in tags.items():
            localized_name: str = value["localized_name"]
            if tag not in goods_tags:
                connection.execute(SQLStatement.insert_eoc_goods_tag, args=(fid, tag, localized_name))


def run():
    options: dict[dict] = get_category_options_from_steam()
    for facet in options.values():
        insert_facet_and_tag_if_not_exist(facet)


if __name__ == '__main__':
    run()
