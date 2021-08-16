# Bilibili Dynamic Storge
存储b站话题内的动态数据，分成带图的、纯文字、专栏、视频几类。建立全文搜索数据库便于搜索。自动下载缩略图。根据MeUmy的二创tag进行分类。

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