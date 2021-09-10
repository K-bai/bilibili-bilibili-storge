from logging import info
from peewee import fn, SQL
from .db_declaration import CreationIndex, Creator, Creation, CategoryList, ExcellentWork, DYNAMIC_TYPE, load_ext
from .logger import logger

LINK_VIDEO = "https://www.bilibili.com/video/{:s}"
LINK_DYNAMIC = "https://t.bilibili.com/{:s}"
LINK_ARTICLE = "https://www.bilibili.com/read/cv{:s}"

LINK_PICTURE = "/pics/{:s}"

class DataMappingAdmin:
    def creation(d):
        if d.type == DYNAMIC_TYPE["video"]:
            return DataMappingAdmin.video(d)
        elif d.type == DYNAMIC_TYPE["article"]:
            return DataMappingAdmin.article(d)
        elif d.type == DYNAMIC_TYPE["dynamic"]:
            if d.category == "picture":
                return DataMappingAdmin.picture(d)
            elif d.category == "article":
                return DataMappingAdmin.dynamic_article(d)
    
    def common(d):
        return {
            "rid": d.id,
            "dynamic_id": str(d.dynamic_id),
            "time": d.time.timestamp(),
            "category": d.sub_category,
            "creator": {
                "name": d.creator.name,
                "uid": d.creator_uid
            },
            "display": d.display,
            "checked": d.checked
        }

    def video(d):
        rst = {
            "type": "video",
            "title": d.info["title"],
            "info": d.info["intro"],
            "pics": [d.pics[0]["file"]]
        }
        common = DataMappingAdmin.common(d)
        common.update(rst)
        return common
    
    def picture(d):
        pics = []
        for p in d.pics:
            pics.append(p["file"])
        if len(pics) == 0:
            pics.append("")
        rst = {
            "type": "picture",
            "title": "",
            "info": d.info["content"],
            "pics": pics
        }
        common = DataMappingAdmin.common(d)
        common.update(rst)
        return common
    
    def article(d):
        pics = []
        for p in d.pics:
            pics.append(p["file"])
        if len(pics) == 0:
            pics.append("")
        rst = {
            "type": "article",
            "title": d.info["title"],
            "info": d.info["intro"],
            "pics": pics
        }
        common = DataMappingAdmin.common(d)
        common.update(rst)
        return common
    
    def dynamic_article(d):
        pics = []
        for p in d.pics:
            pics.append(p["file"])
        if len(pics) == 0:
            pics.append("")
        rst = {
            "type": "article",
            "title": "",
            "info": d.info["content"],
            "pics": pics
        }
        common = DataMappingAdmin.common(d)
        common.update(rst)
        return common
    
    def excellent_work(d):
        rst = {
            "select_time": d.select_time.timestamp(),
            "reason": d.reason
        }
        creation = DataMappingAdmin.creation(d.creation)
        creation.update(rst)
        return creation


class DataMapping:
    def creation(d):
        if d.type == DYNAMIC_TYPE["video"]:
            return DataMapping.video(d)
        elif d.type == DYNAMIC_TYPE["article"]:
            return DataMapping.article(d)
        elif d.type == DYNAMIC_TYPE["dynamic"]:
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
            "authUid": d.creator_uid,
            "time": d.time.timestamp(),
            "imgAddr": LINK_PICTURE.format(d.pics[0]["file"]),
            "bvid": LINK_VIDEO.format(d.id)
        }
    
    def picture(d):
        pics = []
        for p in d.pics:
            pics.append(LINK_PICTURE.format(p["file"]))
        if len(pics) == 0:
            pics.append("")
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
    
    def article(d):
        pics = []
        for p in d.pics:
            pics.append(LINK_PICTURE.format(p["file"]))
        if len(pics) == 0:
            pics.append("")
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
    
    def dynamic_article(d):
        pics = []
        for p in d.pics:
            pics.append(LINK_PICTURE.format(p["file"]))
        if len(pics) == 0:
            pics.append("")
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
    
    def excellent_work(d):
        creation = DataMapping.creation(d.creation)
        return creation


