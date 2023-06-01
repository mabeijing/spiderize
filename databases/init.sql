CREATE
DATABASE `tms_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;


show
variables like "%time_zone%";


-- auto-generated definition
create table eoc_goods_category
(
    id               bigint auto_increment comment '主键id'
        primary key,
    appid            bigint       not null comment 'steam的id',
    classid          bigint       not null comment '分类id',
    instanceid       bigint null comment '实例id',
    market_hash_name varchar(200) null comment '市场英文名称',
    market_name      varchar(200) null comment '市场名称',
    name             varchar(200) not null comment '饰品名称',
    icon_url         varchar(1000) null comment 'icon地址',
    quality          varchar(50) null comment '质量',
    rarity           varchar(50) null comment '稀有',
    type             varchar(50) null comment '饰品类型',
    weapon           varchar(100) null comment '武器',
    skin             varchar(100) null comment '皮肤',
    `group`          varchar(100) null comment '组别',
    `desc`           text null comment '描述',
    tips             varchar(500) null comment '口语文字',
    appearance       varchar(50) null comment '外观',
    price            decimal(9, 2) null comment '展示价格',
    stock            bigint null comment '库存',
    stamp            json null comment '武器关联饰品印花',
    price_trend      json null comment '价格趋势，关联classid',
    collection       varchar(200) null comment '收藏品',
    competitor       varchar(200) null comment '选手',
    team             varchar(200) null comment '战队',
    tournament       varchar(200) null comment '锦标赛',
    sticker_type     varchar(200) null comment '印花类型',
    sticker_color    varchar(200) null comment '印花颜色',
    spray_type       varchar(200) null comment '涂鸦类型',
    spray_color      varchar(200) null comment '涂鸦颜色',
    patch_type       varchar(200) null comment '布章类型',
    patch_color      varchar(200) null comment '布章颜色',
    create_by        bigint null comment '创建人',
    create_time      datetime default CURRENT_TIMESTAMP null comment '创建时间'
) comment '饰品分类表' charset = utf8mb3
                         row_format = DYNAMIC;


-- auto-generated definition
create table eoc_goods_facet
(
    id             bigint auto_increment
        primary key,
    name           varchar(255) null,
    localized_name varchar(255) null
) collate = utf8mb4_bin;


-- auto-generated definition
create table eoc_goods_spu
(
    id               bigint auto_increment comment '主键id'
        primary key,
    classid          bigint                   not null comment '道具分类id，代表一类基础属性相同的道具',
    name             varchar(255)  default '' not null comment '道具名称，简称，比如 “双持贝瑞塔 | 钴蓝石英”',
    name_color       varchar(255)  default '' not null,
    market_name      varchar(255)  default '' not null comment '道具市场通称，一般会在简称基础上加上属性修饰词，比如 "双持贝瑞塔 | 钴蓝石英 (久经沙场)"',
    market_hash_name varchar(255)  default '' not null comment '道具的市场hash名称',
    icon_url         varchar(1000) default '' not null comment '从steam库存接口获取到的道具的图片url cdn图片后缀地址',
    icon_url_large   varchar(1000) default '' not null comment '与icon_url同理，不过是大尺寸的图片，此属性有可能为空',
    descriptions     varchar(5000) null,
    price            decimal(9, 2)            not null comment '价格',
    create_by        bigint null comment '创建人',
    create_time      datetime      default CURRENT_TIMESTAMP null comment '创建时间',
    update_by        bigint null comment '更新人',
    update_time      datetime null comment '更新时间'
) comment '饰品规格SPU表';

create index cls_id
    on eoc_goods_spu (classid);

create index market_name
    on eoc_goods_spu (market_hash_name);


-- auto-generated definition
create table eoc_goods_spu_price_trend
(
    id          bigint auto_increment comment '主键id'
        primary key,
    spu_id      bigint         not null comment '规格id',
    time        date           not null comment '日期',
    price       decimal(10, 2) not null comment '价格',
    quantity    int null comment '数量',
    create_time datetime default CURRENT_TIMESTAMP null comment '创建时间'
) collate = utf8mb4_bin
    row_format = DYNAMIC;


-- auto-generated definition
create table eoc_goods_spu_tag
(
    id     bigint auto_increment
        primary key,
    spu_id bigint not null,
    tag_id bigint not null
) collate = utf8mb4_bin;


-- auto-generated definition
create table eoc_goods_tag
(
    id             bigint auto_increment
        primary key,
    facet_id       bigint                  not null,
    name           varchar(255) default '' not null,
    localized_name varchar(255) default '' not null
) collate = utf8mb4_bin;

