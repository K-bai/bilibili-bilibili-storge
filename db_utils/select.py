from peewee import fn
from .db_declaration import CreationIndex, Creator, Creation, CREATION_TYPE, load_ext
from .logger import logger

LINK_VIDEO = "https://www.bilibili.com/video/{:s}"
LINK_DYNAMIC = "https://t.bilibili.com/{:s}"
LINK_ARTICLE = "https://www.bilibili.com/read/cv{:s}"

LINK_PICTURE = "http://parallel.meumy.club/{:s}"

class DataMapping:
    def creation(d):
        if d.type == CREATION_TYPE["video"]:
            return DataMapping.video(d)
        elif d.type == CREATION_TYPE["article"]:
            return DataMapping.article(d)
        elif d.type == CREATION_TYPE["dynamic"]:
            if d.category == "picture":
                return DataMapping.picture(d)
            elif d.category == "article":
                return DataMapping.dynamic_article(d)

    def video(d):
        return {
            "workType": "0",
            "workTitle": d.info["title"],
            "workText": d.info["intro"],
            "authName": d.creator.name,
            "time": d.time.timestamp(),
            "authUid": d.creator_uid,
            "imgAddr": LINK_PICTURE.format(d.pics[0]["file"]),
            "bvid": LINK_VIDEO.format(d.id)
        }
        return {
            "type": "video",
            "bvid": LINK_VIDEO.format(d.id),
            "creator_uid": d.creator_uid,
            "creator_name": d.creator.name,
            "time": d.time.timestamp(),
            "title": d.info["title"],
            "intro": d.info["intro"],
            "cover": LINK_PICTURE.format(d.pics[0]["file"]),
            "note": d.note
        }
    
    def picture(d):
        pics = []
        for p in d.pics:
            pics.append(LINK_PICTURE.format(p["file"]))
        return {
            "workType": "1",
            "workTitle": "",
            "workText": d.info["content"],
            "authName": d.creator.name,
            "time": d.time.timestamp(),
            "authUid": d.creator_uid,
            "imgAddr": pics[0],
            "dynamic_id": LINK_DYNAMIC.format(d.id),
        }
        return {
            "type": "dynamic",
            "dynamic_id": LINK_DYNAMIC.format(d.id),
            "creator_uid": d.creator_uid,
            "creator_name": d.creator.name,
            "time": d.time.timestamp(),
            "content": d.info["content"],
            "pics": pics,
            "note": d.note
        }
    
    def article(d):
        pics = []
        for p in d.pics:
            pics.append(LINK_PICTURE.format(p["file"]))
        return {
            "workType": "2",
            "workTitle": d.info["title"],
            "workText": d.info["intro"],
            "authName": d.creator.name,
            "time": d.time.timestamp(),
            "authUid": d.creator_uid,
            "imgAddr": pics[0],
            "cvid": LINK_ARTICLE.format(d.id),
        }
        return {
            "type": "article",
            "cvid": LINK_ARTICLE.format(d.id),
            "creator_uid": d.creator_uid,
            "creator_name": d.creator.name,
            "time": d.time.timestamp(),
            "title": d.info["title"],
            "intro": d.info["intro"],
            "words": d.info["words"],
            "pics": pics,
            "note": d.note
        }
    
    def dynamic_article(d):
        pics = []
        for p in d.pics:
            pics.append(LINK_PICTURE.format(p["file"]))
        return {
            "workType": "2",
            "workTitle": "",
            "workText": d.info["content"],
            "authName": d.creator.name,
            "time": d.time.timestamp(),
            "authUid": d.creator_uid,
            "imgAddr": pics[0],
            "dynamic_id": LINK_DYNAMIC.format(d.id),
        }
        return {
            "type": "dynamic_article",
            "dynamic_id": LINK_DYNAMIC.format(d.id),
            "creator_uid": d.creator_uid,
            "creator_name": d.creator.name,
            "time": d.time.timestamp(),
            "content": d.info["content"],
            "pics": pics,
            "note": d.note
        }
    
    def creator(d):
        category_dict = {
            "video": "0",
            "picture": "1",
            "article": "2"
        }
        return {
            "newWork": category_dict[d.last_update_info["category"]],
            "workTitle": d.last_update_info["content"],
            "authName": d.name,
            "time": d.last_update_time.timestamp(),
            "authUid": d.uid,
            "imgAddr": LINK_PICTURE.format(d.face["file"]),
            "vidNum": d.video_num,
            "imgNum": d.picture_num,
            "artNum": d.article_num
        }
        return {
            "uid": d.uid,
            "name": d.name,
            "face": LINK_PICTURE.format(d.face["file"]),
            "intro": d.intro,
            "last_update_time": d.last_update_time.timestamp(),
            "last_update_info": d.last_update_info,
            "video_list": [],
            "article_list": [],
            "picture_list": []
        }


