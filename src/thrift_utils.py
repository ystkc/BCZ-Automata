# thrift_utils

# RUN .\generator.bat
# thrift.exe -gen py d:/dotoro/project/#python/BCZ-Automata/src/thriftAPI


from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol

# 第一阶段：初始化
from src.thriftAPI.ttypes import *
from src.thriftAPI import *
from src.get_headers import getHeaders, bcz_info, get_device_str
from src.avatar import find_unique_id
from src.notice_parser import notice_storage_class
import requests
import ssl
import socket
import random
import gzip
import struct
import time
import json
import httpx
import certifi
import datetime
import sqlite3
import threading
import hashlib
import traceback
from fuzzywuzzy import process


class user_dict:
    def __init__(self):
        with open("user_cookie.json", 'r', encoding='utf-8') as f:
            self.user_dict_list = json.load(f)
            self.user_cookie = self.user_dict_list[0]['cookie'] # 默认第一个是咕咕
            self.user_config = self.user_dict_list[0]['config']
            self.modified = False
            # config中包含book_id
            # 410：中考词汇

    def add_user(self, access_token, unique_id, name, device_id):
        new_user = {
            "config": {
                "book_id": 410,
                "name": name,
                "unique_id": int(unique_id),
                "adv_id": 166102,
                "timezone": "Asia/Shanghai",
                "device_name_ext": "DCO-AL00-HUAWEI",
                "app_channel": "Rongyao"
            },
            "cookie": {
                "access_token": access_token,
                "app_name": "7060100",
                "device_name": "android%2FDCO-AL00-HUAWEI",
                "client_time": "",
                "device_id": device_id,
                "serial": "",
                "channel": "qq",
                "version": "12",
                "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
                "bcz_dmid": "2a16dfbb",
                "device_version": "12",
            }
        }
        self.user_dict_list.append(new_user)
        self.modified = True
        self.close()
    
    def del_user(self, unique_id):
        for i in range(len(self.user_dict_list)):
            if self.user_dict_list[i]['config']['unique_id'] == unique_id:
                del self.user_dict_list[i]
                self.modified = True
                break
        self.close()


    def close(self):
        ...
        # if self.modified:
            # with open("user_cookie.json", 'w', encoding='utf-8') as f:
            #     json.dump(self.user_dict_list, f, indent=4, ensure_ascii=False)
            # self.modified = False
    
    def find(self, unique_id):
        unique_id = int(unique_id)
        for i in range(len(self.user_dict_list)):
            if self.user_dict_list[i]['config']['unique_id'] == unique_id:
                return i, self.user_dict_list[i]
        return None, None
    
    def update_book_id(self, unique_id, book_id):
        _, user = self.find(unique_id)
        if user:
            user['config']['book_id'] = book_id
            self.modified = True


    def __del__(self):
        self.close()

user_dict_obj = user_dict()
user_dict_list = user_dict_obj.user_dict_list
user_cookie = user_dict_obj.user_cookie
user_config = user_dict_obj.user_config

report_json = [
    {# 0
        "event_id": "bcz_active_heartbeat_detail",
        "extra_info": "{\"period\":30,\"plan_type\":\"\"}",
        "log_time": "1725061321587",
        "product_id": "bcz_app",
        "stat_group": "heartbeat-common"
    },
    {# 1
        "event_id": "close-notify",
        "extra_info": "{\"adv_id\":\"100240167527175029\"}",
        "log_time": "1723850458343",
        "notify_title": "100240167527175029",
        "product_id": "bcz_app",
        "stat_group": "notify-popup"
    },
    {# 2
        "event_id": "enter-main-view",
        "log_time": "1725062704325",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 3
        "event_id": "homepage-book-adv-show",
        "extra_info": "{\"adv_id\":\"100213198904513909\",\"id\":\"100213198904513909\",\"book_id\":\"410\"}",
        "log_time": "1725062704865",
        "product_id": "bcz_app",
        "stat_group": "adv-common"
    },
    {# 4
        "event_id": "homepage-banner-show",
        "extra_info": "{\"adv_id\":\"166102\",\"id\":\"166102\"}",
        "log_time": "1725063038669",
        "product_id": "bcz_app",
        "stat_group": "adv-common"
    },
    {# 5
        "event_id": "push_curr_permission",
        "extra_info": "{\"status\":\"1\"}",
        "log_time": "1725063038837",
        "product_id": "bcz_app",
        "stat_group": "push-common"
    },
    {# 6
        "event_id": "cold_launch",
        "extra_info": "{\"device_id\":\"DCO-AL00-HUAWEI-8d946f2ddaf90f18\",\"channel\":\"Rongyao\"}",
        "log_time": "1725063036294",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 7 显示新单词
        "log_time": "1723850610168",
        "product_id": "bcz_app_h5",
        "stat_group": "study-detail-common",
        "event_id": "strategy_study_enter",
        "extra_info": "{\"topic_id\":8741,\"strategy_id\":\"q1\",\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 8 用户选择
        "log_time": "1723850603106",
        "product_id": "bcz_app_h5",
        "stat_group": "study-detail-common",
        "event_id": "choose_in_recite_click",
        "extra_info": "{\"topic_id\":16066,\"strategy_id\":\"q1\",\"choice_topic_id\":16066,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 9 显示单词
        "log_time": "1723850514619",
        "product_id": "bcz_app_h5",
        "stat_group": "study-detail-common",
        "event_id": "topic_wiki_show",
        "extra_info": "{\"topic_id\":4951,\"book_id\":410,\"channel\":\"study_mainstream\",\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 10 开始拼写
        "log_time": "1723850626993",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "begin-spelling-plan"
    },
    {# 11 完成拼写
        "log_time": "1723850651181",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "finish-spelling-plan",
        "extra_info": "{\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 12 复习过渡页
        "log_time": "1723850655161",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "review_midpage_view",
        "extra_info": "{\"mode_type\":3}"
    },
    {# 13 复习过渡页点击
        "log_time": "1723850658350",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "review_midpage_click",
        "extra_info": "{\"mode_type\":3,\"button_type\":\"yes\"}"
    },
    {# 14 开始复习
        "log_time": "1723850658359",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "begin-normal-plan",
        "extra_info": "{\"mode_type\":3,\"button_text\":\"复习\",\"home_state\":{\"state\":\"learning\",\"data\":{\"reviewingPoolCount\":999}}}"
    },
    {# 15 完成复习
        "log_time": "1723850707920",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "finish-normal-plan",
        "extra_info": "{\"plan_type\":\"XModelReviewStudy\"}"
    },
    {# 16 学习数据同步完成页面
        "stat_group": "main-study",
        "event_id": "account_finished_data_show",
        "product_id": "bcz_app_h5",
        "log_time": "1723850723866",
        "extra_info": "{\"word_num\":7,\"experience\":20}"
    },
    {# 17 点击首页去打卡
        "event_id": "homepage-daka-click",
        "log_time": "1723850773934",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 18 访问打卡页面
        "event_id": "daka_page_visit",
        "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"\"}",
        "log_time": "1723850774922",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 19 点击分享到微信
        "event_id": "daka-to-wx",
        "log_time": "1723850788432",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 20 点击分享
        "event_id": "daka_share_channel_click",
        "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"6373\",\"share_channel\":\"weixin\"}",
        "log_time": "1723850788412",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 21 分享结束
        "event_id": "return-on-finish-plan-share",
        "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"6373\",\"share_channel\":\"weixin\"}",
        "log_time": "1723850883118",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 22 领取同桌奖励
        "log_time": "1723852063541",
        "product_id": "bcz_app_h5",
        "stat_group": "explore-common",
        "event_id": "together_recite_click",
        "extra_info": "{\"button\":\"coin\",\"channel\":\"deskmate\"}"
    },
    {# 23 班级签到
        "log_time": "1723852064583",
        "product_id": "bcz_app_h5",
        "stat_group": "explore-common",
        "event_id": "together_recite_click",
        "extra_info": "{\"button\":\"coin\",\"channel\":\"class\"}"
    },
    {# 24 班级段位奖励
        "log_time": "1723852064583",
        "product_id": "bcz_app_h5",
        "stat_group": "explore-common",
        "event_id": "together_recite_click",
        "extra_info": "{\"button\":\"coin\",\"channel\":\"class_level\"}"
    },
    {# 25 点击商城
        "event_id": "mall-tab-click",
        "log_time": "1723852206439",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 26 加载商城
        "event_id": "mall-tab-click_extra_v2",
        "extra_info": "{\"servertype\":1,\"imageurl\":\"https://vol-v6.bczcdn.com/r/ltxwm285a8njpqetlsmf66453zsulws4.png\",\"taobaoinstalled\":false,\"aid\":\"10000\",\"jumptype\":1}",
        "log_time": "1723852206446",
        "product_id": "bcz_app",
        "stat_group": "h5-error"
    },
    {# 27 商城heartbeat
        "log_time": "1723852214632",
        "product_id": "bcz_app_h5",
        "stat_group": "bcz-mall-common",
        "event_id": "mall_carousel_show",
        "extra_info": "{\"trace\":\"bcz_app_main\",\"_path\":\"/homeV2\",\"banner_idx\":2,\"link_url\":\"https://learn.baicizhan.com/new_copper/link-to-duiba?linkTo=https%3A%2F%2Factivity-6.m.duiba.com.cn%2Fhdtool%2Findex%3Fid%3D272751389954266%26dbnewopen\"}"
    },
    {# 28 任务中心
        "stat_group": "activity-common",
        "event_id": "study_task_main_show",
        "product_id": "bcz_app_h5",
        "log_time": "1725581943815",
        "extra_info": "{\"task_id\":1631590}"# 最后一个任务
    },
    {# 29 pk加载
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_ActivityHomePageView",
        "product_id": "bcz_app_h5",
        "log_time": 1725754449459,
        "extra_info": "{\"ABPage\":\"B\"}"
    },
    {# 30 pk主页面
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_ArenaHomePageView",
        "product_id": "bcz_app_h5",
        "log_time": 1725754449945,
        "extra_info": "{\"SignStatus\":1}"
    },
    {# 31 进入pk准备页面
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_ArenaHomePageGoPKClick",
        "product_id": "bcz_app_h5",
        "log_time": 1725754453782,
        "extra_info": "{\"SignStatus\":1}"
    },
    {# 32 pk练习页面
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_PKPracticeMainPageView",
        "product_id": "bcz_app_h5",
        "log_time": 1725754453883,
        "extra_info": "{}"
    },
    {# 33 pk开始
        "stat_group": "activity-common",
        "event_id": "PKPracticePageBeginClick",
        "product_id": "bcz_app_h5",
        "log_time": 1725756092359,
        "extra_info": "{}"
    },
    {# 34 pk回合开始
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_PKPracticeChallengeBegin",
        "product_id": "bcz_app_h5",
        "log_time": 1725756094213,
        "extra_info": "{\"CurrentRound\":0}"
    },
    {# 35 pk匹配成功
        "stat_group": "activity-common",
        "event_id": "PKMatchSuccess",
        "product_id": "bcz_app_h5",
        "log_time": 1725756096025,
        "extra_info": "{\"MatchTime\":1811}"
    },
    {# 36 pk选择答案
        "stat_group": "activity-common",
        "event_id": "PKQuestionChoiceClick",
        "product_id": "bcz_app_h5",
        "log_time": 1725756102245,
        "extra_info": "{\"ContestId\":null,\"ChallengeId\":15034976,\"QuesOrder\":1,\"PuzzleId\":12656,\"ChoiceOrder\":3,\"CostTime\":2824,\"IsRight\":false}"
    },
    {# 37 pk结束
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_PKPracticeChallengeFinish",
        "product_id": "bcz_app_h5",
        "log_time": 1725756149177,
        "extra_info": "{\"CurrentRound\":1}"
    },
    {# 38 单词对战进入
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962138195",
        "event_id": "enter-pk-main",
        "extra_info": "{}"
    },
    {# 39 单词对战开始匹配
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962243878",
        "event_id": "begin-rank-pk",
        "extra_info": ""
    },
    {# 40 单词对战匹配开始
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962247178",
        "event_id": "pk_matched_enter",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585,\"cost_time\":3}"
    },
    {# 41 单词对战匹配完成
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1729302070692",
        "event_id": "pk_matched_done",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585,\"cost_time\":4}"
    },
    {# 42 匹配成功
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1729302071448",
        "event_id": "pk_success",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585,\"cost_time\":5}"
    },
    {# 43 作答完毕
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962255353",
        "event_id": "click_pk_detail_score",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"topic_id\":19480,\"challenge_id\":421585,\"puzzle_order\":1,\"score\":\"\",\"challenge_type\":\"排位赛\",\"cost_time\":5}"
    },
    {# 44 单词对战结束
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962285330",
        "event_id": "pk_over",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585}"
    },
    {# 45 查看单词对战结果
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962287866",
        "event_id": "enter_result",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\"}"
    }
]




def generator(content):
    # 压缩数据
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    yield content
    
# def create_thrift_ssl_socket(host, port, cert_path=None, key_path=None):  

#     context = ssl.create_default_context()  
#     if cert_path:  
#         # 如果需要，加载 SSL 证书和密钥  
#         context.load_cert_chain(certfile=cert_path, keyfile=key_path) 
#     ssl_socket = TSSLSocket.TSSLSocket(host, port, ssl_context=context, server_hostname = host) 
#     # sslContext.wrap_socket()已经包含在TSSLSocket中

#     return ssl_socket

# def create_ssl_socket(host, port, cert_path=None, key_path=None):  

#     context = ssl.create_default_context()  
#     if cert_path:  
#         # 如果需要，加载 SSL 证书和密钥  
#         context.load_cert_chain(certfile=cert_path, keyfile=key_path) 
#     ssl_socket = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname = host)
#     ssl_socket.connect((host, port))
#     return ssl_socket

