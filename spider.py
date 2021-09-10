import requests, time, datetime, sys, copy
from logger import logger
from pic_download import download_all
from db_utils.db_declaration import SpiderLog
from db_utils.insert import insert_one_dynamic

class MeUmyApiException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def __str__(self):
        return "Code：{}, Message：{}".format(self.code, self.msg)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.bilibili.com/",
    "Content-Type": "application/json"
}

API = {
    "topic_history": {
        "url": "https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_history",
        "params": {
            "topic_name": "呜米",
            "offset_dynamic_id": 0
        }
    },
    "topic_new": {
        "url": "https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_new",
        "params": {
            "topic_name": "呜米"
        }
    },
    "dynamic_detail": {
        "url": "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail",
        "params": {
            "dynamic_id": "0"
        }
    }
}

def get_api(name):
    return copy.deepcopy(API[name])


def get(api):
    time.sleep(1)
    req = requests.request("GET",**api, headers = DEFAULT_HEADERS)
    if req.ok:
        con = req.json()
        if con["code"] != 0:
            if "message" in con:
                msg = con["message"]
            elif "msg" in con:
                msg = con["msg"]
            else:
                msg = "Api error with no reason."
            raise MeUmyApiException(con["code"], msg)
        return con['data']
    else:
        raise MeUmyApiException(req.status_code, "Network error.")


def get_all_topic(custom_last_time=None):
    '''
    爬取所有话题的数据
    custom_last_time: 截止时间，爬到哪个时间为止(s)
    '''
    logger.info("开始爬取话题数据")
    # 遍历tag列表开始获取数据
    tag_list = list(SpiderLog.select().dicts())
    for tag_info in tag_list:
        # 获取最新数据
        logger.debug("开始爬取 <{:s}> 最新数据".format(tag_info["tag"]))
        api = get_api("topic_new")
        api["params"]["topic_name"] = tag_info["tag"]
        try:
            data = get(api)
        except:
            logger.warning("网络错误 跳过本轮爬取过程。错误信息：{}".format(sys.exc_info()[1]))
            return
        logger.debug("已获取{:d}条数据".format(len(data["cards"])))
        # 遍历每一个卡片
        for card in data["cards"]:
            insert_one_dynamic(card)
        
        # 获取历史数据
        logger.debug("开始爬取 <{:s}> 历史数据".format(tag_info["tag"]))
        api = get_api("topic_history")
        api["params"]["topic_name"] = tag_info["tag"]
        api["params"]["offset_dynamic_id"] = 0
        last_time = tag_info["last_dynamic_time"].timestamp()
        if custom_last_time != None:
            last_time = custom_last_time
        continue_flag = True
        card_time_list = []
        while continue_flag:
            # 获取数据
            try:
                data = get(api)
            except:
                logger.warning("网络错误 跳过本轮爬取过程。错误信息：{}".format(sys.exc_info()[1]))
                return
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
            api["params"]["offset_dynamic_id"] = data["offset"]
        # 找到当前最新时间，输入数据库
        record = SpiderLog.get(SpiderLog.tag == tag_info["tag"])
        record.last_dynamic_time = max(card_time_list)
        record.save()
        # 休息10秒
        time.sleep(10)
    logger.info("本轮爬取已结束")


if __name__=="__main__":
    # 循环获取话题列表 间隔5分钟
    # get_all_topic(custom_last_time=datetime.datetime(2021, 8, 21).timestamp())
    INTERVAL = 5*60
    last_hour = datetime.datetime.today().time().hour
    while True:
        # 爬数据
        get_all_topic()
        # 下图片
        download_all()
        # 休息
        time.sleep(INTERVAL)
        # 到半天爬一次全天
        c_hour = datetime.datetime.today().time().hour
        if (c_hour == 11 or c_hour == 0) and last_hour != c_hour:
            yesterday = datetime.datetime.today()+datetime.timedelta(days=-1)
            get_all_topic(custom_last_time=yesterday.timestamp())
            download_all()
            last_hour = c_hour
            time.sleep(INTERVAL)