def get_creation_list(
    type="video",
    sub_category=None,
    search_text=None,
    page=1,
    per_page=10,
    order="desc",
    order_by="time",
    uid=None,
    display=None,
    is_owner=None,
    checked=None
):
    # 类别
    if type == "video":
        type_filter = (Creation.type == CREATION_TYPE["video"])
    elif type == "picture":
        type_filter = ((Creation.type == CREATION_TYPE["dynamic"]) & (Creation.category == "picture"))
    elif type == "article":
        type_filter = (((Creation.type == CREATION_TYPE["dynamic"]) & (Creation.category == "article")) | (Creation.type == CREATION_TYPE["article"]))
    elif type == "all":
        type_filter = True
    # 子分类
    if sub_category:
        sub_category_filter = (Creation.sub_category == sub_category)
    else:
        sub_category_filter = True
    # 排序依据
    if order_by == "rank" and search_text != None:
        order_by_sign = CreationIndex.rank()
    elif order_by == "time":
        order_by_sign = Creation.time
    # 顺序
    if order == "desc":
        order_sign = order_by_sign.desc()
    else:
        order_sign = order_by_sign
    # 特定up
    if uid:
        uid_filter = (Creation.creator_uid == uid)
    else:
        uid_filter = True
    # 是否可显示
    if display == None:
        display_filter = True
    else:
        display_filter = (Creation.display == display)
    # 联合投稿是否是拥有者
    if is_owner == None:
        is_owner_filter = True
    else:
        is_owner_filter = (Creation.is_owner == is_owner)
    # 是否被审核
    if checked == None:
        checked_filter = True
    else:
        checked_filter = (Creation.checked == checked)
    # 获取数据
    if search_text != None:
        # 存在搜索词
        load_ext()
        data = (Creation
            .select(Creation, Creator.name, fn.Count(Creation.id).over().alias("count"))
            .join(Creator, on=(Creation.creator_uid == Creator.uid), attr="creator")
            .join(CreationIndex, on=(Creation.dynamic_id == CreationIndex.rowid), attr="index")
            .where(
                type_filter, 
                uid_filter, 
                sub_category_filter, 
                is_owner_filter,
                display_filter, 
                checked_filter, 
                CreationIndex.content.match(fn.simple_query(search_text))
            )
            .order_by(order_sign)
            .paginate(page, per_page))
    else:
        # 不存在搜索词
        data = (Creation
            .select(Creation, Creator.name, fn.Count(Creation.id).over().alias("count"))
            .join(Creator, on=(Creation.creator_uid == Creator.uid), attr="creator")
            .where(
                type_filter, 
                uid_filter, 
                sub_category_filter, 
                is_owner_filter,
                display_filter, 
                checked_filter
            )
            .order_by(order_sign)
            .paginate(page, per_page))
    # 输出
    output = []
    #print(data)
    for d in data:
        #print(d)
        schema = DataMapping.creation(d)
        output.append(schema)
    if len(data)>0:
        count = data[0].count
    else:
        count = 0
    return {"rst": output, "count": count}

def get_creator_list(
    page=1,
    per_page=10,
    search_text=None,
    search_type=None,
    order="desc"
):
    # 搜索类型和关键字
    if search_text and search_type:
        if search_type == "name":
            search_filter = Creator.name.contains(search_text)
        elif search_type == "uid":
            search_filter = (Creator.uid == int(search_text))
    else:
        search_filter = True

    # 顺序
    if order == "desc":
        order_sign = Creator.last_update_time.desc()
    else:
        order_sign = Creator.last_update_time
    data = (Creator
        .select(Creator, fn.Count(Creator.uid).over().alias("count"))
        .where(search_filter)
        .order_by(order_sign)
        .paginate(page, per_page))
    # 输出
    output = []
    for d in data:
        schema = DataMapping.creator(d)
        output.append(schema)
    if len(data)>0:
        count = data[0].count
    else:
        count = 0
    return {"rst": output, "count": count}

def get_creation(id):
    data = (Creation
        .select(Creation, Creator.name)
        .join(Creator, on=(Creation.creator_uid == Creator.uid), attr="creator")
        .where(Creation.is_owner == True, Creation.id == id)
        .limit(1))
    if len(data) == 0:
        return None
    else:
        return DataMapping.creation(data[0])


def get_creator(uid):
    # 获取up信息
    data = (Creator.select().where(Creator.uid == uid))
    if len(data) == 0:
        return None
    schema = DataMapping.creator(data[0])
    # 获取up创作信息
    #schema["video_list"] = get_creation_list(type="video", uid=uid, display=True)
    #schema["picture_list"] = get_creation_list(type="picture", uid=uid, display=True)
    #schema["article_list"] = get_creation_list(type="article", uid=uid, display=True)
    return schema