db_path = 'user_config.db'
def db_init(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_daka_timestamp (
        unique_id INTEGER PRIMARY KEY,
        year INTEGER,
        month INTEGER,
        day INTEGER,
        timestamp INTEGER
    )''')
    conn.commit()
    conn.close()

def connect():
    conn = sqlite3.connect(db_path)
    return conn

def print_thrift_object(obj, indent=0, index=-1, f=None):  
    """  
    递归打印Thrift对象及其嵌套结构  
    :param obj: Thrift对象  
    :param indent: 用于缩进的空格数  
    """  
    index_str = ''
    if index != -1:  
        index_str = f'[{index}]:'  
    indent_str = ' ' * indent  
    if isinstance(obj, dict):  
        for key, value in obj.items():  
            if f is not None:
                f.write(f'{indent_str}{index_str}{key}:\n')
            else:
                print(f"{indent_str}{index_str}{key}:")  
            print_thrift_object(value, indent + 4, f=f)  
    elif isinstance(obj, list):  
        for index, item in enumerate(obj):  
            print_thrift_object(item, indent, index = index, f=f)  
    elif hasattr(obj, '__dict__'):  
        # Thrift生成的类通常具有__dict__属性，包含字段名和值  
        for key, value in obj.__dict__.items():  
            # 忽略Thrift内部使用的属性，如thrift_spec, thrift_field_annotations等  
            if not key.startswith('_'):  
                if f is not None:
                    f.write(f'{indent_str}{index_str}{key}:\n')
                else:
                    print(f"{indent_str}{index_str}{key}:")  
                print_thrift_object(value, indent + 4, f=f)  
    else:  
        # 处理基本类型（如int, str等）  
        if isinstance(obj, str):
            if f is not None:
                f.write(f'{indent_str}{index_str}\'{obj}\'\n')
            else:
                print(f"{indent_str}{index_str}'{obj}'")  
        else:
            if f is not None:
                f.write(f'{indent_str}{index_str}{obj}\n')
            else:
                print(f"{indent_str}{index_str}{obj}")  
  

def send_request(method, url, headers, content = None):
    '''此处没有gzip'''
    if method == 'POST':
        response = requests.post(url, headers=headers, data=content)
    elif method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'OPTIONS':
        response = requests.options(url, headers=headers)
    else:
        raise Exception('method not support')
    if response.status_code != 200:
        raise Exception(f'http status code: {response.status_code}')
    return response

client = None
def send_http2_request(method, url, headers, content, jsonify=False):
    '''
    使用了http2尽可能复用tunnel，但5s闲置会断开连接
    此处没有gzip'''
    
    global client
    if client is None or client.is_closed:
        client = httpx.Client(http2=True, verify=certifi.where())

    client.headers.clear()  
    client.headers.update(headers)
    failed_count = 0
    response = None
    if method == 'POST':
        while True:
            try:
                response = client.post(url, content=content)
                if jsonify:
                    if response.status_code == 200:
                        response = response.json()
                    else:
                        time.sleep(5)
                        continue
                break
            except Exception as e:
                print(f'http2 error: {e}')
                time.sleep(5)
                failed_count += 1
                if failed_count > 7:
                    raise Exception('http2 error')
                continue
        return response
    elif method == 'GET':
        while True:
            try:
                response = client.get(url)
                if jsonify and response.status_code == 200:
                    response = response.json()
                break
            except Exception as e:
                print(f'http2 error: {e}')
                time.sleep(5)
                failed_count += 1
                if failed_count > 7:
                    raise Exception('http2 error')
                continue
        return response
    elif method == 'OPTIONS':
        return client.options(url)
    else:
        return Exception('method not support')

def get_http2_client():
    global client
    if client is None or client.is_closed:
        client = httpx.Client(http2=True, verify=certifi.where())
    return client

    
class bcz_system:
    
    def bcz_system_check_infos(user_cookie=user_cookie, user_config=user_config):
        '''check_infos'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_check_infos()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/check_infos/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_check_infos()
        transport.close()

        return result


    def bcz_system_get_switches(user_cookie=user_cookie, user_config=user_config):
        '''get_switches'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_switches()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_switches/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_switches()
        transport.close()

        return result


    def bcz_system_get_static_config(user_cookie=user_cookie, user_config=user_config):
        '''get_static_config'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_static_config()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_static_config/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_static_config()
        transport.close()

        return result


    def bcz_system_get_domain_whitelist(user_cookie=user_cookie, user_config=user_config):
        '''get_domain_whitelist'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_domain_whitelist()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_domain_whitelist/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()    


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_domain_whitelist()
        transport.close()

        return result


    def bcz_system_get_privacy_agreement_version(user_cookie=user_cookie, user_config=user_config):
        '''get_privacy_agreement_version'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_privacy_agreement_version()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_privacy_agreement_version/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_privacy_agreement_version()
        transport.close()

        return result


    def bcz_system_get_app_beta_update_info(user_cookie=user_cookie, user_config=user_config):
        '''get_app_beta_update_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        args = AppBetaUpdateRequest(
            device_id=user_cookie['device_id'],
            device_manufacturer=bcz_info['device_manufacturer'],
            device_model=bcz_info['device_model'],
            os_name=bcz_info['os_name'],
            os_sdk=bcz_info['os_sdk'],
            short_version=bcz_info['short_version'],
            long_version=bcz_info['long_version'],
            app_channel=user_cookie['channel'],
            app_name=bcz_info['app_name'],
        )
        client.send_get_app_beta_update_info(args)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_app_beta_update_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_app_beta_update_info()
        transport.close()

        return result
    
class advertise:

    def advertise_get_startup_ad(user_cookie=user_cookie, user_config=user_config, screen_length=1920, screen_width=1080):
        '''get_startup_ad'''
        oaid = bcz_info['oaid']
        android_id = user_cookie['device_id']
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        args = StartupAdRequest(screen_length=screen_length, screen_width=screen_width, android_id=android_id, oaid=oaid)
        client.send_get_startup_ad(args)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_startup_ad/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_startup_ad()
        transport.close()

        return result


    def advertise_get_mall_tab_icon_info(user_cookie=user_cookie, user_config=user_config):
        '''get_mall_tab_icon_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_mall_tab_icon_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_mall_tab_icon_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_mall_tab_icon_info()
        transport.close()

        return result


    def advertise_get_practice_popup_adv(user_cookie=user_cookie, user_config=user_config):
        '''get_practice_popup_adv'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_practice_popup_adv()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_practice_popup_adv/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_practice_popup_adv()
        transport.close()

        return result


    def advertise_get_explore_popup_adv(user_cookie=user_cookie, user_config=user_config):
        '''get_explore_popup_adv'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_explore_popup_adv()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_explore_popup_adv/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_explore_popup_adv()
        transport.close()

        return result


    def advertise_get_loading_ad_items(user_cookie=user_cookie, user_config=user_config):
        '''get_loading_ad_items'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_loading_ad_items()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_loading_ad_items/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_loading_ad_items()
        transport.close()

        return result


    def advertise_get_loading_ad_info(user_cookie=user_cookie, user_config=user_config):
        '''get_loading_ad_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_loading_ad_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_loading_ad_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_loading_ad_info()
        transport.close()

        return result


    def advertise_get_live_streaming_info(user_cookie=user_cookie, user_config=user_config):
        '''get_live_streaming_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_live_streaming_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_live_streaming_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_live_streaming_info()
        transport.close()

        return result


    def advertise_get_main_view_bottom_advs_v2(user_cookie=user_cookie, user_config=user_config):
        '''get_main_view_bottom_advs_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_main_view_bottom_advs_v2()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_main_view_bottom_advs_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_main_view_bottom_advs_v2()
        transport.close()

        return result


    def advertise_get_main_view_top_banner_advs(user_cookie=user_cookie, user_config=user_config):
        '''get_main_view_top_banner_advs'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_main_view_top_banner_advs()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_main_view_top_banner_advs/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_main_view_top_banner_advs()
        transport.close()

        return result


    def advertise_get_practice_popup_adv(user_cookie=user_cookie, user_config=user_config):
        '''get_practice_popup_adv'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_practice_popup_adv()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_practice_popup_adv/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_practice_popup_adv()
        transport.close()

        return result
    

    def advertise_get_practice_banner_adv(user_cookie=user_cookie, user_config=user_config):
        '''get_practice_banner_adv'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_practice_banner_adv()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_practice_banner_adv/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_practice_banner_adv()
        transport.close()

        return result   
    
class user_study:
    def user_study_user_basic_info_v2(user_cookie=user_cookie, user_config=user_config):
        '''user_basic_info_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_user_basic_info_v2()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/user_basic_info_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_user_basic_info_v2()
        transport.close()

        return result


    def user_study_get_user_study_config(user_cookie=user_cookie, user_config=user_config):
        '''get_user_study_config'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_user_study_config()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_user_study_config/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_user_study_config()
        transport.close()

        return result


    def user_study_get_user_study_mode(user_cookie=user_cookie, user_config=user_config):
        '''get_user_study_mode'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_user_study_mode()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_user_study_mode/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_user_study_mode()
        transport.close()

        return result




    def user_study_user_limit_info_v2(user_cookie=user_cookie, user_config=user_config):
        '''user_limit_info_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_user_limit_info_v2()    
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/user_limit_info_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_user_limit_info_v2()
        transport.close()

        return result


    def user_study_win_streak_status(user_cookie=user_cookie, user_config=user_config, date=int(datetime.datetime.now().strftime('%Y%m%d'))):
        '''win_streak_status'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_win_streak_status(date)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/win_streak_status/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_win_streak_status()
        transport.close()

        return result

    def user_study_submit_win_streak_records(user_cookie=user_cookie, user_config=user_config, client_date=int(datetime.datetime.now().strftime('%Y%m%d'))):
        '''submit_win_streak_records'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        try:
            client_date = int(client_date)
        except:
            client_date = int(datetime.datetime.now().strftime('%Y%m%d'))
        client.send_submit_win_streak_records(client_date=client_date, win_streak_dates=[client_date])
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/submit_win_streak_records/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content, False)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_submit_win_streak_records()
        transport.close()

        result = f"{result}.{client_date}.{datetime.datetime.now().strftime('%Y%m%d')}"

        return result


    def user_study_get_books_replace_info(user_cookie=user_cookie, user_config=user_config):
        '''get_books_replace_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_books_replace_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_books_replace_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_books_replace_info()
        transport.close()

        return result


    def user_study_get_main_page_js(user_cookie=user_cookie, user_config=user_config):
        '''get_main_page_js'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_main_page_js()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_main_page_js/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_main_page_js()
        transport.close()

        return result

    def user_study_user_daka_v2(user_cookie=user_cookie, user_config=user_config, daka_dates=[]):
        '''user_daka_v2
        params: daka_dates: list of (year, month, day, timestamp), the whole month(1 to today), ascending'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        user_daka_dates = []

        def get_this_month_timestamp(year, month, day):
            # 获取当月第一天的日期
            timestamp = int(datetime.datetime(year, month, 1).timestamp()) + 1
            result = []
            for i in range(day):
                result.append([year, month, i+1, timestamp + i*86400])
            return result
        
        if daka_dates == []:
            today_date = datetime.datetime.now().date()
            year = today_date.year
            month = today_date.month
            day = today_date.day
            daka_dates = get_this_month_timestamp(year, month, day)

        for date in daka_dates:
            user_daka_dates.append(UserDakaDate(year=date[0], month=date[1], day=date[2], timestamp=date[3]))
        
        client.send_user_daka_v2(UserDakaRequest(
            book_id = user_config['book_id'],
            count = 7,# 今日学习+复习单词数
            daka_dates=user_daka_dates,
            timezone=user_config['timezone'],
            client_date=user_daka_dates[-1],
            poster_topic_ids=[]
        ))
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/user_daka_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content, False)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_user_daka_v2()
        transport.close()

        return result


    def user_study_get_train_page_resource(user_cookie=user_cookie, user_config=user_config):
        '''get_train_page_resource'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_train_page_resource()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_train_page_resource/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_train_page_resource()
        transport.close()

        return result
    
    def user_study_update_done_data(user_cookie=user_cookie, user_config=user_config, done_data={}):
        '''update_done_data
        params: done_data: dict{topicId:{current_score, span_days, used_time, done_times, wrong_times, is_first_do_at_today, tag_id, spell_score, listening_score, chn_score, review_round}} '''
        word_list = []
        for topic_id, data in done_data.items():
            word_list.append(UserDoneWordRecord(
                word_topic_id=int(topic_id),
                current_score=data['current_score'],
                span_days=data['span_days'],
                used_time=data['used_time'],
                done_times=data['done_times'],
                wrong_times=data['wrong_times'],
                is_first_do_at_today=data['is_first_do_at_today'],
                tag_id=data['tag_id'],
                spell_score=data['spell_score'],
                listening_score=data['listening_score'],
                chn_score=data['chn_score'],
                review_round=data['review_round']
            ))
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        time_stamp_short = int(time.time())
        client.send_update_done_data(
            last_sync_at=time_stamp_short,
            arr_done_records=word_list,
            current_word_level_id=user_config['book_id'],
            is_today_completed=True
        )
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/update_done_data/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content, False)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_update_done_data()
        transport.close()

        return result
    
    def user_study_submit_experience_record(user_cookie=user_cookie, user_config=user_config, word_count=5, wrong_count=1, review_count=5, review_wrong_count=1):
        '''submit_experience_record
        params: experience_record: list of experiences'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        experience_list = [
            StudyExperienceRecord(
                # 已知：behavior: 1 第一次正确 2 改正 3 第一次错误 4 点击下一个的次数
                # 斩的不计入正确或更正，只计入错误
                questionType='deep-learning-one',
                behavior=1,
                cnt=word_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-two',
                behavior=1,
                cnt=word_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-three',
                behavior=1,
                cnt=word_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=1,
                cnt=word_count - wrong_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=2,
                cnt=wrong_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=3,
                cnt=word_count
            )]
        if review_count > 0:
            experience_list.extend([
                StudyExperienceRecord(
                    questionType='deep-review-one',
                    behavior=1,
                    cnt=review_count
                ),
                StudyExperienceRecord(
                    questionType='deep-review-spell',
                    behavior=1,
                    cnt=review_count - review_wrong_count
                ),
                StudyExperienceRecord(
                    questionType='deep-review-spell',
                    behavior=2,
                    cnt=review_wrong_count
                ),
                StudyExperienceRecord(
                    questionType='deep-review-spell',
                    behavior=3,
                    cnt=review_wrong_count
                )
            ])
        
        if random.random() < 0.5:
            experience_list.append(StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=4,
                cnt=1
            ))
        if random.random() < 0.5:
            experience_list.append(StudyExperienceRecord(
                questionType='deep-review-spell',
                behavior=4,
                cnt=1
            ))
        client.send_submit_experience_record(experience_list)
            
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/submit_experience_record/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content, False)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_submit_experience_record()
        transport.close()

        return result
    
    def get_daka_background_datas(learn_list, user_cookie=user_cookie, user_config=user_config):
        '''get_daka_background_datas'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_daka_background_datas(learn_list)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_daka_background_datas/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_daka_background_datas()
        transport.close()

        return result
    
    def user_study_share_bonus(user_cookie=user_cookie, user_config=user_config):
        '''share_bonus'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        time_long = int(time.time() * 1000)
        client.send_share_bonus(client_timestamp_ms = time_long)
        content = transport.getvalue()
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/share_bonus/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_share_bonus()
        transport.close()

        return result
    
    def user_study_credit_task_center(user_cookie=user_cookie, user_config=user_config):
        '''credit_task_center'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_credit_task_center()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/credit_task_center/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_credit_task_center()
        transport.close()

        return result
    # void upload_task_action(1: list<TaskUploadReq> req) throws (1: LogicException bomb, 2: SystemException boom)
    def user_study_upload_task_action(user_cookie=user_cookie, user_config=user_config, task_upload_req_list=[]):
        '''upload_task_action
        args: list[[action, cnt]]
        actions: learnMore'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        task_upload_req_list = [TaskUploadReq(action=action, cnt=cnt) for action, cnt in task_upload_req_list]
        client.send_upload_task_action(task_upload_req_list)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/upload_task_action/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_upload_task_action()
        transport.close()

        return result

    

class unified_user:
    def unified_user_get_bind_info(user_cookie=user_cookie, user_config=user_config):
        '''get_bind_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        client.send_get_bind_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$passport", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/unified_user_service/get_bind_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        result = client.recv_get_bind_info()
        transport.close()

        return result


    def unified_user_check_access_token(user_cookie=user_cookie, user_config=user_config):
        '''check_access_token'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        client.send_check_access_token(get_device_str(user_cookie['device_id']))
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$passport", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/unified_user_service/check_access_token/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        result = client.recv_check_access_token()
        transport.close()

        return result

