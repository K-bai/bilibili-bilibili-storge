from peewee import fn
from .db_declaration import CategoryList, Creator, Creation, ExcellentWork
import datetime
from .logger import logger

def creation(
    dynamic_id,
    checked=None,
    display=None,
    sub_category=None
):
    # 获取对应row
    row = Creation.get_or_none(Creation.dynamic_id==int(dynamic_id))
    if row==None:
        return "No such id."
    # checked标志
    if checked != None:
        row.checked = checked
    # display标志
    if display != None:
        row.display = display
    # 分类
    if sub_category != None and row.category=="video":
        # 获取全部分类
        category_q = CategoryList.select().where(CategoryList.main==row.category)
        if len(category_q) != 0:
            category_list = [c.sub for c in category_q]
            if sub_category in category_list:
                row.sub_category = sub_category
            else:
                return "No such category."
        else:
            return "Wrong category."
    # 更新作品列表
    try:
        row.save()
    except Exception as e:
        return repr(e)
    logger.debug("已更新动态 动态id:{}".format(dynamic_id))
    # 更新用户列表
    return refresh_creator(row.creator_uid)

def refresh_creator(uid):
    '''
    刷新创作者的最新更新、作品数量
    '''
    creation_lastest = (Creation
        .select(
            Creation.time,
            Creation.type,
            Creation.category,
            Creation.info
        )
        .where(
            Creation.creator_uid == uid,
            Creation.display == True,
        )
        .order_by(Creation.time.desc())
        .limit(1)
    )
    # 如果没有作品 就隐藏这个人
    if len(creation_lastest)==0:
        creation_lastest = {
            "category": None,
            "time": 0
        }
    else:
        creation_lastest = creation_lastest.dicts()[0]
    video_number = (Creation
        .select(fn.Count().alias("count"))
        .where(
            Creation.creator_uid == uid,
            Creation.display == True,
            Creation.category == "video"
        )
        .group_by(Creation.creator_uid)
    )
    if len(video_number)==0:
        video_number = 0
    else:
        video_number = video_number[0].count
    picture_number = (Creation
        .select(fn.Count().alias("count"))
        .where(
            Creation.creator_uid == uid,
            Creation.display == True,
            Creation.category == "picture"
        )
        .group_by(Creation.creator_uid)
    )
    if len(picture_number)==0:
        picture_number = 0
    else:
        picture_number = picture_number[0].count
    article_number = (Creation
        .select(fn.Count().alias("count"))
        .where(
            Creation.creator_uid == uid,
            Creation.display == True,
            Creation.category == "article"
        )
        .group_by(Creation.creator_uid)
    )
    if len(article_number)==0:
        article_number = 0
    else:
        article_number = article_number[0].count
    # 设置最新作品
    if creation_lastest["category"]=="video":
        last_info = {
            "category": "video",
            "content": creation_lastest["info"]["title"]
        }
    elif creation_lastest["category"]=="article":
        if "content" in creation_lastest["info"]:
            content = creation_lastest["info"]["content"]
        else:
            content = creation_lastest["info"]["intro"]
        last_info = {
            "category": "article",
            "content": content
        }
    elif creation_lastest["category"]=="picture":
        last_info = {
            "category": "picture",
            "content": creation_lastest["info"]["content"]
        }
    else:
        last_info = {
            "category": "none",
            "content": None
        }
    update_dict = {
        Creator.video_num: video_number,
        Creator.article_num: article_number,
        Creator.picture_num: picture_number,
        Creator.last_update_info: last_info,
        Creator.last_update_time: creation_lastest["time"],
    }
    update_query = (Creator
        .update(update_dict)
        .where(Creator.uid==uid)
    )
    try:
        num = update_query.execute()
    except Exception as e:
        return repr(e)
    logger.debug("已刷新创作者信息 uid:{}".format(uid))
    return "Success."

def excellent_creation(dynamic_id):
    q = ExcellentWork.delete().where(ExcellentWork.dynamic_id == int(dynamic_id))
    try:
        n = q.execute()
    except Exception as e:
        return repr(e)
    if n > 0:
        logger.debug("已删除优秀作品 动态id:{}".format(dynamic_id))
        return "Success."
    else:
        return "No such dynamic_id."