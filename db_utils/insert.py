import json, uuid, time
from peewee import IntegrityError, fn
from .db_declaration import CreationIndex, Creator, Creation, Raw, PicDownload, ExcellentWork, db, DYNAMIC_TYPE, load_ext
from .logger import logger

TOPIC_ARTICLE = "呜能为栗"
TOPIC_PIC_UMY = "图崽场"
TOPIC_PIC_MERRY = "羊皮书"


def save_pic(url, width=None, height=None):
    # 设置大小
    if width==None and height==None:
        pic_url = url
        ext = url.split(".")[-1]
    elif width!=None and height==None:
        pic_url = "{:s}@{:d}w.webp".format(url, width)
        ext = "webp"
    else:
        pic_url = "{:s}@{:d}h.webp".format(url, height)
        ext = "webp"
    name = uuid.uuid4().hex + "." + ext
    PicDownload.create(url=pic_url, file=name)
    logger.debug("已添加一张图片 {}".format(pic_url))
    return name

def serialize_tag(tags):
    return " ".join(tags)

def identify_video_category(data):
    '''
    自动识别视频的分类，按优先级排序
    手书、动画-animation: title intro tags中包含“手书”
    鬼畜-remix: title intro tags中包含“鬼畜”
    MMD-mmd: title intro tags中包含“MMD”
    歌曲切片-song: title intro tags中包含“歌”
    直播切片-cut: title intro tags中包含“切片”
    否则为None
    '''
    category_dict = {
        "animation": ["手书"],
        "remix": ["鬼畜"],
        "mmd": ["MMD"],
        "song": ["歌", "唱"],
        "cut": ["切片", "剪辑", "羊肉片"],
    }
    content = data["title"] + data["intro"] + serialize_tag(data["tags"])
    for k in category_dict:
        for key_word in category_dict[k]:
            if content.find(key_word) >= 0:
                return k
    return None


def update_creator(row, last_update_info):
    data = {
        "uid": row["desc"]["user_profile"]["info"]["uid"],
        "name": row["desc"]["user_profile"]["info"]["uname"],
        "face": {
            "url": row["desc"]["user_profile"]["info"]["face"],
            "file": None
        },
        "intro": row["desc"]["user_profile"]["sign"],
        "last_update_time": row["desc"]["timestamp"],
        "last_update_info": last_update_info
    }
    # 查找是否存在
    users = Creator.select().where(Creator.uid == data["uid"])
    if len(users) == 0:
        # 不存在则创建
        # 更新头像文件
        data["face"]["file"] = save_pic(data["face"]["url"])
        data["video_num"] = 0
        data["picture_num"] = 0
        data["article_num"] = 0
        user = Creator.create(**data)
        logger.debug("创建新up {}".format(data["name"]))
    else:
        # 存在则检测最新发布更新
        # 若有更新则同时检测头像和名字
        user = users[0]
        if user.last_update_time.timestamp() < data["last_update_time"]:
            user.last_update_time = data["last_update_time"]
            user.last_update_info = data["last_update_info"]
            if user.name != data["name"]:
                user.name = data["name"]
            if user.face["url"] != data["face"]["url"]:
                user.face["url"] = data["face"]["url"]
                # 更新头像文件
                data["face"]["file"] = save_pic(data["face"]["url"])
            logger.debug("更新up {}".format(data["name"]))
    # 更新发布的作品数据
    if last_update_info["category"] == "video":
        user.video_num = user.video_num + 1
    elif last_update_info["category"] == "picture":
        user.picture_num = user.picture_num + 1
    elif last_update_info["category"] == "article":
        user.article_num = user.article_num + 1
    user.save()