class assistant:
    def assistant_check_feedback_msg(user_cookie=user_cookie, user_config=user_config):
        '''check_feedback_msg'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        client.send_check_feedback_msg(get_device_str(user_cookie['device_id']))
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$assistant", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/assistant/check_feedback_msg/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        result = client.recv_check_feedback_msg()
        transport.close()

        return result

    def assistant_get_activity_updated_time(user_cookie=user_cookie, user_config=user_config):
        '''get_activity_updated_time'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        client.send_get_activity_updated_time()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$assistant", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/assistant/get_activity_updated_time/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        result = client.recv_get_activity_updated_time()
        transport.close()

        return result


    def assistant_get_beta_user_types_v2(user_cookie=user_cookie, user_config=user_config):
        '''get_beta_user_types_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        client.send_get_beta_user_types_v2()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$assistant", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/assistant/get_beta_user_types_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        result = client.recv_get_beta_user_types_v2()
        transport.close()

        return result



def get_report_event_jsons(args: list, thrift=True) -> list[str]:
    jsons = []
    for arg in args:
        json_dict = report_json[arg['index']].copy()
        json_dict['log_time'] = str(int(time.time() * 1000))
        if 'extra_info' in arg:
            json_dict['extra_info'] = arg['extra_info']
        if thrift:
            jsons.append(json.dumps(json_dict, ensure_ascii=False))
        else:
            jsons.append(json_dict)
    return jsons

def report_event(user_cookie=user_cookie, user_config=user_config, jsons=[], type=0, host=0):
    '''report_event
    args:jsons[{"index":int,"extra_info":str}]
    type:0 thrift; 1 json
    host:0 events; 1 system(only for json)'''
    time_long = int(time.time() * 1000)
    if type == 0:
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_report_service.Client(protocol)
        client.send_report_event(get_report_event_jsons(jsons))
        content = transport.getvalue()
        headers = getHeaders("$report", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_report/report_event/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_report_service.Client(protocol)
        result = client.recv_report_event()
        transport.close()
        return result
    else:
        if host == 0:
            headers = getHeaders('$report', user_cookie, int(time.time()), index=1, quote=True)
            # https://events.baicizhan.com/api/system/report_event
        else:
            headers = getHeaders('$system', user_cookie, int(time.time()), index=1, quote=True)
        headers['Content-Type'] = 'text/plain'

        # https://system.baicizhan.com/api/system/report_event
        # https://events.baicizhan.com/api/system/report_event_without_login
        if jsons[0].get('without_login', False) == True:
            url = f'https://{headers["Host"]}/api/system/report_event_without_login'
        else:
            url = f'https://{headers["Host"]}/api/system/report_event'
        result = send_http2_request('POST', url, headers, json.dumps(get_report_event_jsons(jsons, False), ensure_ascii=False))

        return result


    

# 下面是notify接口
def notify_get_remind_info(user_cookie=user_cookie, user_config=user_config):
    '''get_remind_info'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    client.send_get_remind_info()
    content = transport.getvalue()
    time_long = int(time.time() * 1000)
    headers = getHeaders("$notify", user_cookie, int(time.time()))
    url = f'https://{headers["Host"]}/rpc/notify/get_remind_info/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    result = client.recv_get_remind_info()
    transport.close()

    return result

def notify_get_latest_notify(user_cookie=user_cookie, user_config=user_config):
    '''get_latest_notify'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    client.send_get_latest_notify()
    content = transport.getvalue()
    time_long = int(time.time() * 1000)
    headers = getHeaders("$notify", user_cookie, int(time.time()))
    url = f'https://{headers["Host"]}/rpc/notify/get_latest_notify/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    result = client.recv_get_latest_notify()
    transport.close()

    return result

# 下面是resource接口
def resource_get_book_resource_update_info(user_cookie=user_cookie, user_config=user_config):
    '''get_book_resource_update_info'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = resource_api_service.Client(protocol)
    book_id = user_config['book_id']
    client.send_get_book_resource_update_info(book_id)
    content = transport.getvalue()
    time_long = int(time.time() * 1000)
    headers = getHeaders("$resource", user_cookie, int(time.time()))
    url = f'https://{headers["Host"]}/rpc/resource_api/get_book_resource_update_info/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = resource_api_service.Client(protocol)
    result = client.recv_get_book_resource_update_info()
    transport.close()

    return result

def social_send_share_success(user_cookie=user_cookie, user_config=user_config, channel=1):
    '''send_share_success'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = social_service.Client(protocol)
    time_long = int(time.time() * 1000)
    client.send_send_share_success(module_name=0, timestamp=time_long, channel=channel)
    content = transport.getvalue()
    headers = getHeaders("$DATA", user_cookie, int(time.time()))
    # https://www.baicizhan.com/rpc/socials/send_share_success/1723850883199
    url = f'https://{headers["Host"]}/rpc/socials/send_share_success/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = social_service.Client(protocol)
    result = client.recv_send_share_success()
    transport.close()

    return result

class thrift_logger:
    def __init__(self):
        self.f = open(f'log{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.txt', 'w', encoding='utf-8')
        self.threads = []
        self.lock = threading.Lock()

    
    def run(self, generator):
        def threaded_run(name, generator):
            result = []
            for i in generator:
                result.append(i)
            with self.lock:
                # print(f'\033[1;37m--[{name}]\033[0m\n')
                self.f.write(f'\n\n\n\n\n\n# 🌟[{name}]\n')
                for i in result:
                    # print(f'\033[1;36m[{i.__class__.__name__}]\033[0m\n')
                    self.f.write(f'## ❄️[{i.__class__.__name__}]\n')
                    print_thrift_object(i, f=self.f)
        self.threads.append(threading.Thread(target=threaded_run, args=(generator.__name__, generator)))
        self.threads[-1].start()

    def close(self):
        for t in self.threads:
            t.join()
        self.f.close()

    def __del__(self):
        self.close()

class cold_launch:
    '''模仿bcz客户端冷启动，将读取到的数据写入txt日志'''
    # fiddler_filter: regex:^https://system\.baicizhan\.com.+(0|1|2|3|4|5|6|7|8|9)$
    def user_study_cold_launch(cold_launch=True, daka_dates=[], user_cookie=user_cookie, user_config=user_config):
        '''user_study_cold_launch'''
        if cold_launch:
            yield user_study.user_study_user_basic_info_v2(user_cookie=user_cookie, user_config=user_config)
            yield user_study.user_study_get_user_study_config(user_cookie=user_cookie, user_config=user_config)
            yield user_study.user_study_get_user_study_mode(user_cookie=user_cookie, user_config=user_config)
        yield user_study.user_study_user_limit_info_v2(user_cookie=user_cookie, user_config=user_config)
        yield user_study.user_study_win_streak_status(user_cookie=user_cookie, user_config=user_config)
        if cold_launch:
            yield user_study.user_study_get_books_replace_info(user_cookie=user_cookie, user_config=user_config)
            yield user_study.user_study_get_main_page_js(user_cookie=user_cookie, user_config=user_config)
            yield user_study.user_study_user_daka_v2(daka_dates=daka_dates, user_cookie=user_cookie, user_config=user_config)
            yield user_study.user_study_get_train_page_resource(user_cookie=user_cookie, user_config=user_config)


    def bcz_system_cold_launch(cold_launch=True, user_cookie=user_cookie, user_config=user_config):
        '''bcz_system_cold_launch'''
        yield bcz_system.bcz_system_check_infos(user_cookie=user_cookie, user_config=user_config)
        if cold_launch:
            yield bcz_system.bcz_system_get_switches(user_cookie=user_cookie, user_config=user_config)
            yield bcz_system.bcz_system_get_static_config(user_cookie=user_cookie, user_config=user_config)
            yield bcz_system.bcz_system_get_domain_whitelist(user_cookie=user_cookie, user_config=user_config)
            yield bcz_system.bcz_system_get_privacy_agreement_version(user_cookie=user_cookie, user_config=user_config)
            yield bcz_system.bcz_system_get_app_beta_update_info(user_cookie=user_cookie, user_config=user_config)



    def advertise_cold_launch(cold_launch=True, user_cookie=user_cookie, user_config=user_config):
        '''advertise_cold_launch'''
        yield advertise.advertise_get_startup_ad(user_cookie=user_cookie, user_config=user_config)
        if cold_launch:
            yield advertise.advertise_get_mall_tab_icon_info(user_cookie=user_cookie, user_config=user_config)
        yield advertise.advertise_get_practice_popup_adv(user_cookie=user_cookie, user_config=user_config)
        yield advertise.advertise_get_explore_popup_adv(user_cookie=user_cookie, user_config=user_config)
        yield advertise.advertise_get_loading_ad_items(user_cookie=user_cookie, user_config=user_config)
        yield advertise.advertise_get_loading_ad_info(user_cookie=user_cookie, user_config=user_config)
        yield advertise.advertise_get_live_streaming_info(user_cookie=user_cookie, user_config=user_config)
        yield advertise.advertise_get_main_view_bottom_advs_v2(user_cookie=user_cookie, user_config=user_config)
        yield advertise.advertise_get_main_view_top_banner_advs(user_cookie=user_cookie, user_config=user_config)
        if cold_launch:
            yield advertise.advertise_get_practice_banner_adv(user_cookie=user_cookie, user_config=user_config)
        


    def assistant_cold_launch(cold_launch=True, user_cookie=user_cookie, user_config=user_config):
        '''assistant_cold_launch'''
        yield assistant.assistant_check_feedback_msg(user_cookie=user_cookie, user_config=user_config)
        yield assistant.assistant_get_activity_updated_time(user_cookie=user_cookie, user_config=user_config)
        yield assistant.assistant_get_beta_user_types_v2(user_cookie=user_cookie, user_config=user_config)

    def report_event_cold_launch(cold_launch=True, user_cookie=user_cookie, user_config=user_config):
        '''report_event_cold_launch'''
        cold_launch_report_event = [
            {"index": 0},
            {"index": 2},
            {"index": 4, "extra_info": "{" + f"adv_id\":\"{user_config['adv_id']}\",\"id\":\"{user_config['adv_id']}\"" + "}"},
            {"index": 5},
            {"index": 6, "extra_info": "{" + f"\"device_id\":\"{get_device_str(user_cookie['device_id'])}\",\"channel\":\"{user_config['app_channel']}\"" + "}"},
        ]
        yield report_event(jsons = cold_launch_report_event,user_cookie=user_cookie, user_config=user_config)


    def notify_cold_launch(cold_launch=True, user_cookie=user_cookie, user_config=user_config):
        '''notify_cold_launch'''

        yield notify_get_remind_info(user_cookie=user_cookie, user_config=user_config)
        yield notify_get_latest_notify(user_cookie=user_cookie, user_config=user_config)

    def resource_cold_launch(cold_launch=True, user_cookie=user_cookie, user_config=user_config):
        '''resource_cold_launch'''
        if cold_launch:
            yield resource_get_book_resource_update_info(user_cookie=user_cookie, user_config=user_config)

    def unified_user_cold_launch(cold_launch=True, user_cookie=user_cookie, user_config=user_config):
        '''unified_user_cold_launch'''
        if cold_launch:
            yield unified_user.unified_user_get_bind_info(user_cookie=user_cookie, user_config=user_config)
        yield unified_user.unified_user_check_access_token(user_cookie=user_cookie, user_config=user_config)


    def example(user_cookie=user_cookie, user_config=user_config):

        logger = thrift_logger()
        print('\033[1;37m--[$bcz_system]\033[0m')
        logger.run(cold_launch.bcz_system_cold_launch(user_cookie=user_cookie, user_config=user_config))
        
        print('\033[1;37m--[$advertise]\033[0m')
        logger.run(cold_launch.advertise_cold_launch(user_cookie=user_cookie, user_config=user_config))

        print('\033[1;37m--[$passport/unified_user_service]\033[0m')
        logger.run(cold_launch.unified_user_cold_launch(user_cookie=user_cookie, user_config=user_config))

        print('\033[1;37m--[$assistant]\033[0m')
        logger.run(cold_launch.assistant_cold_launch(user_cookie=user_cookie, user_config=user_config))

        print('\033[1;37m--[$notify]\033[0m')
        notify_generator = cold_launch.notify_cold_launch(user_cookie=user_cookie, user_config=user_config)
        logger.run(notify_generator)

        print('\033[1;37m--[$resource]\033[0m')
        resource_generator = cold_launch.resource_cold_launch(user_cookie=user_cookie, user_config=user_config)
        logger.run(resource_generator)
        
        
        print('\033[1;37m--[$learn/user_study]\033[0m')
        
        user_study_generator = cold_launch.user_study_cold_launch(user_cookie=user_cookie, user_config=user_config)
        logger.run(user_study_generator)
        print('\033[1;37m--[$report]\033[0m')
        logger.run(cold_launch.report_event_cold_launch(user_cookie=user_cookie, user_config=user_config))

        logger.close()

def clear_learnt_list(unique_id):
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''DROP TABLE IF EXISTS {learnt_words_db}''')
    conn.commit()

def get_learnt_list(unique_id):
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {learnt_words_db} (
        TOPIC_ID INTEGER,
        DATE TEXT)
    ''')
    conn.commit()
    result = cursor.execute(f'''SELECT TOPIC_ID FROM {learnt_words_db}''')
    learnt_list = [i[0] for i in result.fetchall()]
    return learnt_list

def add_learnt_list(unique_id, topic_id: list):
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {learnt_words_db} (
        TOPIC_ID INTEGER,
        DATE TEXT)
    ''')
    conn.commit()
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    for i in topic_id:
        cursor.execute(f'''INSERT INTO {learnt_words_db} (TOPIC_ID, DATE) VALUES (?,?)''', (i, today_date))
    conn.commit()

def get_history_learnt_list(unique_id, delta=1):
    '''获取delta天前的学习列表'''
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {learnt_words_db} (
        TOPIC_ID INTEGER,
        DATE TEXT)
    ''')
    conn.commit()
    history_date = (datetime.datetime.now() - datetime.timedelta(days=delta)).strftime('%Y-%m-%d')
    print(f"get{delta}={history_date}")
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    result = cursor.execute(f'''SELECT TOPIC_ID FROM {learnt_words_db} WHERE DATE == ?''', (history_date, ))
    learnt_list = [i[0] for i in result.fetchall()]
    return learnt_list

from src.bcz import getRandomWordIDInBook

conn = None
def puzzle_init(puzzle_category):
    global conn
    if conn is not None:
        return
    conn = sqlite3.connect('puzzle.db')
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {puzzle_category} (
        INDEX_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        ID INTEGER UNIQUE,
        QUESTION TEXT,
        CHN_MEAN TEXT,
        ANSWER TEXT,
        OPTIONS1 TEXT,
        OPTIONS2 TEXT,
        OPTIONS3 TEXT,
        TOPIC_ID INTEGER)
    ''')
    conn.commit()

def puzzle_solver(puzzle_dict, puzzle_category):
    # 链接数据库
    cursor = conn.cursor()
    id = int(puzzle_dict['id'])
    chn_mean = puzzle_dict['chnMean']
    if chn_mean is None:
        puzzle_dict['chnMean'] = ''
    option_list = puzzle_dict['options'].copy()
    answer = puzzle_dict['rightAnswer']
    question = puzzle_dict['question']
    topic_id = puzzle_dict['topicId']
    # 查找答案
    cursor.execute(f'''SELECT ANSWER FROM {puzzle_category} WHERE ID == ?''', (id, ))
    result = cursor.fetchone()
    stored = False
    if result is not None:
        stored = True
        puzzle_dict['chnMean'] += 'Stored'
        # print(id ,result, option_list)
        if answer is None:
            for i, option in enumerate(option_list):
                # print(i, option, result[0], answer)
                if option == result[0]:
                    answer = i + 1
                    break
            if answer is None:
                # print(i, option, result[0], answer, puzzle_dict['chnMean'])
                puzzle_dict['chnMean'] += 'Expired'
                stored = False
                print(f'id={id} 题目过期...更新中')
            
    
    # print(stored, answer, puzzle_dict['chnMean'])
    if not stored and answer is not None:
        answer_text = option_list[answer - 1]
        cursor.execute(f'''INSERT OR REPLACE INTO {puzzle_category} (ID, QUESTION, CHN_MEAN, ANSWER, OPTIONS1, OPTIONS2, OPTIONS3, TOPIC_ID) VALUES (?, ?, ?, ?, ?, ?,?, ?)''', (id, question, chn_mean, answer_text, option_list[0], option_list[1], option_list[2], topic_id))
        conn.commit()
        puzzle_dict['chnMean'] += 'Learnt'
    if answer is None:
        answer = random.randint(0, 4)
        if answer == 0:
            answer = 1 # 干扰概率
    return answer

def puzzle_close():
    global conn
    if conn is None:
        return
    conn.close()
    conn = None

