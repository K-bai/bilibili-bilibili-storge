import json, jsonschema, sys
from flask import Flask, request, jsonify
import db_utils.select as select
import db_utils.update as update
import db_utils.insert as insert
from logger import logger
import spider

with open("api_schema.json", "r") as f:
    SCHEMA = json.loads(f.read())

ERROR_MSG_NOT_VALID = {"MuHeader":{"msg": "Not a valid request."}}
CREATION_TYPE = {
    "-1": "all",
    "0": "video",
    "1": "picture",
    "2": "article",
    "3": "all",
}
CREATION_SEARCH_TYPE = {
    "content": "0",
    "creator_name": "1",
    "uid": "2"
}
CREATION_VIDEO_SUB_CATEGORY = {
    "0": None,
    "1": "cut",
    "2": "song",
    "3": "remix",
    "4": "animation",
    "5": "mmd",
    "6": "other"
}
CREATOR_SEARCH_TYPE = {
    "name": "1",
    "uid": "2"
}

app = Flask(__name__)

def get_dynamic(dynamic_id):
    api = spider.get_api("dynamic_detail")
    api["params"]["dynamic_id"] = dynamic_id
    try:
        data = spider.get(api)
    except Exception as e:
        logger.warning("手动资源添加失败。错误信息：{}".format(sys.exc_info()[1]))
        return str(e)
    if "card" not in data:
        return "No such dynamic id."
    return insert.insert_one_dynamic(data["card"])



@app.route("/api", methods=['POST'])
def api():
    data = request.json
    logger.debug("请求: {}".format(repr(data)))
    try:
        jsonschema.validate(data, SCHEMA)
    except jsonschema.exceptions.ValidationError:
        return jsonify(ERROR_MSG_NOT_VALID)
    # 密码验证
    if "secret" in data:
        pass
    # 获取数据
    if "getWorks" in data:
        # 搜索词和排序依据
        search_word = None
        search_type = None
        uid = None
        is_owner = True
        order_reference = "time"
        order_sequence = "desc"
        # 判断搜索类型
        if "searchWord" in data["getWorks"] and "searchType" in data["getWorks"]:
            search_word_org = data["getWorks"]["searchWord"]
            search_type_org = data["getWorks"]["searchType"]
            if search_type_org==CREATION_SEARCH_TYPE["content"]:
                # 搜标题、简介、tag
                order_reference = "rank"
                order_sequence = "asc"
                search_type = "content"
                search_word = search_word_org
            elif search_type_org==CREATION_SEARCH_TYPE["creator_name"]:
                # 搜创作者名字
                search_type = "creator_name"
                search_word = search_word_org
            elif search_type_org==CREATION_SEARCH_TYPE["uid"]:
                # 确定uid
                try:
                    uid = int(search_word_org)
                    is_owner = None
                except ValueError:
                    return jsonify(ERROR_MSG_NOT_VALID)
        # 子分类
        sub_category = None
        if "classifyChoice" in data["getWorks"]:
            sub_category = CREATION_VIDEO_SUB_CATEGORY[data["getWorks"]["classifyChoice"]]
        params = {
            "type": CREATION_TYPE[data["getWorks"]["workType"]],
            "sub_category": sub_category,
            "search_type": search_type,
            "search_text": search_word,
            "page": data["getWorks"]["pageNum"],
            "per_page": 10,
            "order": order_sequence,
            "order_by": order_reference,
            "uid": uid,
            "display": True,
            "is_owner": is_owner,
            "checked": None
        }
        data = select.get_creation_list(**params)
        rst = {
            "MuHeader": {
                "msg": "success"
            },
            "MuBody": {
                "worksNum": data["count"],
                "worksList": data["rst"]
            }
        }
        logger.debug("返回: {}".format(repr(rst)))
        return jsonify(rst)
    elif "getAuthors" in data:
        search_word = None
        search_type = None
        # 判断搜索类型
        if "searchWord" in data["getAuthors"].keys() and "searchType" in data["getAuthors"].keys():
            search_word_org = data["getAuthors"]["searchWord"]
            search_type_org = data["getAuthors"]["searchType"]
            if search_type_org == CREATOR_SEARCH_TYPE["name"]:
                # 搜名字
                search_type = "name"
                search_word = search_word_org
            elif search_type_org == CREATOR_SEARCH_TYPE["uid"]:
                # 搜uid
                search_type = "uid"
                try:
                    search_word = int(search_word_org)
                except ValueError:
                    return jsonify(ERROR_MSG_NOT_VALID)
        params = {
            "page": data["getAuthors"]["pageNum"],
            "per_page": 10,
            "search_text": search_word,
            "search_type": search_type,
            "order": "desc"
        }
        data = select.get_creator_list(**params)
        rst = {
            "MuHeader": {
                "msg": "success"
            },
            "MuBody": {
                "authNum": data["count"],
                "worksList": data["rst"]
            }
        }
        return jsonify(rst)
    elif "getExcellentWorks" in data:
        data = select.get_excellent_work()
        rst = {
            "MuHeader": {"msg": "success"}, 
            "MuBody": {
                "worksNum": data["count"],
                "worksList": data["rst"]
            }
        }
        return jsonify(rst)
    elif "creation_list" in data:
        return jsonify(select.get_creation_list(
            **data["creation_list"],
            admin_results=True
        ))
    elif "excellent_creation_list" in data:
        return jsonify(select.get_excellent_work(
            admin_results=True
        ))
    elif "update_creation" in data:
        return jsonify({
            "msg": update.creation(**data["update_creation"])
        })
    elif "add_creation" in data:
        return jsonify({
            "msg": get_dynamic(**data["add_creation"])
        })
    elif "add_excellent_creation" in data:
        return jsonify({
            "msg": insert.excellent_creation(**data["add_excellent_creation"])
        })
    elif "delete_excellent_creation" in data:
        return jsonify({
            "msg": update.excellent_creation(**data["delete_excellent_creation"])
        })
    elif "get_categorys" in data:
        return jsonify(select.get_categorys(**data["get_categorys"]))
    elif "secret" in data:
        return jsonify({"msg": "Pass."})
    else:
        return jsonify({"msg": "?"})