def insert_normal(row):
    card = json.loads(row["card"])
    # 找到话题
    tags = []
    for tag in row["display"]["topic_info"]["topic_details"]:
        tags.append(tag["topic_name"])
    # 记录图片 宽窄最高500px
    pics = []
    for pic in card["item"]["pictures"]:
        if pic["img_height"] < 500 and pic["img_width"] < 500:
            pic_name = save_pic(pic["img_src"])
        elif pic["img_height"] > pic["img_width"]:
            pic_name = save_pic(pic["img_src"], height=500)
        else:
            pic_name = save_pic(pic["img_src"], width=500)
        pics.append({"url": pic["img_src"], "file": pic_name})
    # 结构化数据
    data = {
        "type": DYNAMIC_TYPE["dynamic"],
        "dynamic_id": row["desc"]["dynamic_id"],
        "id": row["desc"]["dynamic_id"],
        "creator_uid": row["desc"]["user_profile"]["info"]["uid"],
        "time": row["desc"]["timestamp"],
        "info": {
            "content": card["item"]["description"],
            "tags": tags,
        },
        "pics": pics,
        "category": None,
        "sub_category": None,
        "display": True,
        "view_data": {
            "view": row["desc"]["view"],
            "repost": row["desc"]["repost"],
            "like": row["desc"]["like"],
            "comment": row["desc"]["comment"],
            "update_time": int(time.time())
        }
    }
    index_data = {
        "rowid": data["dynamic_id"],
        "title": "", 
        "content": data["info"]["content"], 
        "tags": serialize_tag(tags)
    }
    # 判定分类
    if TOPIC_ARTICLE in data["info"]["tags"]:
        data["category"] = "article"
    elif TOPIC_PIC_UMY in data["info"]["tags"]:
        data["category"] = "picture"
        if TOPIC_PIC_MERRY in data["info"]["tags"]:
            data["sub_category"] = "both"
        else:
            data["sub_category"] = "umy"
    elif TOPIC_PIC_MERRY in data["info"]["tags"]:
        data["category"] = "picture"
        data["sub_category"] = "merry"
    else:
        data["display"] = False
    # 更新up主
    if data["display"]:
        update_info = {
            "category": data["category"], 
            "content": data["info"]["content"]
        }
        update_creator(row, update_info)
    # 插入数据库
    Creation.create(**data)
    CreationIndex.create(**index_data)
    logger.debug("已创建图片动态 动态id:{}".format(data["dynamic_id"]))
    return "Add new picture dynamic, id:{}".format(data["dynamic_id"])

def insert_text_normal(row):
    card = json.loads(row["card"])
    # 找到话题
    tags = []
    for tag in row["display"]["topic_info"]["topic_details"]:
        tags.append(tag["topic_name"])
    # 结构化数据
    data = {
        "type": DYNAMIC_TYPE["dynamic"],
        "dynamic_id": row["desc"]["dynamic_id"],
        "id": row["desc"]["dynamic_id"],
        "creator_uid": row["desc"]["user_profile"]["info"]["uid"],
        "time": row["desc"]["timestamp"],
        "info": {
            "content": card["item"]["content"],
            "tags": tags,
        },
        "pics": [],
        "category": None,
        "sub_category": None,
        "display": True,
        "view_data": {
            "view": row["desc"]["view"],
            "repost": row["desc"]["repost"],
            "like": row["desc"]["like"],
            "comment": row["desc"]["comment"],
            "update_time": int(time.time())
        }
    }
    index_data = {
        "rowid": data["dynamic_id"],
        "title": "", 
        "content": data["info"]["content"], 
        "tags": serialize_tag(tags)
    }
    # 判定分类 仅文类被记录
    if TOPIC_ARTICLE in data["info"]["tags"]:
        data["category"] = "article"
    else:
        data["display"] = False
    # 更新up主
    if data["display"]:
        update_info = {
            "category": data["category"], 
            "content": data["info"]["content"]
        }
        update_creator(row, update_info)
    # 插入数据库
    Creation.create(**data)
    CreationIndex.create(**index_data)
    logger.debug("已创建文字动态 动态id:{}".format(data["dynamic_id"]))
    return "Add new text dynamic, id:{}".format(data["dynamic_id"])

def insert_video(row):
    try:
        card = json.loads(row["card"])
        # 找到话题
        tags = []
        for tag in row["display"]["topic_info"]["topic_details"]:
            tags.append(tag["topic_name"])
        # 记录封面
        pic_name = save_pic(card["pic"], width=500)
        # 结构化数据
        data = {
            "type": DYNAMIC_TYPE["video"],
            "dynamic_id": row["desc"]["dynamic_id"],
            "id": row["desc"]["bvid"],
            "creator_uid": row["desc"]["user_profile"]["info"]["uid"],
            "time": row["desc"]["timestamp"],
            "is_owner": True,
            "info": {
                "title": card["title"],
                "intro": card["desc"],
                "tags": tags,
            },
            "pics": [{
                "url": card["pic"],
                "file": pic_name
            }],
            "category": "video",
            "display": True,
            "view_data": {
                "view": row["desc"]["view"],
                "repost": row["desc"]["repost"],
                "like": row["desc"]["like"],
                "update_time": int(time.time())
            }
        }
        index_data = {
            "rowid": data["dynamic_id"],
            "title": data["info"]["title"], 
            "content": data["info"]["intro"], 
            "tags": serialize_tag(tags)
        }
        # 判定是否是拥有者
        if data["creator_uid"] != card["owner"]["mid"]:
            data["is_owner"] = False
    except KeyError:
        logger.warning("错误动态格式 动态id:{}".format(row["desc"]["dynamic_id"]))
        db.rollback()
        return    
    # 判定分类 这里可以做智能判定？
    data["sub_category"] = identify_video_category(data["info"])
    # 更新up主
    if data["display"]:
        update_info = {
            "category": "video", 
            "content": data["info"]["title"]
        }
        update_creator(row, update_info)
    # 插入数据库
    Creation.create(**data)
    CreationIndex.create(**index_data)
    logger.debug("已创建视频 bvid:{}".format(data["id"]))
    return "Add new video, bvid:{}".format(data["id"])