wl_conn = None
wl_patch_conn = None
whitelist = []
def word_lookup_init():
    global wl_conn
    global wl_patch_conn
    global whitelist
    with open('whitelist.json', 'r', encoding='utf-8') as f:
        whitelist = json.load(f)
    if wl_conn is not None:
        return
    wl_conn = sqlite3.connect('lookup.db')
    wl_patch_conn = sqlite3.connect('lookup_patch.db')
    cursor = wl_patch_conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS dict_bcz (
        TOPIC_ID INTEGER,
        WORD TEXT,
        ANSWER TEXT,
        RANK TEXT)
    ''')
    wl_patch_conn.commit()
    # 默认存在，不需要创建
    return

def find_variant(word):
    cursor = wl_conn.cursor()
    cursor.execute(f'''SELECT origin FROM {get_variant_table_name(word)} WHERE variant == ?''', (word, ))
    result = cursor.fetchone()
    if result is None:
        return word
    return result[0]

def get_variant_table_name(word):
    if word[0] >= 'a' and word[0] <= 'b':
        return 'variant_a_b'
    elif word[0] == 'c':
        return 'variant_c'
    elif word[0] >= 'd' and word[0] <= 'f':
        return 'variant_d_f'
    elif word[0] >= 'g' and word[0] <= 'k':
        return 'variant_g_k'
    elif word[0] >= 'l' and word[0] <= 'o':
        return 'variant_l_o'
    elif word[0] >= 'p' and word[0] <= 'r':
        return 'variant_p_r'
    elif word[0] == 's':
        return 'variant_s'
    elif word[0] >= 't' and word[0] <= 'z':
        return 'variant_t_z'
    else:
        return 'variant_t_z'
        raise ValueError(f'word{word} not in any variant')

def word_lookup(word, topic_id=None):
    # 先尝试查找原型
    cursor = wl_patch_conn.cursor()
    cursor.execute(f'''SELECT ANSWER FROM dict_bcz WHERE WORD == ?''', (word, ))
    result = cursor.fetchall()
    if result is not None and result != []:
        # 可能有多个，用，连接
        return '@' + '，'.join([i[0] for i in result])
    
    # 尝试查找topic_id
    if topic_id is not None:
        cursor = wl_conn.cursor()
        cursor.execute(f'''SELECT mean_cn FROM dict_bcz WHERE topic_id == ?''', (int(topic_id), ))
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return f'#{result[0]}'
    
    cursor = wl_conn.cursor()
    cursor.execute(f'''SELECT mean_cn FROM dict_bcz WHERE word == ?''', (word, ))
    result = cursor.fetchone()
    if result is not None and result[0] is not None:
        return result[0]
    # 再尝试查找变体
    variant = find_variant(word)
    if variant == word:
        return None
    cursor.execute(f'''SELECT mean_cn FROM dict_bcz WHERE word == ?''', (variant, ))
    result = cursor.fetchone()
    if result is not None and result[0] is not None:
        return '##' + result[0]
    return None


def word_lookup_close():
    global wl_conn
    if wl_conn is None:
        return
    wl_conn.close()
    wl_conn = None
    global wl_patch_conn
    if wl_patch_conn is None:
        return
    wl_patch_conn.close()
    wl_patch_conn = None

replace_dict = {
    '（':'',
    '）':'',
    '  ': ' ',
    '…': '',
    '/': '',
    ', ': '，',
    '…': '',
    '.': '',
    '；':'，'
}
def standardize(chn_mean):
    if chn_mean is None:
        return None
    # 将大写字母转换为小写字母
    # chn_mean = chn_mean.lower()
    for key, value in replace_dict.items():
        chn_mean = chn_mean.replace(key, value)
    return chn_mean # 统一成中文逗号

def word_lookup_puzzle_solver(puzzle_dict):
    word = standardize(puzzle_dict['title'])
    topic_id = puzzle_dict['topicId']
    msg = word
    chn_mean = standardize(word_lookup(word, topic_id))
    if chn_mean is None:
        chn_mean = ''
        Warning(f'word_lookup_puzzle_solver: word not found: {word}')
        msg += '<font color="red">未找到</font>'
    options = puzzle_dict['options']
    options_text = [standardize(option['text']) for option in options] # 统一成中文逗号
    result = None
    for text in options_text:
        if text == chn_mean:
            result = (text, 100)
            msg += '&ltEXACT&gt'
            break
        elif text in chn_mean and (result is None or len(text) > len(result[0])):
            result = (text, 95)
            msg += '&ltIN&gt'
    if result is None:
        result = process.extractOne(chn_mean, options_text)
        msg += '&ltFUZZ&gt'
    msg += f'{options_text}match={result}<br>释义：{chn_mean}'
    if result is None:
        return random.randint(0, 3)
    index = options[options_text.index(result[0])]['id']
    return index, msg

def word_lookup_patcher(puzzle_dict, answer_id, topic_id, rank, rival_score):
    word = puzzle_dict['title']
    for option in puzzle_dict['options']:
        if option['id'] == answer_id:
            answer = option['text']
            break
    else:
        Warning(f'PATCHER: answer_id={answer_id} not found in options')
        return
    cursor = wl_patch_conn.cursor()
    # 检查是否已经存在
    cursor.execute(f'''SELECT RANK FROM dict_bcz WHERE WORD == ? AND ANSWER == ?''', (word, answer))
    result = cursor.fetchone()
    if result is None:
        cursor.execute(f'''INSERT OR IGNORE INTO dict_bcz (TOPIC_ID, WORD, ANSWER, RANK) VALUES (?, ?, ?, ?)''', (topic_id, word, answer, rank))
        wl_patch_conn.commit()
    elif result[0] is None:
        cursor.execute(f'''UPDATE dict_bcz SET RANK = ? WHERE WORD == ? AND ANSWER == ?''', (rank, word, answer))
        wl_patch_conn.commit()
    else:
        recorded_rank = result[0].split(',')
        if rank not in recorded_rank:
            recorded_rank.append(rank)
            cursor.execute(f'''UPDATE dict_bcz SET RANK = ? WHERE WORD == ? AND ANSWER == ?''', (','.join(recorded_rank), word, answer))
            wl_patch_conn.commit()



class daka_list_class:
    def __init__(self):
        self.daka_list = []
        self.lock = threading.Lock()
        self.notice_storage = notice_storage_class()
        self.patch_list = []
        self.status = [] # 标记每个patch_list中的检查状态：0未检查，1已从后检查，2已双向检查
        self.class_list = {}
        self.time_start = time.time()

        # 初始化notice_and_rank_conn
        year = datetime.datetime.now().year
        self.notice_and_rank_path = f'../BCZ-Notice-Examiner/bcz_notice.db'
        conn = sqlite3.connect(self.notice_and_rank_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS notice (
            SHARE_KEY TEXT,
            GROUP_ID INTEGER,
            NAME TEXT,
            RANK_TYPE TEXT,
            RANK INTEGER,
            HASH_VALUE TEXT,
            CONTENT TEXT,
            DATE TEXT,
            LATEST_DATE TEXT,
            SCORE INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS MEMBERS (                   -- 成员表（以用户 + 小班 + 日期 为主键）
                USER_ID INTEGER,             -- 用户ID   *
                NICKNAME TEXT,                      -- 用户昵称
                GROUP_NICKNAME TEXT,                -- 班内昵称(直接覆盖旧的)
                COMPLETED_TIME TEXT,                -- 打卡时间
                TODAY_DATE TEXT,             -- 记录日期 *
                WORD_COUNT INTEGER,                 -- 今日词数
                STUDY_CHEAT INTEGER,                -- 是否作弊
                COMPLETED_TIMES INTEGER,            -- 打卡天数
                DURATION_DAYS INTEGER,              -- 入班天数
                BOOK_NAME TEXT,                     -- 学习词书
                GROUP_ID INTEGER,            -- 小班ID   *
                GROUP_NAME TEXT,                    -- 小班昵称
                AVATAR TEXT,                        -- 用户头像
                DATA_TIME TEXT,                      -- 记录时间
                UNIQUE(USER_ID, GROUP_ID, TODAY_DATE))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS BOOK_NAME (
                HASH_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                BOOK_NAME INTEGER,
                BOOK_ID INTEGER,
                BOOK_URL TEXT)''')
        conn.commit()
        conn.close()

    def close(self):
        # 如果有没检测完的notice，存回去
        for i, patch in enumerate(self.patch_list):
            if self.status[i] == 0:
                self.notice_storage.insert(patch)
        self.notice_storage.close()

    def get_notice_and_rank_conn(self):
        return sqlite3.connect(self.notice_and_rank_path)

    def get_class_list(self, rank):
        class_list = []
        current_data_time = datetime.datetime.now().strftime('%Y-%m-%d')
        if rank not in self.class_list or current_data_time != self.class_list[rank]['data_time']:
            with self.lock:
                headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
                if rank == 0:
                    # https://group.baicizhan.com/group/recommended_groups
                    response = send_http2_request('GET', f'https://{headers["Host"]}/group/recommended_groups', headers, None)
                elif rank >= 1 and rank <= 7:
                    response = send_http2_request('GET', f'https://{headers["Host"]}/group/get_group_rank?rank={rank}', headers, None)
                else:
                    return []
                class_list = response.json()['data']['list']
                self.class_list[rank] = {'data_time': current_data_time, 'class_list': class_list}
                return class_list
        class_list = self.class_list[rank]['class_list']
        return class_list

    def add(self, unique_id):
        with self.lock:
            if len(self.daka_list) == 0:
                print('daka_list time start!')
                self.time_start = time.time()
            self.daka_list.append(unique_id)

    def remove(self,unique_id):
        with self.lock:
            if unique_id in self.daka_list:
                self.daka_list.remove(unique_id)
            if self.is_empty():
                print('daka_list is empty!')
                self.close()
                print(f'总耗时{time.time() - self.time_start}秒')

    def query(self, unique_id):
        return unique_id in self.daka_list
    
    def get_notice(self):
        with self.lock:
            index = -1
            # 检查是否有还没检查完的notice
            if len(self.patch_list) > 0:
                for i, patch in enumerate(self.patch_list):
                    if self.status[i] < 2:
                        bad_notice = patch
                        index = i
                        direction = self.status[i] # 0逆向，1正向
                        break
            if index == -1:
                bad_notice = self.notice_storage.fetch() # 从notice_storage取出一个notice（995token）
                self.patch_list.append(bad_notice)
                self.status.append(0)
                index = len(self.patch_list) - 1
                direction = 0
        return index, bad_notice, direction
    
    def patch_notice(self, index, notice_accepted, direction): # 回调函数，标记fetch到的哪些部分是被接受的
        with self.lock:
            # 取出原来的notice
            bad_notice = self.patch_list[index]
            # 将被接受的部分消除，注意notice_accepted仅可能是从头开始的或末尾的
            if bad_notice[0] == notice_accepted[0]: # or direction == 0:
                self.patch_list[index] = bad_notice[len(notice_accepted):]
                self.status[index] = 1
            if bad_notice[-1] == notice_accepted[-1]: # or direction == 1:
                self.patch_list[index] = bad_notice[:-len(notice_accepted)]
                self.status[index] = 2

    def get_bad_words(self): # 获取检查结果
        result = []
        with self.lock:
            for i, patch in enumerate(self.patch_list):
                if self.status[i] == 2:
                    result.append(patch)
    
    def is_empty(self):
        return len(self.daka_list) == 0




