import json, jsonschema
from flask import Flask, request, abort, jsonify
import db_utils.select as select

with open("api_schema.json", "r") as f:
    SCHEMA = json.loads(f.read())


app = Flask(__name__)

@app.route("/api", methods=['POST'])
def api():
    data = request.json
    print(data)
    try:
        jsonschema.validate(data, SCHEMA)
    except jsonschema.exceptions.ValidationError:
        return jsonify({"MuHeader":{"msg": "Not a valid request."}})
    if "getWorks" in data.keys():
        type_dict = {
            "0": "video",
            "1": "picture",
            "2": "article",
            "3": "all"
        }
        if "searchWord" not in data["getWorks"].keys():
            sw = None
        elif data["getWorks"]["searchWord"] == "":
            sw = None
        else:
            sw = data["getWorks"]["searchWord"]
        ob = "rank" if sw else "time"
        params = {
            "type": type_dict[data["getWorks"]["workType"]],
            "sub_category": None,
            "search_text": sw,
            "page": data["getWorks"]["pageNum"],
            "per_page": 10,
            "order": "desc",
            "order_by": ob,
            "uid": None,
            "display": None,
            "is_owner": True,
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
        return jsonify(rst)
    elif "getAuthors" in data.keys():
        sw = None
        st = None
        if "searchWord" in data["getAuthors"].keys() and data["getAuthors"]["searchWord"] != "":
            if "searchType" in data["getAuthors"].keys():
                sw = data["getAuthors"]["searchWord"]
                if data["getAuthors"]["searchType"] == "0":
                    st = "name"
                else:
                    st = "uid"
        params = {
            "page": data["getAuthors"]["pageNum"],
            "per_page": 10,
            "search_text": sw,
            "search_type": st,
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
    elif "creator" in data.keys():
        return jsonify(select.get_creator(**data["creator"]))
    elif "getExcellentWorks" in data.keys():
        return jsonify({"MuHeader":{"msg": "success"}, "MuBody":[]})