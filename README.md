# Bilibili Dynamic Storage
存储b站话题内的动态数据，分成带图的、纯文字、专栏、视频几类。建立全文搜索数据库便于搜索。自动下载缩略图。根据MeUmy的二创tag进行分类。是MeUmy草原平时时空的后端哒！

## 话题的api

历史列表
```
{
    "url": "https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_history",
    "params": {
        "topic_name": "话题名字",
        "offset_dynamic_id": 0
    }
}
```

热门列表
```
{
    "url": "https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_new",
    "params": {
        "topic_id": "话题id"
    }
}
```

## spider.py
topic的爬虫，定时爬取在数据库里设定好的topic数据，存入数据库。

## web_interface.py
flask服务端，验证由`api_schema.json`定义的接口，并进行数据库查询操作。

## db_utils/db_declaration.py
使用sqlite和peewee，定义了数据库结构。使用fts5作为全文搜索引擎，并使用了https://github.com/wangfenjin/simple作为中文分词插件。