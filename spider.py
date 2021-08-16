import requests, json, time
from logger import logger
from db_utils.db_declaration import SpiderLog
from db_utils.insert import insert_one_dynamic

class MeUmyApiException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def __str__(self):
        return "错误代码：%s, 信息：%s" % (self.code, self.msg)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.bilibili.com/",
    "Content-Type": "application/json"
}

st = {
    "url": "https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_history",
    "params": {
        "topic_name": "呜米",
        "offset_dynamic_id": 0
    }
}

st_new = {
    "url": "https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_new",
    "params": {
        "topic_id": "15932687"
    }
}


def get(api):
    time.sleep(1)
    req = requests.request("GET",**api, headers = DEFAULT_HEADERS)
    if req.ok:
        content = req.content.decode("utf8")
        if req.headers.get("content-length") == 0:
            return None
        con = json.loads(content)
        if con["code"] != 0:
            if "message" in con:
                msg = con["message"]
            elif "msg" in con:
                msg = con["msg"]
            else:
                msg = "请求失败，服务器未返回失败原因"
            raise MeUmyApiException(con["code"], msg)
        return con['data']
    else:
        raise MeUmyApiException(req.status_code, "网络错误")


def get_all_topic():
    # 遍历tag列表开始获取数据
    tag_list = list(SpiderLog.select().dicts())
    for tag_info in tag_list:
        st["params"]["topic_name"] = tag_info["tag"]
        st["params"]["offset_dynamic_id"] = 0
        last_time = tag_info["last_dynamic_time"].timestamp()

        continue_flag = True
        card_time_list = []
        logger.debug("开始爬取 <{:s}> 最新数据".format(tag_info["tag"]))
        # 获取最新数据
        st_new["params"]["topic_id"] = str(tag_info["tag_id"])
        data = get(st_new)
        logger.debug("已获取{:d}条数据".format(len(data["cards"])))
        logger.debug("开始爬取 <{:s}> 历史数据".format(tag_info["tag"]))
        # 遍历每一个卡片
        for card in data["cards"]:
            insert_one_dynamic(card)
        # 获取历史数据
        while continue_flag:
            # 获取数据
            data = get(st)
            # 到结尾则退出
            if "cards" not in data:
                logger.debug("已达 <{:s}> 结尾".format(tag_info["tag"]))
                break
            logger.debug("已获取{:d}条数据".format(len(data["cards"])))
            # 遍历每一个卡片
            for card in data["cards"]:
                current_card_time = card["desc"]["timestamp"]
                card_time_list.append(current_card_time)
                # 如果当前时间小于等于记录的时间，则跳出
                if current_card_time <= last_time:
                    logger.debug("已达 <{:s}> 上次爬取结果".format(tag_info["tag"]))
                    continue_flag = False
                    break
                # 否则加入数据库
                insert_one_dynamic(card)
            # 准备获取下一轮数据
            st["params"]["offset_dynamic_id"] = data["offset"]
        # 找到当前最新时间，输入数据库
        record = SpiderLog.get(SpiderLog.tag == tag_info["tag"])
        record.last_dynamic_time = max(card_time_list)
        record.save()
        # 休息10秒
        time.sleep(10)
    logger.debug("本轮爬取已结束")

get_all_topic()