def heartbeat_demon( daka_list: daka_list_class, user_cookie=user_cookie, user_config=user_config):
    unique_id = user_config['unique_id']
    while daka_list.query(unique_id):
        payload=[
            {"index":0}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
        time.sleep(30)
    if daka_list.is_empty():
        puzzle_close()


    

def print_puzzle(puzzle_dict):
    chn_mean = puzzle_dict['chnMean']
    option_list = puzzle_dict['options']
    question = puzzle_dict['question']
    answer = puzzle_dict['rightAnswer']
    result = f'{question}({chn_mean})('
    for i, option in enumerate(option_list):
        if i == answer - 1:
            result += f'<font color="green">{option}</font>/'
        else:
            result += f'{option}/'
    result += ')'
    return result


def pkonline(user_cookie=user_cookie, user_config=user_config, max_round=3):
    '''pkonline'''# max_round用来随机轮数，用来调用2次分散打卡时间
    return # 已于12.5结束
    # 领奖
    # https://pkonline1.baicizhan.com/api/contest/2024/prepare/giftMain?code=mB5AG9fCzo
    headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=1)
    url = f'https://{headers["Host"]}/api/contest/2024/prepare/giftMain?code=mB5AG9fCzo'
    response = send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    cnt = data['blindBox']
    while cnt > 0:
        # https://pkonline1.baicizhan.com/api/contest/2024/prepare/useBlindBox
        headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=1)
        url = f'https://{headers["Host"]}/api/contest/2024/prepare/useBlindBox'
        response = send_http2_request('POST', url, headers, content='{}')
        data = response.json()['data']
        yield f'领取{data["name"]}成功:{data["url"]}，剩余{cnt-1}个'

        url = f'https://{headers["Host"]}/api/contest/2024/prepare/giftMain?code=mB5AG9fCzo'
        response = send_http2_request('GET', url, headers, None)
        data = response.json()['data']
        cnt = data['blindBox']
        time.sleep(random.randint(1, 2))

    puzzle_init('BCZ_NCSVC')
    # https://pk.baicizhan.com/contest2024/sign/?code=mB5AG9fCzo
    # https://pk.baicizhan.com/contest2024/preparation/index.html?code=mB5AG9fCzo
    # https://pkonline1.baicizhan.com/api/contest/2024/tournament/status?code=mB5AG9fCzo
    time_long = int(time.time() * 1000)
    headers = getHeaders("$pk", user_cookie, int(time.time()), index=1)
    url = f'https://{headers["Host"]}/contest2024/sign/?code=mB5AG9fCzo'
    response = send_http2_request('GET', url, headers, None, False)
    if response.status_code != 200:
        yield f'<p style="color:red">单词pk接口请求失败</p>{response.text}'
    url = f'https://{headers["Host"]}/contest2024/preparation/index.html?code=mB5AG9fCzo'
    response = send_http2_request('GET', url, headers, None)

    headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
    url = f'https://{headers["Host"]}/api/contest/2024/tournament/status?code=mB5AG9fCzo'
    response = send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    if data['status'] == 1:
        yield f'pk正在进行 '
    extra_info = "{\"ABPage\":\"B\"}"
    if data['college'] == False:
        extra_info = "{\"ABPage\":\"A\"}"
    payload = [
        {"index": 29, "extra_info": extra_info}, # pk加载
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
    # https://pkonline1.baicizhan.com/api/contest/2024/prepare/main?code=mB5AG9fCzo
    url = f'https://{headers["Host"]}/api/contest/2024/prepare/main?code=mB5AG9fCzo'
    response = send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    if data is None:
        yield f'<p style="color:red">请手动登录并报名pk再运行</p>'
        return
    if data['todayPKFinished'] == True:
        yield f'今日PK已结束'
        return
    yield '开始pk'
    payload = [
        {"index": 30}, # pk主页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
    # https://pkonline1.baicizhan.com/api/contest/2024/prepare/pkMain?code=mB5AG9fCzo
    url = f'https://{headers["Host"]}/api/contest/2024/prepare/pkMain?code=mB5AG9fCzo'
    response = send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    daily_round = data['dailyRound']
    current_round = 0
    if max_round == 0:
        return
    yield f' 今已完成{daily_round}/3 '
    time.sleep(1)
    if daily_round < 3:
        payload = [
            {"index": 31} # 进入pk
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
        
        # https://pkonline1.baicizhan.com/api/contest/2024/tournament/failed_puzzle?lastId=
        time_long = int(time.time() * 1000)
        headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
        url = f'https://{headers["Host"]}/api/contest/2024/tournament/failed_puzzle?lastId='
        response = send_http2_request('GET', url, headers, None)
        data = response.json()['data']

        payload = [
            {"index": 32} # pk练习页面
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
        time.sleep(1)
        payload = [
            {"index": 33} # 点击开始按钮
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
        # https://pk.baicizhan.com/contest2024/contest/index.html?code=mB5AG9fCzo&mode=practice
        time_long = int(time.time() * 1000)
        headers = getHeaders("$pk", user_cookie, int(time.time()), index=3)
        url = f'https://{headers["Host"]}/contest2024/contest/index.html?code=mB5AG9fCzo&mode=practice'
        response = send_http2_request('GET', url, headers, None)

        while True:
            payload = [
                {"index": 34, "extra_info": "{\"CurrentRound\":%d}" % 0} # pk开始（CurrentRound是摆设）
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
            # 匹配
            # https://pkonline1.baicizhan.com/api/contest/practice/match?code=mB5AG9fCzo&contestId=null
            
            time_long = int(time.time() * 1000)
            headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
            url = f'https://{headers["Host"]}/api/contest/practice/match?code=mB5AG9fCzo&contestId=null'
            response = send_http2_request('GET', url, headers, None)
            data = response.json()['data']
            challenge_id = data['challengeId']
            current_round = data['currentRound']
            yield f'第{current_round}轮<br>'
            payload = [
                {"index": 35, "extra_info": "{\"MatchTime\":%d}" % (int(time.time() * 1000) - time_long)} # pk匹配成功
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)

            post_headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
            post_headers['content-type'] = 'application/json'
            options_headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=2)# 这两个请求头一直使用到结束
            time.sleep(3)

            prev_order = 0
            while True:
                # 开始答题
                # https://pkonline1.baicizhan.com/api/contest/practice/heartbeat
                url = f'https://{options_headers["Host"]}/api/contest/practice/heartbeat'
                response = send_http2_request('OPTIONS', url, options_headers, None)
                content = {
                    "challengeId": challenge_id
                }
                content_str = json.dumps(content)
                response = send_http2_request('POST', url, post_headers, content_str)
                data = response.json()['data']
                order = data['order']
                while order == 0 or order == prev_order:
                    response = send_http2_request('POST', url, post_headers, content_str)
                    data = response.json()['data']
                    order = data['order']
                    time.sleep(1)
                yield f'第{order}题'
                rival_escaped = data['rivalEscaped']
                ans = puzzle_solver(data['puzzle'], 'BCZ_NCSVC')
                response_thresh = 4000
                response_delay = random.randint(2000, response_thresh)
                start_timestamp = int(time.time() * 1000)
                session_cnt = int(response_delay / 1000)
                session_delay = response_delay % 1000
                for i in range(session_cnt):
                    time.sleep(1)
                    response = send_http2_request('POST', url, post_headers, content_str)
                    rival_escaped = response.json()['data']['rivalEscaped']
                    if rival_escaped:
                        break
                time.sleep(session_delay / 1000)
                ans_content = {
                    "challengeId": challenge_id,
                    "order": order,
                    "answer": ans
                }
                ans_content_str = json.dumps(ans_content)
                response = send_http2_request('POST', url, post_headers, ans_content_str)
                data = response.json()['data']
                rival_escaped = data['rivalEscaped']
                payload = [
                    {"index": 36, "extra_info": "{\"ContestId\":null,\"ChallengeId\":%d,\"QuesOrder\":%d,\"PuzzleId\":%d,\"ChoiceOrder\":%d,\"CostTime\":%d,\"IsRight\":false}" % (challenge_id, order, data['puzzle']['id'], ans, int(time.time() * 1000 - start_timestamp))} # pk答题成功
                ]
                report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
                if data['rivalAnswer'] is None and not rival_escaped:
                # 等待对手作答
                    while True:
                        response = send_http2_request('POST', url, post_headers, content_str)
                        data = response.json()['data']
                        if data['rivalAnswer'] is not None or data['rivalEscaped']:
                            break
                        time.sleep(1)
                # 检查答案
                puzzle_solver(data['puzzle'], 'BCZ_NCSVC')
                right_answer = data['puzzle']['rightAnswer']
                my_answer = '√' if data['meAnswer'] == right_answer else '×'
                rival_answer = '已逃跑'
                if not rival_escaped:
                    rival_answer = '√' if data['rivalAnswer'] == right_answer else '×'
                puzzle_str = print_puzzle(data['puzzle'])
                yield f'{puzzle_str} {my_answer}/{rival_answer}<br>'

                time.sleep(3)
                if order == 7:
                    break
                prev_order = order # 防止刷新不及时导致重复答题

            # 结束本轮pk
            payload = [
                # "{\"CurrentRound\":1}"
                {"index": 37, "extra_info": "{\"CurrentRound\":%d}" % current_round} # pk结束
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
            # https://pkonline1.baicizhan.com/api/contest/practice/result?contestId=null&challengeId=15133142&code=mB5AG9fCzo
            time_long = int(time.time() * 1000)
            headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
            url = f'https://{headers["Host"]}/api/contest/practice/result?contestId=null&challengeId={challenge_id}&code=mB5AG9fCzo'
            response = send_http2_request('GET', url, headers, None)
            data = response.json()['data']
            daily_finished = data['dailyFinished']
            if daily_finished:
                yield f'完成3轮 +50铜板<br>'
                break
            else:
                yield f'完成第{current_round}轮<br>'
                current_round += 1
                if current_round > max_round:
                    return
                random_wait_second = random.randint(1,4)

pkonline2_lock = threading.Lock()
def pkonline2(user_cookie=user_cookie, user_config=user_config, max_round=3, max_win_round=3, allow_self=False):
    '''单词对战''' # max_round无论输赢，但是体力值不足时，会自动退出
    if user_config.get('no_pk', False) == True:
        yield f'{user_config["name"]}不参加pk'
        return
    word_lookup_init()
    time_short = int(time.time())
    time_long = int(time.time() * 1000) # 只有report_event的cookie和url需要更新time_long，其余均不需要
    # https://pk.baicizhan.com/api/rankpk/v2/current_session?time=1728962138173
    pk_get_headers = getHeaders("$pk", user_cookie, time_short, index=1, quote=True)
    pk_post_headers = getHeaders("$pk", user_cookie, time_short, index=1, quote=True)
    pk_post_headers['content-type'] = 'application/json'

    total_round = 0
    total_win_round = 0
    while True:
        total_round += 1
        if total_round > max_round or total_win_round >= max_win_round:
            return
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/v2/current_session?time={time_long}'
        response = send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        current_user_info = data['currentRankUserInfo']
        end_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['session']['endTime'] // 1000))# auditEndTime=1731772799000
        session_id = data["session"]["sessionId"]
        current_level = current_user_info["currentLevel"]
        current_star = current_user_info["currentStar"]
        current_energy = current_user_info["energy"]
        yield f'单词pk第{total_round}轮 {session_id}赛季{current_level}段{current_star}星{current_energy}体力<br>'
        state = data['session']['state']
        if state == 3:
            yield f'单词pk赛季清扫中，结束<br>'
            return
        if state != 2:
            yield f'<p style="color:red">单词pk赛季状态{state}，请检查</p>'
            return
        # https://pk.baicizhan.com/api/rankpk/main?time=1728962138249&activity_id=0&session_id=40
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/main?time={time_long}&activity_id=0&session_id={session_id}'
        response = send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        current_level = data['current_level']
        current_star = data['current_star']
        current_energy = data['energy']
        reward_available = data['reward_avalible']

        for level in data['levels']:
            if level['level'] == current_level:
                current_level_dict = level
                break
        energy_cost = current_level_dict['energy_cost']
        if current_energy < energy_cost:
            yield f'体力{current_energy}不足{energy_cost}，结束<br>'
            return
        rank_name_en = current_level_dict['name_en']

        if reward_available:
            yield f'正在领取'
            payload = [
                {"index": 38}
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            # https://pk.baicizhan.com/api/rankpk/get_reward?time=1728962144814&session_id=40
            url = f'https://{pk_get_headers["Host"]}/api/rankpk/get_reward?time={time_long}&session_id={session_id}'
            response = send_http2_request('GET', url, pk_get_headers, None)
            data = response.json()['data']
            pre_session_id = data['sessionId']
            money = data['money']
            yield f'{pre_session_id}赛季+{money}铜板'
        payload = [ # 进入页面
            {"index": 38, "extra_info": '{"trace":"together_tab","session_id":"%d","pk_rank":"%d"}'% (session_id, current_level)}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        
        time.sleep(1)

        payload = [ # 开始匹配
            {"index": 39, "without_login": True, "extra_info": '{"trace":"together_tab","session_id":"%d","pk_rank":"%d"}'% (session_id, current_level)}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)

        challenge_id = 0
        puzzle_count = 0
        side = ''
        rival_name = ''
        rival_avatar = ''
        time_start = time.time()
        if not allow_self:
            pkonline2_lock.acquire()
        while True:
            # https://pk.baicizhan.com/api/rankpk/challenge/match?challenge_type=word&challenge_level=wood&time=1728962245954&activity_id=0&session_id=40
            url = f'https://{pk_get_headers["Host"]}/api/rankpk/challenge/match?challenge_type=word&challenge_level={rank_name_en}&time={time_long}&activity_id=0&session_id={session_id}'
            response = send_http2_request('GET', url, pk_get_headers, None)
            data = response.json()['data']
            if not data.get('again', False): # 匹配成功
                challenge_id = data['challenge_id']
                puzzle_count = data['puzzle_count']
                side = data['side']
                rival_name = data['rival']['nickname']
                rival_avatar = data['rival']['avatar']
                break
            time.sleep(1)
        yield f'匹配对手:{rival_name}<br>'
        if not allow_self:
            pkonline2_lock.release()
        unique_id = find_unique_id(rival_avatar, nickname=rival_name)
        if unique_id != 'None':
            yield f'对手bczId:<font color="lemonchiffon">{unique_id}</font><br>'
        else:
            yield f'未找到对手bczId<br>'
        if unique_id in whitelist:
            yield f'白名单用户💖<br>'
        # yield f'共{puzzle_count}题'
        payload = [ # 匹配成功
            {"index": 40, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d,\"cost_time\":%d}"% (session_id, current_level, challenge_id, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        time.sleep(0.5)
        payload = [ # 初始化（重复发送3次等待）
            {"index": 41, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d,\"cost_time\":%d}"% (session_id, current_level, challenge_id, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        time.sleep(0.25)
        payload = [ # 初始化（重复发送3次等待）
            {"index": 42, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d,\"cost_time\":%d}"% (session_id, current_level, challenge_id, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        
        order = 0
        chosen_id = 0
        rival_answer = None
        rival_escaped = False
        my_answer = None
        right_answer = None
        current_time = 10000
        my_score = 0
        score_delta = 0
        rival_score = 0
        penalty = 0 # 对于过分快对手，提高速度
        my_penalty = 0 # 对于自己打错的，不计入分差
        topic_id = 0
        time_start = time.time()
        while order < puzzle_count: # 最后一题作答完毕之后，退出
            try:
                # https://pk.baicizhan.com/api/rankpk/challenge/heartbeat?activity_id=0
                # {"challenge_id":421585,"submit":null,"session_id":40}
                url = f'https://{pk_get_headers["Host"]}/api/rankpk/challenge/heartbeat?activity_id=0'
                content = {
                    "challenge_id": challenge_id,
                    "submit": None,
                    "session_id": session_id
                }
                content_str = json.dumps(content)
                while True:
                    response = send_http2_request('POST', url, pk_post_headers, content_str)
                    time.sleep(0.5)
                    data = response.json()['data']
                    if data['order'] != order:
                        break
                # 报告上一题
                if order > 0: # 第一题时，order还未赋值
                    score_str = f'{my_score}' if order > 1 else ''
                    payload = [
                        {"index": 43, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"topic_id\":%d,\"challenge_id\":%d,\"puzzle_order\":%d,\"score\":\"%s\",\"challenge_type\":\"排位赛\",\"cost_time\":%d}"% (session_id, current_level, topic_id, challenge_id, order, score_str, int(time.time() - time_start))}
                    ]
                    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
                    time_start = time.time()
                order = data['order']
                chosen_id, msg = word_lookup_puzzle_solver(data['puzzle'])
                topic_id = data['puzzle']['topicId']
                rival_escaped = data['rivalEscaped']
                rival_answer = data['rival']['answer']

                yield f'第{order}题 {msg}<br>'
                if unique_id in whitelist:
                    penalty = 0
                else:
                    penalty = rival_score - 186 * (order - 1)
                lb = 7100
                if rival_score + 32 <= my_score:
                    lb -= min((my_score - rival_score - 32) * 20, 1500) # 5600
                elif my_score < rival_score + 32:
                    lb += min((rival_score + 32 - my_score) * 40, 500) # 7600
                ub = max(lb + 500, 8600 - chosen_id * 300 + min(0, rival_score - my_score) * 40)
                target_time = random.randint(lb, ub) # 分数=答对100+剩余时间/100，每题满分200
                if penalty > 0:
                    target_time = min(8600 + penalty*200, 9999)
                    lb = ub = target_time
                    yield '[AC]'
                yield f'目标{int(100 + target_time/100)}({lb}-{ub})delta{max(penalty*1, 0)}<br>'
                
                current_time = data['puzzle']['cd']
                
                # {"challenge_id":421585,"nvcVal":"","submit":{"order":1,"answer":3},"session_id":40}
                content = {
                    "challenge_id": challenge_id,
                    "nvcVal": "",
                    "submit": {
                        "order": order,
                        "answer": chosen_id
                    },
                    "session_id": session_id
                }
                content_ans_str = json.dumps(content)
                modem_simulate = (random.randint(1, 5) == 1)

                while True:
                    response = send_http2_request('POST', url, pk_post_headers, content_str)
                    data = response.json()['data']
                    current_time = data['puzzle']['cd']
                    rival_answer = data['rival']['answer']
                    rival_escaped = data['rivalEscaped']
                    
                    if current_time < target_time or (rival_answer is not None and rival_answer == chosen_id):
                        # if modem_simulate and penalty < 3:  # 模拟网络意外延时，反挂除外
                            # time.sleep(0.5)
                        break
                    if current_time - 500 <= target_time and current_time < 10000:
                        time.sleep((current_time - target_time) / 1000)
                        break
                    time.sleep(0.4)
                

                response = send_http2_request('POST', url, pk_post_headers, content_ans_str)
                time.sleep(0.2)
                response = send_http2_request('POST', url, pk_post_headers, content_ans_str)
                time.sleep(0.2)
                data = response.json()['data']
                my_answer = data['me']['answer']
                while my_answer is None:
                    response = send_http2_request('POST', url, pk_post_headers, content_ans_str)
                    time.sleep(0.2)
                    data = response.json()['data']
                    my_answer = data['me']['answer']
                    me_escaped = data['meEscaped']
                    if me_escaped:
                        yield f'<font color="red">掉线，本轮结束</font><br>'
                        return
                score_delta = data['me']['score'] - my_score
                my_score = data['me']['score']
                right_answer = data['puzzle']['right_answer']
                if my_answer == right_answer:
                    yield f'✓{my_score}(+{score_delta})/'
                else:
                    my_penalty += 175
                    yield f'×{my_score}(+{score_delta})/'
                rival_answer = data['rival']['answer']
                rival_escaped = data['rivalEscaped']
                content = {
                    "challenge_id": challenge_id,
                    "submit": None,
                    "session_id": session_id
                }
                content_str = json.dumps(content)
                while rival_answer is None and not rival_escaped and current_time > 0:
                    response = send_http2_request('POST', url, pk_post_headers, content_str)
                    time.sleep(0.5)
                    data = response.json()['data']
                    rival_answer = data['rival']['answer']
                    rival_escaped = data['rivalEscaped']
                    current_time = data['puzzle']['cd']
                score_delta = data['rival']['score'] - rival_score
                rival_score = data['rival']['score']
                if rival_escaped:
                    yield f'对手逃跑<br>'
                    score_delta = -1
                elif rival_answer is None:
                    yield f'未作答<br>'
                    score_delta = -1
                else:
                    if rival_answer == right_answer:
                        yield f'✓{rival_score}(+{score_delta})<br>'
                    else:
                        my_penalty -= 150
                        yield f'×{rival_score}(+{score_delta})<br>'
                word_lookup_patcher(data['puzzle'], right_answer, topic_id, rank_name_en, score_delta)
                # 等待直到current_time为0
                while True:
                    response = send_http2_request('POST', url, pk_post_headers, content_str)
                    time.sleep(0.5)
                    data = response.json()['data']
                    current_time = data['puzzle']['cd']
                    rival_escaped = data['rivalEscaped']
                    if current_time == 0 or order != data['order']:
                        break
            except:
                yield traceback.format_exc()
                break # 有可能是睡眠导致比赛异常，退出即可
        # 最后一题作答完毕
        score_str = f'{my_score}' if order > 1 else ''
        payload = [
            {"index": 43, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"topic_id\":%d,\"challenge_id\":%d,\"puzzle_order\":%d,\"score\":\"%s\",\"challenge_type\":\"排位赛\",\"cost_time\":%d}"% (session_id, current_level, topic_id, challenge_id, order, score_str, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        payload = [
            {"index": 44, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d}" % (session_id, current_level, challenge_id)}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        # https://pk.baicizhan.com/api/rankpk/challenge/result?challenge_id=421585&side=left&time=1728962287864&activity_id=0&session_id=40
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/challenge/result?challenge_id={challenge_id}&side={side}&time={time_long}&activity_id=0&session_id={session_id}'
        response = send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        incr_score = data['incrScore']
        limited = data['limited']
        yield f'学习得分+{incr_score}'
        if limited:
            yield f' 达上限 '
        my_score = data['me']['score']
        rival_score = data['rival']['score']
        yield f' {my_score} - {rival_score} - '
        if my_score > rival_score:
            yield f'<font color="green">WIN</font><br>'
            total_win_round += 1
        elif my_score < rival_score:
            yield f'<font color="red">LOSE</font><br>'
        else:
            yield f'<font color="yellow">DRAW</font><br>'
        payload = [
            {"index": 45, "without_login": True, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\"}" % (session_id, current_level)} # pk结束
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        yield "<br><br>"
        delay = random.randint(3,6)
        for i in range(delay):
            yield f'.'
            time.sleep(1)

    return

def yzdd(user_cookie=user_cookie, user_config=user_config):
    '''一站到底'''
    # 2024.12.2已经结束
    return
    # 如果是星期日，跳过
    if datetime.datetime.now().weekday() == 6:
        return "$星期日，跳过"
    # https://pkonline2.baicizhan.com/api/contest/2024/one_fight/get_exam_question?bczId=0&day=
    time_long = int(time.time() * 1000)
    headers = getHeaders("$pkonline2", user_cookie, int(time.time()), index=1)
    url = f'https://{headers["Host"]}/api/contest/2024/one_fight/get_exam_question?bczId=0&day='
    response = send_http2_request('GET', url, headers, None)
    data = response.json()['data']

    conn = sqlite3.connect('yzdd.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS yzdd (
        INDEX_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        QID INTEGER,
        IMAGE TEXT,
        TITLE TEXT,
        ANSWER TEXT,
        OPTION_2 TEXT,
        OPTION_3 TEXT,
        OPTION_4 TEXT,
        DETAIL TEXT)
    ''')
    conn.commit()

    qid = data['qid']

    answered = True if (data.get('answer', 1) > 0) else False
    if not answered:
        # qid 查询数据库
        # https://pkonline2.baicizhan.com/api/contest/2024/one_fight/submit_exam
        # Content-Type: application/json; charset=UTF-8
        time.sleep(random.randint(2000, 4000) / 1000)
        headers = getHeaders("$pkonline2", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        url = f'https://{headers["Host"]}/api/contest/2024/one_fight/submit_exam'
        payload = {
            "qid": data['qid'],
            "answer": random.randint(1, 4)
        }
        response = send_http2_request('POST', url, headers, json.dumps(payload))
        time.sleep(0.9)

        # 重新请求题目
        # https://pkonline2.baicizhan.com/api/contest/2024/one_fight/get_exam_question?bczId=0&day=
        headers = getHeaders("$pkonline2", user_cookie, int(time.time()), index=1)
        url = f'https://{headers["Host"]}/api/contest/2024/one_fight/get_exam_question?bczId=0&day='
        response = send_http2_request('GET', url, headers, None)
        data = response.json()['data']


    
    title = data['title']
    answer_id = data['answer']
    image = data['image']
    detail = data['detail']
    options = []
    options.append(data['options'][answer_id-1]['content'])
    for i, option in enumerate(data['options']):
        if i != answer_id - 1:
            options.append(option['content'])
    cursor.execute('''SELECT * FROM yzdd WHERE QID == ?''', (qid, ))
    result = cursor.fetchone()
    if not result:
        cursor.execute('''INSERT INTO yzdd (QID, TITLE, IMAGE, ANSWER, OPTION_2, OPTION_3, OPTION_4, DETAIL) VALUES (?,?,?,?,?,?,?,?)''', (qid, title, image, options[0], options[1], options[2], options[3],detail))
        conn.commit()
    conn.close()
    return f'$今日题目:{title}:<img src="{image}" width="100px" height="100px"><br>正确答案:{options[0]}<br>选项1:{options[1]}<br>选项2:{options[2]}<br>选项3:{options[3]}<br>'

def deskmate_pk(cookie=user_cookie, config=user_config):
    '''同桌PK'''
    
    data = {}

    name = config['name']
    # random_delay = random.randint(0, random_delay_thresh)
    # while random_delay > 0:
        # yield (f'{name} 等待{random_delay}秒')
        # time.sleep(1)
        # random_delay -= 1

    # https://social.baicizhan.com/api/deskmate/game/start_word_match_game
    time_long = int(time.time() * 1000)
    headers = getHeaders('$social', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json'
    response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/start_word_match_game', headers, '{}')
    yield (f'{name} 开始每周双人战{response.json()}<br>')
    if response.json()['code'] == 100:
        yield f'出现问题，请检查<br>'
        return
    
    
    
    while True:
        # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
        time_long = int(time.time() * 1000)
        headers = getHeaders('$social', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json'
        response = send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
        data = response.json()['data']
        if data.get('needCompletedTopicList', None) is not None:
            break
        time.sleep(1)

    if data['newUserGuide']['status'] == 0:
        yield ('播放新手指南4s')
        # https://social.baicizhan.com/api/deskmate/game/finish_new_user_guide
        time_long = int(time.time() * 1000)
        headers = getHeaders('$social', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json'
        time.sleep(4)
        response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/finish_new_user_guide', headers, '{}')

    finish_all = False
    if time.localtime().tm_wday in [5,6]:
        finish_all = True

    while True:
        try:
            cnt = data['mine']['finishCount']
            deskmate_cnt = data['deskmate']['finishCount']
            # yield (cnt, deskmate_cnt)
            if finish_all and cnt + deskmate_cnt >= 100:
                break
            elif not finish_all and cnt >= 50:
                break
            topic_list = data['needCompletedTopicList']
            deskmate_completed_list = data['deskmate']['completedTopicList']
            my_completed_list = data['mine']['completedTopicList']
            finished_topic_ids = [t['topicId'] for t in deskmate_completed_list]
            finished_topic_ids.extend([t['topicId'] for t in my_completed_list])
            # 找第一个同桌未完成的题目
            found = - random.randint(0, 2)
            topic_id = -1
            
            for topic in topic_list:
                if topic['topicId'] not in finished_topic_ids:
                    found += 1
                    topic_id = topic['topicId']
                    topic_option = topic['topicOption']
                    if found > 0:
                        break
            if topic_id == -1:
                raise f'{name} 没有找到未完成的题目'

            time.sleep(random.randint(3000, 4000) / 1000)

            # https://social.baicizhan.com/api/deskmate/game/word_match
            # {"topicId":45,"topicOption":"疼痛"}
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            headers['Content-Type'] = 'application/json'
            response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/word_match', headers, json.dumps({"topicId":topic_id,"topicOption":topic_option}, ensure_ascii=False))
            response_json = response.json()['data']
            # 刷新
            while True:
                # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
                time_long = int(time.time() * 1000)
                headers = getHeaders('$social', cookie, time_long, index = 1)
                response = send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
                data = response.json()['data']
                if data['needCompletedTopicList'] is not None:
                    break
                time.sleep(1)
            
            cnt = data['mine']['finishCount']
            yield (f'完成第{cnt}次{response_json} <br>')
            if response_json['credit'] > 0:
                yield (f'铜板+{response_json["credit"]} <br>')
                time.sleep(0.5)
        except Exception as e:
            yield (f'{name} {e}')
    yield (f'{name} 每周双人战结束 <br>')

    if data['status'] == 3:# 结束
        if data['wordMatchReward']['status'] == 0:
            # https://social.baicizhan.com/api/deskmate/game/send_word_match_reward
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            headers['Content-Type'] = 'application/json'
            response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/send_word_match_reward', headers, '{}')

            # 检验是否领取成功
            # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            response = send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
            data = response.json()['data']
            if data['wordMatchReward']['status'] == 1:
                yield ('00 每周双人战奖励领取成功 <br>')
            else:
                yield ('01 领取失败 <br>')
        else:
            yield ('02 奖励已领取 <br>')
    else:
        yield ('03 等待同桌完成 <br>')


def get_class_range(user_config=user_config, total_user_cnt = 18, max_rank_cnt = 1000):
    user_index = int(user_config['user_index'])
    total_user_cnt = total_user_cnt
    # 获取今日日期
    today = datetime.datetime.now().strftime('%Y%m%d')
    # 获取日期最后一位
    # date_last_num = int(today[-1])
    # date_last_num = 0
    # 将这100个班级分成total_user_cnt份
    cnt = max_rank_cnt / total_user_cnt
    num_start = int(cnt * (user_index) + 1)
    num_end = int(cnt * (user_index + 1) )
    if user_index == total_user_cnt - 1:
        num_end = max_rank_cnt - 1
    # 组成班级范围
    # num_start += date_last_num * 100
    # num_end += date_last_num * 100
    # 限制班级范围防止一次性获取过多
    if num_end - num_start > 30:
        num_end = num_start + 30
    return num_start, num_end

def task_center(user_cookie=user_cookie, user_config=user_config, word_cnt=10, react_wait_seconds=1):
    # 获取不断电和学习分排行榜
    client_date = int(datetime.datetime.now().strftime('%Y%m%d'))
    def daily_summary_desc(client_date):
        # https://learn.baicizhan.com/api/study/win-streak/dailySummary?clientDate=20240817
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/dailySummary?clientDate={client_date}', headers, None)
        return response.json()
    
    
    data = daily_summary_desc(client_date)['data']
    score = data['score']
    if score is None:
        yield '还未打卡'
        score = 0
    rank = data['rank']
    win_streak_days = data['winStreakDays']
    if rank is None:
        raise Exception('学习记录异常')
    rank = rank['level']
    level_in_rank = 1
    for person in data['rank']['rankList']:
        if person.get('score', 0) > score:
            level_in_rank += 1

    yield f'{win_streak_days}天<br>学习分{score}排{rank}段第{level_in_rank}名'
    time.sleep(react_wait_seconds)

    def get_monthly_task_desc():
        # https://social.baicizhan.com/api/task/v2/getOneUnEndTask
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/task/v2/getOneUnEndTask', headers, None)
        return response.json()
    
    monthly_task_data = get_monthly_task_desc()['data']
    if monthly_task_data is None:
        progress = total = 'null'
    else:
        progress = monthly_task_data.get('progress', 'null')
        total = monthly_task_data.get('actionCnt', 'null')
    
    # yield f' 新任务{progress}/{total}'


    # 前往任务中心领取奖励
    def get_award(user_task_id, task_award_list):
        # https://social.baicizhan.com/api/task/v2/getAward?userTaskId=1631594
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/json'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/task/v2/getAward?userTaskId={user_task_id}', headers, content = '{}')
        data = response.json()
        if data.get('code', 0) == 1:
            return get_award_str(task_award_list)
        else:
            return f'失败{data.get("msg", "")}'
        
    def get_award_str(award_list):
        award_str = ''
        for award in award_list:
            award_str += f'{award["type"]}+{award["cnt"]} '
        return award_str

    def get_task_center_reward_desc(user_cookie, user_config):
        # https://social.baicizhan.com/api/task/v2/home

        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/task/v2/home', headers, None)
        data = response.json()['data']
        yield "任务中心：<br>"
        for task in data['taskList']:
            task_id = task['userTaskId']
            task_name = task['taskName']
            task_type = task['taskType']
            task_progress = task['progress']
            task_action_cnt = task['actionCnt']
            yield f'#{task_type}.{task_name}{task_progress}/{task_action_cnt} '
            payload = [
                {"index": 28, "extra_info": "{\"task_id\":%d}" % task_id}
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
            
            if task['status'] == 1:
                yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
            elif task['status'] == 0:
                if task_name == '加量学5个单词':
                    time.sleep(1.5)
                    user_study.user_study_upload_task_action(user_cookie=user_cookie, user_config=user_config, task_upload_req_list=[['learnMore', 5]])
                    time.sleep(3)
                    yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
                elif '单词PK' in task_name and '3' in task_name:
                    for msg in pkonline2(user_cookie, user_config, max_round=8, max_win_round=3):
                        yield msg
                    time.sleep(1.5)
                    yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
                elif '单词PK' in task_name and '1' in task_name:
                    for msg in pkonline2(user_cookie, user_config, max_round=8, max_win_round=1):
                        yield msg
                    time.sleep(1.5)
                    yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
                elif task_name == '单词速听复习10个单词':
                    time.sleep(1.5)
                # elif task_name == '完成今日学习计划':

                # elif taskname == '完成1局单词消消练':
                # 因为要花费50铜板，因此不做处理
                else:
                    yield '<br>'
                # 其他还没记录，先返回描述供开发
            # status == 2：任务已完成，奖励已领取
    
    
    if progress != 'null' and total != 'null':
        # 前往任务中心领取奖励
        time.sleep(react_wait_seconds)
        for msg in get_task_center_reward_desc(user_cookie, user_config):
            yield msg


    payload=[
        {"index": 16, "extra_info": "{\"word_num\":%d,\"experience\":%d}" % (word_cnt, score)} # 数据上传完成标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)

def sleep_actual(sleep_seconds):
    sleep_seconds *= 0.9
    index = random.randint(1, 100)
    if index < 5:
        time.sleep(sleep_seconds * index)
    time.sleep(sleep_seconds + index * 0.001)
    return

def learn_words(user_cookie=user_cookie, user_config=user_config, react_wait_seconds=1, word_count=5):
    unique_id = user_config['unique_id']
    
    yield f'{user_config["book_id"]}书'
    client_date = int(datetime.datetime.now().strftime('%Y%m%d'))


    # 打卡状态检查链接：https://group.baicizhan.com/group/study_words_together_home_page
    def check_if_daka():
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_cookie, int(time.time()), index = 1)
        url = 'https://group.baicizhan.com/group/study_words_together_home_page'
        response = send_http2_request('GET', url, headers=headers, content=None)
        response_json = response.json()
        return response_json['data']['todayDaka']
    
    if check_if_daka():
        yield '今天已经打卡过了<br>'

    def get_credit_status_desc(client_date):
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        url = f'https://{headers["Host"]}/api/study/xMode/getCreditStatus?date={client_date}'
        response = send_http2_request('GET', url, headers, None)
        result = response.json()
        if result['code'] == 1:
            return result['data']['inExperiment'], result['data']['studyCreditObtained'], result['data']['reviewCreditObtained']
        return False, False, False
    
    iE, sCO, rCO = get_credit_status_desc(client_date)
    if not iE:
        yield '没有拼写奖励 '
    elif sCO and rCO:
        yield '所有拼写奖励已领取 '
        
    # if (iE and (not sCO or not rCO)) or not today_daka:
    # 开始新学5个单词
    book_finished = False
    learn_list = getRandomWordIDInBook('lookup.db', user_config['book_id'], word_count, get_learnt_list(unique_id))
    if (len(learn_list) < word_count):
        yield '<p style="color:red;background-color:yellow">新词不足 重新学习本书或更换书本</p>'
        book_finished = True
        word_count = len(learn_list)
    yield f'本次{word_count}个词<br>'
    if book_finished:
        clear_learnt_list(unique_id)
        yield '已完成本书学习<br>'

    add_learnt_list(unique_id, learn_list)
    
    learnt_count = 0
    yield f'完成新学轮数：'
    for strategy_id in range(1, 4): # 图选、英选中、中选英
        for i in range(word_count):
            
            
            '''choice_topic_id -1斩,null拼写,其他正常'''
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], strategy_id)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            sleep_actual(1)
            
            # 选择单词
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":%d,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], strategy_id, learn_list[i])},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            learnt_count += 1
            if learnt_count == 5:
                # 上传win_streak_status
                yield str(user_study.user_study_submit_win_streak_records(user_cookie=user_cookie, user_config=user_config, client_date=client_date))
                # 疑似bug：user_study_submit_win_streak_records的client_date有默认值，但这个默认值可能是程序启动时的时间，导致跨天的打卡失败
            sleep_actual(react_wait_seconds)
            if strategy_id == 1:
                payload = [
                    {"index": 9, "extra_info": "{\"topic_id\":%d,\"book_id\":%d,\"channel\":\"study_mainstream\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], user_config['book_id'])}
                ]
                report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
                # 学习单词
                sleep_actual(1)
            yield '.'
        yield f'{strategy_id}'

    def daka_desc(word_count: int, unique_id: str, client_date: str):
        # 根据用户unique_id计算一个固定的timedelta，范围-1000s到0
        time_long = int(time.time() * 1000) - (int(hashlib.md5(str(unique_id).encode('utf-8')).hexdigest(), 16) % 1000000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/x-www-form-urlencoded'
        send_http2_request('POST', f'https://{headers["Host"]}/api/study/xMode/daka', headers, f'date={client_date}&count={word_count}')
        
    daka_desc(word_count, unique_id, client_date)
    # 拼写
    payload = [
        {"index": 10}# 开始拼写标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
    for i in range(word_count):
        payload = [
            {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], 4)},
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        sleep_actual(3.6)
        payload = [
            {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":null,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], 4)},
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        time.sleep(react_wait_seconds)
        yield '.'
        
    def receive_credit_desc(type: int, client_date: str):# 1 新学，2 复习
        type_str = 'study' if type == 1 else 'review'
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/study/xMode/receiveCredit?date={client_date}&type={type_str}', headers, None)
        result = response.json()
        return result['data']
    
    if iE and not sCO:
        yield f'拼写铜板x{receive_credit_desc(1, client_date)}<br>'
    else:
        yield '拼写完成<br>'

    payload=[
        {"index": 11}# 拼写完成标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
    payload=[
        {"index": 12}# 复习过渡页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)   
    time.sleep(react_wait_seconds)
    payload=[
        {"index": 13}# 复习过渡页点击
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)

    # 复习列表是今天学过的+昨天的单词，昨天的复习时斩掉
    yield '开始复习 '

    yesterday_list = get_history_learnt_list(unique_id, delta=1)
    the_day_before_list = get_history_learnt_list(unique_id, delta=2)
    review_count = len(yesterday_list)+len(the_day_before_list)
    yield f'共{review_count}个单词<br>'

    review_wrong_cnt = 0
    if review_count > 0:
        payload=[
            {"index": 14}# 复习开始
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        
        # 复习选择题
        yield '复习选择'
        for word in yesterday_list:
            # 昨天的单词：复习
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            sleep_actual(1)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":%d,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 2, word)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(react_wait_seconds)
            yield '.'
        
        yield ' 前天'
        for word in the_day_before_list:
            # 前天的单词：斩掉
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            sleep_actual(1)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":-1,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(react_wait_seconds)
            yield '.'

        # 复习拼写
        def save_study_record_desc(topic_id: int, book_id: int, sleep_time_ms: int, wrong=False):
            time_long = int(time.time() * 1000)
            headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
            headers['Content-Type']= 'application/json'
            payload = {}
            if wrong:
                payload = {
                    "bookId": int(book_id),
                    "topicId": int(topic_id),
                    "spellWrongTimes" : 1
                }
            else:
                payload = {
                    "bookId": int(book_id),
                    "topicId": int(topic_id),
                    "costMilliseconds": int(sleep_time_ms)
                }
            response = send_http2_request('POST', f'https://{headers["Host"]}/api/study/xMode/saveStudyRecord', headers, content=json.dumps(payload))
            
        yield ' 复习拼写'
        for word in yesterday_list:
            # 昨天的单词：拼写
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 4)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            sleep_time = (random.randint(3000, 6000) / 1000)
            if random.randint(1, 5) == 1:
                # 错题
                review_wrong_cnt += 1
                time.sleep(sleep_time)
                save_study_record_desc(word, user_config['book_id'], sleep_time * 1000, wrong=True)
                yield '`'
                extra_sleep_time = random.randint(3000, 5000) / 1000
                time.sleep(extra_sleep_time)
                save_study_record_desc(word, user_config['book_id'], (extra_sleep_time + sleep_time) * 1000)
            else:
                time.sleep(sleep_time)
                save_study_record_desc(word, user_config['book_id'], sleep_time * 1000)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":null,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 4)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(react_wait_seconds)
            yield '.'

        # 复习完成
        daka_desc(word_count + review_count, unique_id, client_date)
        if iE and not rCO:
            yield f' 复习铜板x{receive_credit_desc(2, client_date)} '
        else:
            yield ' 复习完成 '
        payload=[
            {"index": 15}# 复习完成标志
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
    
    def win_streak_status_desc() -> bool:
        # https://learn.baicizhan.com/api/study/win-streak/status
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/status', headers, None)
        return response.json()['data']
    

    if win_streak_status_desc():
        yield  '连胜'
    else:
        yield '连胜上传失败'
    
    def report_finish_daily_plan_desc(book_id, new_words_count, total_words_count, book_finished):
        # https://learn.baicizhan.com/api/study/reportFinishDailyPlan
        time_long = int(time.time() * 1000)
        payload = {
            "bookId": int(book_id),
            "totalWordsCount": int(total_words_count),
            "newWordsCount": int(new_words_count),
            "bookFinished": 'true' if (book_finished) else 'false'
        }
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/json'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/study/reportFinishDailyPlan', headers, content = json.dumps(payload))
        return response.json()
    
    report_finish_daily_plan_desc(user_config['book_id'], word_count, word_count + review_count, book_finished)

    word_done_data = {}
    for i in learn_list:
        word_done_data[i] = {
            "current_score": 3,
            "span_days": 0,
            "used_time": 0,
            "done_times": 4,
            "wrong_times": 0,
            "is_first_do_at_today": 1,
            "tag_id": 0,
            "spell_score": 3,
            "listening_score": 4,
            "chn_score": 3,
            "review_round": 0
        }
    # 数据收集非常水，span_days等等好几个字段都是废弃的
    for i in yesterday_list:
        word_done_data[i] = {
            "current_score": 5,
            "span_days": 0,
            "used_time": 0,
            "done_times": 4,
            "wrong_times": 0,
            "is_first_do_at_today": 0,
            "tag_id": 0,
            "spell_score": 3,
            "listening_score": 7,
            "chn_score": 3,
            "review_round": 0
        }
    for i in the_day_before_list:
        word_done_data[i] = {
            "current_score": 6,
            "span_days": 0,
            "used_time": 0,
            "done_times": 4,
            "wrong_times": 0,
            "is_first_do_at_today": 0,
            "tag_id": 0,
            "spell_score": 3,
            "listening_score": 7,
            "chn_score": 3,
            "review_round": 0
        }

    user_study.user_study_submit_experience_record(user_cookie=user_cookie, user_config=user_config, word_count=word_count, wrong_count=0, review_count=review_count, review_wrong_count=review_wrong_cnt)
    user_study.user_study_update_done_data(user_cookie=user_cookie, user_config=user_config, done_data=word_done_data)
    user_study.user_study_user_daka_v2(user_cookie=user_cookie, user_config=user_config)


    time.sleep(react_wait_seconds)
    yield ' 分享中.'
    # 返回首页去打卡
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
    # 获取打卡背景图
    result = user_study.get_daka_background_datas(learn_list, user_cookie=user_cookie, user_config=user_config)
    poster_id = result.category_info[0].image_ids[0]
    

    payload=[
        {"index": 17},# 点击去打卡
        {"index": 18, "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\"}" % poster_id},# 访问打卡页面
        {"index": 0}# heartbeat
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
    time.sleep(react_wait_seconds)
    yield '.'
    
    payload=[
        {"index": 19},# 点击分享到微信
        {"index": 20, 'extra_info': "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\", \"share_channel\":\"weixin\"}" % poster_id}# 点击打卡
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
    time.sleep(react_wait_seconds)
    yield '.'
    if social_send_share_success(user_cookie=user_cookie, user_config=user_config, channel=1):
        yield '分享成功'
    result = user_study.user_study_share_bonus(user_cookie=user_cookie, user_config=user_config)
    yield f'奖励+{result.coinCount}'
    time.sleep(react_wait_seconds)

    # 返回主页
    payload=[
        {"index": 21, "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\",\"share_channel\":\"weixin\"}" % poster_id}# 返回首页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
    yield ' 学习结束<br>'

    for msg in task_center(user_cookie=user_cookie, user_config=user_config, word_cnt=word_count + review_count):
        yield msg

def patch_win_streak(user_cookie, user_config):
    
    def win_streak_status_desc():
        # https://learn.baicizhan.com/api/study/win-streak/status
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/status', headers, None)
        return response.json()
    
    def daily_summary_desc(client_date):
        # https://learn.baicizhan.com/api/study/win-streak/dailySummary?clientDate=20240817
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/dailySummary?clientDate={client_date}', headers, None)
        return response.json()
    
    client_date = datetime.datetime.now().strftime('%Y%m%d')
    yield 'before:<br>'
    yield str(win_streak_status_desc())
    
    data = daily_summary_desc(client_date)['data']
    score = data['score']
    if score is None:
        score = 0
    rank = data['rank']
    win_streak_days = data['winStreakDays']
    if rank is None:
        Warning('学习记录异常')
        print(data)
        rank = level_in_rank = -1
    else:
        rank = rank['level']
        level_in_rank = 1
        for person in data['rank']['rankList']:
            if person['score'] > score:
                level_in_rank += 1

    yield f'{win_streak_days}天<br>学习分{score}排{rank}段第{level_in_rank}名'

    yield str(user_study.user_study_submit_win_streak_records(user_cookie=user_cookie, user_config=user_config, client_date=client_date))
    yield '<br>after:<br>'
    yield str(win_streak_status_desc())
    
    data = daily_summary_desc(client_date)['data']
    score = data['score']
    if score is None:
        score = 0
    rank = data['rank']
    win_streak_days = data['winStreakDays']
    if rank is None:
        Warning('学习记录异常')
        print(data)
        rank = level_in_rank = -1
    else:
        rank = rank['level']
        level_in_rank = 1
        for person in data['rank']['rankList']:
            if person['score'] > score:
                level_in_rank += 1

    yield f'{win_streak_days}天<br>学习分{score}排{rank}段第{level_in_rank}名'


def get_leader_info(members):
    for member in members:
        if member['leader'] == True:
            return member['uniqueId'], member['nickname']
    return '',''

def save_member_info(group_name, group_id, members, cursor: sqlite3.Cursor):
    # 保存成员信息
    table_name = 'MEMBERS'
    today_date = datetime.datetime.now().strftime('%Y%m%d')
    data_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for member in members:
        # member["uniqueId"]=int
        # 选取同一天、同一用户的最早打卡时间
        recorded_time = cursor.execute(
            f'SELECT COMPLETED_TIME FROM {table_name} WHERE USER_ID = ? AND TODAY_DATE = ? ORDER BY COMPLETED_TIME',
            (member['uniqueId'], today_date)
        ).fetchone()
        if recorded_time and recorded_time[0]!='' :
            recorded_time = int(recorded_time[0])
            if recorded_time != 0 and recorded_time < member['completedTime']:
                member['completedTime'] = recorded_time
            # 可能加入新的小班后，会产生更晚的时间，以早的为准

        # 选取同一用户的最早头像
        # avatar = cursor.execute(
        #     f'SELECT AVATAR FROM {table_name} WHERE USER_ID = ? AND (TODAY_DATE < ? OR GROUP_ID IS NOT ?) AND AVATAR IS NOT NULL',
        #     (member['uniqueId'], today_date, group_id)
        # ).fetchone()
        # if avatar and avatar[0]==member['avatar']:
        #     member['avatar'] = None
        member['avatar'] = None # 暂时不需要头像

        # 选取同一用户的最早昵称
        nickname = cursor.execute(
            f'SELECT NICKNAME FROM {table_name} WHERE USER_ID = ? AND (TODAY_DATE < ? OR GROUP_ID IS NOT ?) AND NICKNAME IS NOT NULL',
            (member['uniqueId'], today_date, group_id)
        ).fetchone()
        if nickname and nickname[0]==member['nickname']:
            member['nickname'] = None

        # 获取书本的HASH_ID
        hash_id = cursor.execute(
            f'SELECT HASH_ID FROM BOOK_NAME WHERE BOOK_NAME = ?',
            (member['bookName'],)
        ).fetchone()
        if hash_id is not None:
            member['bookName'] = hash_id[0]
        else:
            # 插入新的书本
            cursor.execute(
                f'INSERT INTO BOOK_NAME (BOOK_NAME) VALUES (?)',
                (member['bookName'],)
            )
            hash_id = cursor.execute(
                f'SELECT last_insert_rowid() FROM BOOK_NAME'
            ).fetchone()
            member['bookName'] = hash_id[0]

        cursor.execute(
            f'INSERT INTO {table_name} (USER_ID, TODAY_DATE, GROUP_ID, NICKNAME, GROUP_NICKNAME, COMPLETED_TIME, WORD_COUNT, STUDY_CHEAT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_NAME, AVATAR, DATA_TIME) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(USER_ID, TODAY_DATE, GROUP_ID) DO UPDATE SET'
            ' NICKNAME = excluded.NICKNAME, '
            'GROUP_NICKNAME = excluded.GROUP_NICKNAME, '
            'COMPLETED_TIME = excluded.COMPLETED_TIME, '
            'WORD_COUNT = excluded.WORD_COUNT, '
            'STUDY_CHEAT = excluded.STUDY_CHEAT, '
            'COMPLETED_TIMES = excluded.COMPLETED_TIMES, '
            'DURATION_DAYS = excluded.DURATION_DAYS, '
            'BOOK_NAME = excluded.BOOK_NAME, '
            'GROUP_NAME = excluded.GROUP_NAME, '
            'AVATAR = excluded.AVATAR, '
            'DATA_TIME = excluded.DATA_TIME',
            (
                member['uniqueId'],# *
                today_date, # *
                group_id, # *
                member['nickname'],
                None, # 此程序没有group_nickname获取
                member['completedTime'],
                member['todayWordCount'],
                member['todayStudyCheat'],
                member['completedTimes'],
                member['durationDays'],
                member['bookName'],
                None, # group_name，可以在notice表中根据group_id获取
                member['avatar'], # 对重复的avatar链接，只保留第一个
                None # data_time，对定时记录冷储存数据库无用
            )
        )
        # print(member['uniqueId'], member['nickname'], member['completedTime'], member['todayWordCount'], member['todayStudyCheat'], member['completedTimes'], member['durationDays'], member['bookName'], member['avatar'], data_time)


def notice_and_rank(user_cookie, user_config, total_user_cnt, daka_list: daka_list_class, target_rank):
    '''获取公告和排名'''
    # https://group.baicizhan.com/group/get_group_rank?rank=7
    target_class_list = daka_list.get_class_list(target_rank)

    # https://group.baicizhan.com/group/information?shareKey=
    class_rank_start, class_rank_end = get_class_range(user_config, total_user_cnt, len(target_class_list))
    data_list = []
    for i in range(class_rank_start, class_rank_end + 1):
        time_long = int(time.time() * 1000)
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        try:
            share_key = target_class_list[i - 1]['shareKey']
            response_json = send_http2_request('GET', f'https://{headers["Host"]}/group/information?shareKey={share_key}', headers, None, True)
            group_info = response_json['data']['groupInfo']
            group_info['members'] = response_json['data']['members']
            group_info['score'] = target_class_list[i - 1].get('score')
            
        except :
            yield (f'❌ → 获取到排名{target_rank}的班级列表失败，请检查网络或排名是否存在')
            yield f'({class_rank_start}, {class_rank_end}, {len(target_class_list)})'

        
        
        data_list.append( group_info )

        yield f'{target_rank}.{i}.{data_list[-1]["name"]}<br>'

        time.sleep(random.randint(1, 4))


    with lock:
        conn = daka_list.get_notice_and_rank_conn()
        cursor = conn.cursor()
        # 暂不再保存班级排名信息
        # if rank_type == 7 or rank_type == 6:
        #     # 对第六段位，只保存前100名
        #     if rank_type == 6:
        #         class_list = class_list[:100]
        #     for i, class_item in enumerate(class_list):
        #         class_share_key = class_item['shareKey']
        #         class_name = class_item['groupName']
        #         class_score = class_item['score']
        #         cursor.execute(f"INSERT OR IGNORE INTO notice (SHARE_KEY, NAME, RANK_TYPE, RANK, HASH_VALUE, CONTENT, DATE, SCORE) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        #                             (class_share_key, class_name, rank_type, i + 1, '', '', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), class_score))
        #     print(f'★ → 获取到排名{rank_type}的班级列表\n')  
        #     message_str += f'★{rank_type}'
        #     yield message_str

        curr_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        for i, group_info in enumerate(data_list):
            class_name = group_info['name']
            group_id = group_info['id']
            content = group_info['notice']
            introduction = group_info['introduction']
            if content == None or content == '':
                content = '(空)'
            share_key = group_info['shareKey']
            score = group_info['score']
            members = group_info['members']
            leader_id, leader_name = get_leader_info(members)
            save_member_info(class_name, group_id, members, cursor)

            hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()
            cursor.execute(f"SELECT NAME FROM notice WHERE HASH_VALUE='{hash_value}' AND SHARE_KEY='{share_key}'")
            result = cursor.fetchone()
            name_str = f'{class_name}(班长:{leader_name}[{leader_id}])\n介绍:{introduction}'
            if not result:
                print(f'❤️ → 获取到排名{i + class_rank_start}的班级{class_name}的通知\n')
                # 保存通知到数据库
                yield '.'
                cursor.execute("""
                    INSERT INTO notice (SHARE_KEY, GROUP_ID, NAME, RANK_TYPE, RANK, HASH_VALUE, CONTENT, DATE, SCORE, LATEST_DATE) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (share_key, group_id, name_str, target_rank, i + class_rank_start, hash_value, content, curr_time_str, score, None))
            else:
                yield '`'
                cursor.execute(f"UPDATE notice SET NAME=?, LATEST_DATE=?, GROUP_ID=? WHERE HASH_VALUE='{hash_value}' AND SHARE_KEY='{share_key}'", (name_str, curr_time_str, group_id))
                # 一定要记得所有并列更新用逗号，不是AND，不然会变成爆0机器（而且不报错！）
                print(f'🙈 → 排名{i + class_rank_start}的班级{class_name}的通知已存在数据库，跳过')

        conn.commit()
        conn.close()


def watch_daily_sentences(user_cookie, user_config):
    '''观看每日句子精讲'''
    # https://learn.baicizhan.com/api/activity/sentence/list
    headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
    headers['Content-Type']= 'application/json'
    response = send_http2_request('POST', f'https://{headers["Host"]}/api/activity/sentence/list', headers, '{"size":20}')
    data = response.json()['data']['data']
    for sentence in data:
        sentence_id = sentence['id']
        daka_num = sentence['dakaNum']
        cn = sentence['sentence']['cn']
        en = sentence['sentence']['en']
        sentence_source = sentence['sentenceSource']
        yield f'句子精讲 #{sentence_id} {daka_num}打卡'
        if user_config['user_index'] == 0:
            yield f'<br>{cn}<br>{en}<br>{sentence_source}'
        # https://learn.baicizhan.com/api/activity/sentence/sentence_daka
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/json'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/activity/sentence/sentence_daka', headers, content = f'{{"sentenceId":{sentence_id}}}')
        if response.json()['code'] == 1:
            yield ' 打卡成功 '
        # https://learn.baicizhan.com/api/activity/sentence/detail?sentenceId=882
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/activity/sentence/detail?sentenceId={sentence_id}', headers, None)
        if response.json()['code'] == 1:
            yield '获取详情成功<br>'
        break
    return

def patch_fun(user_cookie, user_config, react_wait_seconds):
    '''补丁函数'''
    # 补丁-任务中心
    for msg in task_center(user_cookie, user_config):
        yield msg
    time.sleep(react_wait_seconds)
    
    for msg in watch_daily_sentences(user_cookie, user_config):
        yield msg
    time.sleep(react_wait_seconds)

    # 补丁-连胜
    for msg in patch_win_streak(user_cookie, user_config):
        yield msg
    time.sleep(react_wait_seconds)

    # 补丁-任务中心
    for msg in task_center(user_cookie, user_config):
        yield msg


lock = threading.Lock()
def daka(daka_list: daka_list_class, user_cookie=user_cookie, user_config=user_config, total_user_cnt=18, only_rank_and_notice=-1):
    '''为用户打卡'''
    response_wait_second = 0.3
    react_wait_second = 0.9
    time_start = time.time()
    unique_id = user_config['unique_id']
    
    if daka_list.query(unique_id):
        return
    daka_list.add(unique_id)
    message_str = '#'
    client_date = int(datetime.datetime.now().strftime('%Y%m%d'))

    threading.Thread(target=heartbeat_demon, args=(daka_list, user_cookie, user_config)).start()

    # 临时函数放这里

    # only_rank_and_notice = 0
    # for msg in pkonline(user_cookie=user_cookie, user_config=user_config):
    #     message_str += msg
        # yield message_str

    # daka_list.remove(unique_id)
    # return 
    # 临时函数放这里

    if only_rank_and_notice != -1:
        for msg in notice_and_rank(user_cookie, user_config, total_user_cnt, daka_list, only_rank_and_notice):
            message_str += msg
            yield message_str
        daka_list.remove(unique_id)
        return 
    
    for msg in watch_daily_sentences(user_cookie, user_config):
        message_str += msg
        yield message_str
    time.sleep(react_wait_second)

    for msg in deskmate_pk(cookie=user_cookie, config=user_config):
        message_str += msg
        yield message_str
    time.sleep(react_wait_second)

    # pk # 1
    if random.randint(0, 1) == 1:
        for msg in pkonline(user_cookie=user_cookie, user_config=user_config, max_round=3):
            message_str += msg
            yield message_str
        time.sleep(react_wait_second)

    yield yzdd(user_cookie=user_cookie, user_config=user_config)
    if user_config.get('only_yzdd', "False") == "True":
        return
    
    message_str += '<br>开始背单词<br>'
    yield message_str
    word_count = int((user_config.get('user_index', 0) / 10 + 1) * 5)
    for msg in learn_words(user_cookie, user_config, react_wait_second, word_count):
        message_str += msg
        yield message_str
    time.sleep(react_wait_second)

    

    # 前往一起背领取打卡奖励
    def get_task_status_desc():
        
        # https://social.baicizhan.com/api/task/accept_task
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/task/accept_task', headers, '{}')

        # https://social.baicizhan.com/api/task/finish_task # 发一次空接收、完成请求以完成签到
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/task/finish_task', headers, '{}')
        
        #  https://group.baicizhan.com/group/study_words_together_home_page
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/group/study_words_together_home_page', headers, None)
        data = response.json()['data']

        # https://social.baicizhan.com/api/task/get_task_list
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/task/get_task_list', headers, None)
        tasklist = response.json()['data']['taskInfoVoList']
        state = 0
        daily_reward_obtained = True
        for task in tasklist:
            if task['showPriority'] == 1 and task['state'] == 1:
                daily_reward_obtained = False
            elif task['state'] == 1:
                    state += 1

        # https://social.baicizhan.com/api/deskmate/home_page
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/deskmate/home_page', headers, None)
        deskmate_data = response.json()['data']
        if deskmate_data is None or deskmate_data['deskmate'] is None:
            deskmate_daka_today = False
        else:
            deskmate_daka_today = deskmate_data['deskmate']['dakaToday']

        
        return data['haveDeskmate'], data['haveGroup'], data['haveOrdinaryGroup'], data['todayDaka'], data['receivedGroupRankRewards'], data['receivedGroupDailyRewards'], state, deskmate_daka_today, daily_reward_obtained
    
    have_deskmate, have_group, have_ordinary_group, today_daka, received_group_rank_rewards, received_group_daily_rewards, task_state, deskmate_daka_today, daily_reward_obtained = get_task_status_desc()
    if not today_daka:
        message_str += '打卡未同步 '
        time.sleep(5)
        have_deskmate, have_group, have_ordinary_group, today_daka, received_group_rank_rewards, received_group_daily_rewards, task_state, deskmate_daka_today, daily_reward_obtained = get_task_status_desc()
        if not today_daka:
            raise '打卡未同步'
        
    if task_state > 0:
        message_str += f'{task_state}任务请手领 '
        yield message_str

    def get_task_reward_desc(client_date):# 签到奖励

        # https://social.baicizhan.com/api/task/get_task_reward {"taskId":1,"receptionTime":20240817}
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        payload = {"taskId": 1, "receptionTime": client_date}
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/task/get_task_reward', headers, json.dumps(payload))
        return response.json()
    
    if not daily_reward_obtained and get_task_reward_desc(client_date)['code'] == 1:
        message_str += '签到+5 '
        yield message_str
        time.sleep(react_wait_second)

    
    def deskmate_daka_reward_desc(type):# 同桌打卡奖励
        # https://social.baicizhan.com/api/deskmate/daka_reward?type=1
        # 0自己；1同桌

        payload=[
            {"index": 22},# 点击领取同桌奖励(自己、同桌分别发送)
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)

        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/deskmate/daka_reward?type={type}', headers, '{}')
        return response.json()['data']


    if have_deskmate:
        
        message_str += f'自己份+{deskmate_daka_reward_desc(0)} '
        yield message_str
        time.sleep(react_wait_second)

        if deskmate_daka_today:
            message_str += f'同桌份+{deskmate_daka_reward_desc(1)} '
            yield message_str
            time.sleep(react_wait_second)
        
    def class_reward_desc(type):# 班级奖励
        payload=[
            {"index": 23 + type},# 点击领取班级奖励
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)

        time_long = int(time.time() * 1000)
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        if type == 0:
            # https://group.baicizhan.com/group/open_box?surprise=0
            response = send_http2_request('POST', f'https://{headers["Host"]}/group/open_box?surprise=0', headers, None)
        else:
            # https://group.baicizhan.com/group/receive_group_rank_award
            response = send_http2_request('POST', f'https://{headers["Host"]}/group/receive_group_rank_award', headers, None)
        return response.json()['data']['count']

    if have_group and not received_group_daily_rewards:
        message_str += f'班级日签+{class_reward_desc(0)} '
        yield message_str
        time.sleep(react_wait_second)
        if have_ordinary_group and not received_group_rank_rewards:
            message_str += f'班级段位+{class_reward_desc(1)} '
            yield message_str
            time.sleep(react_wait_second)

    # 商城日奖



    def get_daily_shop_reward_desc(client_date):
        # https://learn.baicizhan.com/api/mall/proxy/homepage/get_home_page_info
        # 获取今日是否已领日奖
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/homepage/get_home_page_info', headers, None)
        daily_credit_status = response.json()['data']['dailyCreditStatus']

        # https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit
        # 获取当前铜板数
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/creditmall/get_credit', headers, None)
        balance = response.json()['data']
        
        if not daily_credit_status:
            # https://learn.baicizhan.com/api/mall/proxy/homepage/get_daily_reward
            time_long = int(time.time() * 1000)
            headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
            response = send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/homepage/get_daily_reward', headers, None)
            return balance, response.json()['data']['credit']
        else:
            return balance, 0
    

    balance, daily_shop_reward_data = get_daily_shop_reward_desc(client_date)
    message_str += f'<br>商城日奖+{daily_shop_reward_data} 现有{balance + daily_shop_reward_data} '
    yield message_str
    time.sleep(react_wait_second)

    payload=[
        {"index": 25},# 点击
        {"index": 26} # 加载商城
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
    payload=[
        {"index": 27},# heartbeat
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
    time.sleep(react_wait_second)
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)

    # pk # 2
    for msg in pkonline(user_cookie=user_cookie, user_config=user_config, max_round=3):
        message_str += msg
        yield message_str

    # 前往个人中心
    result = user_study.user_study_credit_task_center(user_cookie=user_cookie, user_config=user_config)
    message_str += f'今日+{result.daily_inc_credit} '
    yield message_str

    # # 补丁-连胜
    # for msg in patch_win_streak(user_cookie, user_config):
    #     message_str += msg
    #     yield message_str

    # # 补丁-任务中心
    # for msg in task_center(user_cookie, user_config):
    #     message_str += msg
    #     yield message_str


    # 删除daka_list中的unique_id
    daka_list.remove(unique_id)

    message_str += f'耗时{time.time() - time_start:.2f}s'
    yield message_str

def daka_headless(daka_list: daka_list_class, unique_id, name, user_cnt, only_rank_and_notice, random_delay=1800):
    if only_rank_and_notice != -1:
        random_delay = 0
    delay = random.randint(1, max(user_cnt*5, random_delay))
    if name == "奶芋" or name == "星烛":
        delay = random_delay / 2
    message = ""
    index, user_dict = user_dict_obj.find(unique_id)
    user_dict['config']['user_index'] = index
    print(f"开始打卡:{name}，延迟{delay}s")
    time.sleep(delay)
    try:
        for msg in daka(daka_list, user_dict['cookie'], user_dict['config'], total_user_cnt=user_cnt, only_rank_and_notice=only_rank_and_notice):
            message = msg
    except Exception as e:
        err_str = traceback.format_exc()
        message += f'$打卡失败{e}{err_str}'
        print(err_str)
    message = F"延迟{delay}s后打卡\n" + message
    date_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    message = message.replace('<br>', '\n')
    with open(f'./logs/{name}.{unique_id}_{date_str}.txt', 'w', encoding='utf-8') as f:
        f.write(message)

def daka_all_headless(daka_list: daka_list_class, only_rank_and_notice):
    user_cnt = len(user_dict_obj.user_dict_list)
    for user_dict in user_dict_obj.user_dict_list:
        threading.Thread(target=daka_headless, args=(daka_list, user_dict['config']['unique_id'], user_dict['config']['name'], user_cnt, only_rank_and_notice)).start()

if __name__ == '__main__':
    cold_launch.example()