def insert_article(row):
    card = json.loads(row["card"])
    # 找到话题
    tags = []
    for tag in row["display"]["topic_info"]["topic_details"]:
        tags.append(tag["topic_name"])
    # 记录图片 宽窄最高500px
    pics = []
    if len(card["banner_url"])>0:
        pic_name = save_pic(card["banner_url"], width=500)
        pics.append({"url": card["banner_url"], "file": pic_name})
    for pic in card["image_urls"]:
        pic_name = save_pic(pic, width=500)
        pics.append({"url": pic, "file": pic_name})
    # 结构化数据
    data = {
        "type": DYNAMIC_TYPE["article"],
        "dynamic_id": row["desc"]["dynamic_id"],
        "id": row["desc"]["rid"],
        "creator_uid": row["desc"]["user_profile"]["info"]["uid"],
        "time": row["desc"]["timestamp"],
        "info": {
            "title": card["title"],
            "intro": card["summary"],
            "words": card["words"],
            "tags": tags,
        },
        "pics": pics,
        "category": "article",
        "display": True,
        "view_data": {
            "view": row["desc"]["view"],
            "repost": row["desc"]["repost"],
            "like": row["desc"]["like"],
            "update_time": int(time.time())
        }
    }
    index_data = {
        "rowid": data["dynamic_id"],
        "title": data["info"]["title"], 
        "content": data["info"]["intro"], 
        "tags": serialize_tag(tags)
    }
    # 判定分类 这里可以做智能判定？
    # 更新up主
    if data["display"]:
        update_info = {
            "category": "article", 
            "content": data["info"]["title"]
        }
        update_creator(row, update_info)
    # 插入数据库
    Creation.create(**data)
    CreationIndex.create(**index_data)
    logger.debug("已创建专栏 cvid:{}".format(data["id"]))
    return "Add new article, cvid:{}".format(data["id"])

def insert_one_dynamic(row):
    # 载入分词库
    load_ext()
    # 建立事务
    with db.atomic():
        # 插入raw数据 提取类型和id 重复则退出
        data = {
            "dynamic_id": row["desc"]["dynamic_id"],
            "type": row["desc"]["type"],
            "raw": row
        }
        try:
            Raw.create(**data)
            logger.debug("新动态 动态id:{}".format(data["dynamic_id"]))
        except IntegrityError:
            logger.debug("重复动态 动态id:{}".format(data["dynamic_id"]))
            return "Duplicated dynamic id."

        # 判定类型，仅包含1, 2, 4, 8, 64
        if data["type"] == 1:
            # 转发动态
            return insert_text_normal(row)
        elif data["type"] == 2:
            # 带图动态
            return insert_normal(row)
        elif data["type"] == 4:
            #纯文字动态
            return insert_text_normal(row)
        elif data["type"] == 8:
            #视频发布动态
            return insert_video(row)
        elif data["type"] == 64:
            #专栏发布动态
            return insert_article(row)


def excellent_creation(
    dynamic_id,
    reason,
    time
):
    '''
    添加优秀作品
    reason: 理由
    time: 时间戳，评选时间
    '''
    # 先找有没有对应的作品
    row = Creation.get_or_none(Creation.dynamic_id==int(dynamic_id))
    if row==None:
        return "No such dynamic id."
    # 插入作品
    data = {
        "dynamic_id": dynamic_id,
        "reason": reason,
        "time": time
    }
    try:
        ExcellentWork.create(**data)
    except IntegrityError:
        logger.debug("重复优秀作品 动态id:{}".format(data["dynamic_id"]))
        return "Duplicated dynamic id."
    except Exception as e:
        return repr(e)
    logger.debug("新优秀作品 动态id:{}".format(data["dynamic_id"]))
    return "Success."

'''
with open("umy_main.json", "r", encoding="utf8") as f:
    l = json.loads(f.read())
for i in l:
    insert_one_dynamic(i)





out = {
    1: [], #转发别人动态
    2: [], #带图动态
    4: [], #纯文字动态
    8: [], #视频发布动态
    64: [], #专栏发布动态
    2048: [] #推荐装扮动态
}
for i in l:
    out[i["desc"]["type"]].append(i)

for i in out.keys():
    with open("umy_main_{}.json".format(i), "w", encoding="utf8") as f:
        f.write(json.dumps(out[i], ensure_ascii=False))

print(len(l))
for i in out:
    print(len(out[i]))



out = set()
for i in l:
    out.add(i["desc"]["status"])
print(out)
'''