def get_creation_list(
    type="video",
    sub_category=None,
    search_type=None,
    search_text=None,
    page=1,
    per_page=10,
    order="desc",
    order_by="time",
    start_time = None,
    end_time = None,
    dynamic_id = None,
    id = None,
    uid=None,
    display=None,
    is_owner=None,
    checked=None,
    admin_results=False
):
    # 类别
    if type in ["video", "picture", "article"]:
        type_filter = (Creation.category == type)
    elif type == "all":
        type_filter = (Creation.category.in_(["video", "picture", "article"]))
    elif type == "none":
        type_filter = True
    # 子分类
    if sub_category:
        sub_category_filter = (Creation.sub_category == sub_category)
    else:
        sub_category_filter = True
    # 搜索关键词
    if search_type == "creator_name":
        search_name_filter = Creator.name.contains(search_text.strip())
    else:
        search_name_filter = True
    # 排序依据
    if order_by == "rank" and search_type == "content":
        order_by_sign = CreationIndex.rank(25, 5, 1)
    elif order_by == "time":
        order_by_sign = Creation.time
    elif order_by == "random":
        order_by_sign = fn.Random()
    else:
        order_by_sign = Creation.time
    # 顺序
    if order == "desc":
        order_sign = order_by_sign.desc()
    else:
        order_sign = order_by_sign
    # 时间范围
    if start_time:
        start_time_filter = (Creation.time >= start_time)
    else:
        start_time_filter = True
    if end_time:
        end_time_filter = (Creation.time <= end_time)
    else:
        end_time_filter = True
    # 特定up
    if uid:
        uid_filter = (Creation.creator_uid == uid)
    else:
        uid_filter = True
    # 特定动态id int
    if dynamic_id:
        dynamic_id_filter = (Creation.dynamic_id == int(dynamic_id))
    else:
        dynamic_id_filter = True
    # 特定id string
    if id:
        id_filter = (Creation.id == id)
    else:
        id_filter = True
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
    if search_text != None and search_type == "content":
        # 存在搜索词
        load_ext()
        data = (Creation
            .select(Creation, Creator.name)
            .join(Creator, on=(Creation.creator_uid == Creator.uid), attr="creator")
            .join(CreationIndex, on=(Creation.dynamic_id == CreationIndex.rowid), attr="index")
            .where(
                type_filter, 
                uid_filter, 
                sub_category_filter, 
                start_time_filter,
                end_time_filter,
                is_owner_filter,
                display_filter, 
                checked_filter, 
                dynamic_id_filter, 
                id_filter,
                CreationIndex.match(fn.simple_query(search_text.strip()))
            )
            .order_by(order_sign)
        )
        # 构造输出
        count = len(data)
        out = []
        for idx in range((page-1)*per_page, page*per_page):
            if idx >= count:
                break
            out.append(data[idx])
        data = out
    else:
        # 不存在搜索词 或通过姓名搜索
        data = (Creation
            .select(Creation, Creator.name, fn.Count(Creation.dynamic_id).over().alias("count"))
            .join(Creator, on=(Creation.creator_uid == Creator.uid), attr="creator")
            .where(
                type_filter, 
                uid_filter, 
                sub_category_filter, 
                start_time_filter,
                end_time_filter,
                is_owner_filter,
                search_name_filter,
                display_filter, 
                checked_filter, 
                dynamic_id_filter, 
                id_filter,
            )
            .order_by(order_sign)
            .paginate(page, per_page)
        )
        if len(data)>0:
            count = data[0].count
        else:
            count = 0
    # 输出
    output = []
    for d in data:
        if admin_results:
            schema = DataMappingAdmin.creation(d)
        else:
            schema = DataMapping.creation(d)
        output.append(schema)
    return {"rst": output, "count": count}

def get_creator_list(
    page=1,
    per_page=10,
    search_text=None,
    search_type=None,
    order="desc",
    order_by="time"
):
    # 搜索类型和关键字
    if search_text and search_type:
        if search_type == "name":
            search_filter = Creator.name.contains(search_text)
        elif search_type == "uid":
            search_filter = (Creator.uid == search_text)
    else:
        search_filter = True
    # 排序依据
    if order_by == "time":
        order_by_sign = Creator.last_update_time
    elif order_by == "video_number":
        order_by_sign = Creator.video_num
    elif order_by == "picture_number":
        order_by_sign = Creator.picture_num
    elif order_by == "article_number":
        order_by_sign = Creator.article_num
    else:
        order_by_sign = Creator.last_update_time
    # 顺序
    if order == "desc":
        order_sign = order_by_sign.desc()
    else:
        order_sign = order_by_sign
    data = (Creator
        .select(Creator, fn.Count(Creator.uid).over().alias("count"))
        .where(
            search_filter,
            Creator.last_update_time != 0
        )
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

def get_excellent_work(admin_results=False):
    data = (ExcellentWork
        .select(
            Creation,
            Creator.name,
            ExcellentWork.time.alias("select_time"),
            ExcellentWork.reason
        )
        .join(Creation, on=(ExcellentWork.dynamic_id == Creation.dynamic_id), attr="creation")
        .join(Creator, on=(Creation.creator_uid == Creator.uid), attr="creator")
        .order_by(ExcellentWork.time.desc())
    )
    # 输出
    output = []
    for d in data:
        if admin_results:
            schema = DataMappingAdmin.excellent_work(d)
        else:
            schema = DataMapping.excellent_work(d)
        output.append(schema)
    count = len(output)
    return {"rst": output, "count": count}

def get_creator(uid):
    # 获取up信息
    data = (Creator.select().where(Creator.uid == uid))
    if len(data) == 0:
        return None
    schema = DataMapping.creator(data[0])
    return schema

def get_categorys(type):
    '''
    获取分类信息
    '''
    return list(CategoryList.select().where(CategoryList.main==type).dicts())