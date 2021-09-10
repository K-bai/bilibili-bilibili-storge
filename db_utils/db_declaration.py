from peewee import *
import json, functools, platform
from playhouse.sqlite_ext import FTS5Model, RowIDField, JSONField, SearchField, SqliteExtDatabase

my_json_dumps = functools.partial(json.dumps, ensure_ascii=False)

db = SqliteExtDatabase('creation.db', pragmas=(
    ('cache_size', -1024 * 64),  # 64MB page-cache.
    ('journal_mode', 'wal'))) # Use WAL-mode (you should always use this!).

DYNAMIC_TYPE = {
    "video": 1,
    "article": 2,
    "dynamic": 3,
}


PIC_DOWNLOAD_STATUS = {
    "waiting": 0,
    "downloaded": 1,
    "skipped": 2
}


# 加载中文分词库
def load_ext():
    SQLITE_EXT_DIR = "sqlite_ext/"
    if platform.system() == "Windows":
        db.load_extension(SQLITE_EXT_DIR + "simple.dll")
    elif platform.system() == "Linux":
        db.load_extension(SQLITE_EXT_DIR + "libsimple.so")
    else:
        raise Exception

class BaseModel(Model):
    class Meta:
        database = db

# up主数据
class Creator(BaseModel):
    uid = IntegerField(primary_key = True) # up主uid
    name = TextField(null = True) # up主名字
    face = JSONField(json_dumps = my_json_dumps, null = True) # up主头像
    intro = TextField(null = True) # up主简介
    last_update_time = TimestampField(null = True) # 最新发布的时间
    last_update_info = JSONField(json_dumps = my_json_dumps, null = True, default = {
        "category": "", 
        "content": ""
    }) # 最新发布内容 包括类型、标题
    video_num = IntegerField(null = True) # 已发布的视频数量
    picture_num = IntegerField(null = True) # 已发布的图片数量
    article_num = IntegerField(null = True) # 已发布的文章数量

# 作品数据表
class Creation(BaseModel):
    type = IntegerField() # 二创分类(专栏、动态、视频)
    dynamic_id = IntegerField(primary_key=True) # 动态号
    id = TextField(index=True) # 动态、BV、CV号
    creator_uid = IntegerField(index=True) # up主uid
    time = TimestampField(index=True) # 发布时间
    is_owner = BooleanField(default=True) # 是否是拥有者
    info = JSONField(json_dumps = my_json_dumps) # 专栏信息，包括标题、预览文字、字数、tag列表
    pics = JSONField(json_dumps = my_json_dumps, default = [{"url": "", "file": ""}]) # 专栏封面列表
    category = TextField(null = True) # 主分类
    sub_category = TextField(null = True) # 次分类

    display = BooleanField(default = True) # 是否显示在列表里
    checked = BooleanField(default = False) # 是否经过审核
    note = TextField(null = True, default = None) # 管理员给的备注
    view_data = JSONField(json_dumps = my_json_dumps, default = {
        "view":0, "repost":0, "like":0, "update_time":None
    }) # 专栏观看数据，包括转发、查看、点赞、更新时间

# 获取的纯数据
class Raw(BaseModel):
    dynamic_id = IntegerField(primary_key = True) # 动态id
    type = IntegerField() # 动态类别（1转发别人动态 2带图动态 4纯文字动态 8视频发布动态 64专栏发布动态 2048推荐装扮动态）
    raw = JSONField(json_dumps = my_json_dumps) # 数据内容

# MeUmy推荐的优秀作品
class ExcellentWork(BaseModel):
    dynamic_id = IntegerField(primary_key = True) # 动态id
    time = TimestampField(index = True) # 推荐时间
    reason = TextField(null = True) # 推荐理由

# 图片下载记录
class PicDownload(BaseModel):
    url = TextField() # 图片原始地址
    file = TextField() # 下载后文件名
    is_downloaded = IntegerField(default=PIC_DOWNLOAD_STATUS["waiting"]) # 是否已下载

# tag爬虫记录
class SpiderLog(BaseModel):
    tag = TextField() # tag名称
    tag_id = IntegerField() # tag id
    last_dynamic_time = TimestampField(default=946656000) # 爬取的最新一条动态的发送时间

# 分类记录
class CategoryList(BaseModel):
    main = TextField() # 主分类 仅包括 video picture article
    sub = TextField() # 次要分类
    description = TextField() # 分类描述

# 信息全文索引
class CreationIndex(FTS5Model):
    rowid = RowIDField() # Creation表的rowid
    title = SearchField() # Creation标题
    content = SearchField() # Creation内容
    tags = SearchField() # Creation tags
    class Meta:
        database = db
        options = {
            "tokenize": "simple 0" # 使用附加的simple分词库并取消拼音
            }
