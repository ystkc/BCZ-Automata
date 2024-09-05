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


default_headers = [
    {
        "Accept": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.1",
        "Cookie": {
            "access_token": "",
            "app_name": "7060100",
            "device_name": "android%2FDCO-AL00-HUAWEI",
            "client_time": "",
            "device_id": "",
            "serial": "",
            "channel": "qq",
            "version": "12"
        },
        "Compress-Type": "gzip",
        "content-encoding": "gzip",
        "Content-Type": "application/x-thrift",
        # "Transfer-Encoding": "chunked",
        "Host": "system.baicizhan.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    },{
        "Host": "group.baicizhan.com",
        "Connection": "keep-alive",
        "User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI",
        # "Content-Type": "application/json; charset=UTF-8",
        "Accept": "*/*",
        "X-Requested-With": "com.jiongji.andriod.card",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        # "Referer": "https://group.baicizhan.com/study_together",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": {
            "access_token": "",
            "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
            "device_name": "android/DCO-AL00-HUAWEI",
            "bcz_dmid": "2a16dfbb",
            "device_version": "12",
            "device_id": "",
            "app_name": "7060100",
            "channel": "qq",
            "client_time": "",
            "serial": ""
        }
    }
]

bcz_info = {
    'short_version': '7.6.1',
    'long_version': 7060100,
    "device_model": "DCO-AL00",
    "device_manufacturer": "HUAWEI",
    "os_name": "android",
    "os_sdk": '32',
    "app_name": "baicizhan",
    "oaid": "unknown"
}
def get_device_str(device_id):
    return f"{bcz_info['device_model']}-{bcz_info['device_manufacturer']}-{device_id}"

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
        if self.modified:
            with open("user_cookie.json", 'w', encoding='utf-8') as f:
                json.dump(self.user_dict_list, f, indent=4)
            self.modified = False
    
    def find(self, unique_id):
        unique_id = int(unique_id)
        for i in range(len(self.user_dict_list)):
            if self.user_dict_list[i]['config']['unique_id'] == unique_id:
                return self.user_dict_list[i]
        return None
    
    def update_book_id(self, unique_id, book_id):
        user = self.find(unique_id)
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
    {# 23 班级段位奖励
        "log_time": "1723852064583",
        "product_id": "bcz_app_h5",
        "stat_group": "explore-common",
        "event_id": "together_recite_click",
        "extra_info": "{\"button\":\"coin\",\"channel\":\"class_level\"}"
    },
    {# 24 点击商城
        "event_id": "mall-tab-click",
        "log_time": "1723852206439",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 25 加载商城
        "event_id": "mall-tab-click_extra_v2",
        "extra_info": "{\"servertype\":1,\"imageurl\":\"https://vol-v6.bczcdn.com/r/ltxwm285a8njpqetlsmf66453zsulws4.png\",\"taobaoinstalled\":false,\"aid\":\"10000\",\"jumptype\":1}",
        "log_time": "1723852206446",
        "product_id": "bcz_app",
        "stat_group": "h5-error"
    },
    {# 26 商城heartbeat
        "log_time": "1723852214632",
        "product_id": "bcz_app_h5",
        "stat_group": "bcz-mall-common",
        "event_id": "mall_carousel_show",
        "extra_info": "{\"trace\":\"bcz_app_main\",\"_path\":\"/homeV2\",\"banner_idx\":2,\"link_url\":\"https://learn.baicizhan.com/new_copper/link-to-duiba?linkTo=https%3A%2F%2Factivity-6.m.duiba.com.cn%2Fhdtool%2Findex%3Fid%3D272751389954266%26dbnewopen\"}"
    }





]




# 实际上，host_dict是有初始值的，只是在启动时会和服务器更新
host_dict = {
    'RES': ['https://vol-v6.bczcdn.com', 'https://7n-backup.bczcdn.com'],
    'DATA': ['https://www.baicizhan.com', 'https://www.bczeducation.cn', 'http://www.baicizhan.com', 'http://www.bczeducation.cn'],
    'activity': ['https://activity.baicizhan.com', 'https://activity.bczeducation.cn', 'http://activity.baicizhan.com', 'http://activity.bczeducation.cn'],
    'learn': ['https://learn.baicizhan.com', 'https://learn.bczeducation.cn', 'http://learn.baicizhan.com', 'http://learn.bczeducation.cn'],
    'resource': ['https://resource.baicizhan.com', 'https://resource.bczeducation.cn', 'http://resource.baicizhan.com', 'http://resource.bczeducation.cn'],
    'mall': ['https://mall.baicizhan.com', 'http://mall.baicizhan.com'],
    'assistant': ['https://assistant.baicizhan.com', 'https://assistant.bczeducation.cn', 'http://assistant.baicizhan.com', 'http://assistant.bczeducation.cn'],
    'conan': ['https://conan.baicizhan.com', 'http://conan.baicizhan.com'],
    'avatar': ['https://avatar.baicizhan.com', 'http://avatar.baicizhan.com'],
    'notify': ['https://notify.baicizhan.com', 'https://notify.bczeducation.cn', 'http://notify.baicizhan.com', 'http://notify.bczeducation.cn'],
    'mywordfavorites': ['https://booklist.baicizhan.com', 'https://booklist.bczeducation.cn', 'http://booklist.baicizhan.com', 'http://booklist.bczeducation.cn'],
    'system': ['https://system.baicizhan.com', 'https://system.bczeducation.cn', 'http://system.baicizhan.com', 'http://system.bczeducation.cn'],
    'passport': ['https://passport.baicizhan.com', 'https://passport.bczeducation.cn', 'http://passport.baicizhan.com', 'http://passport.bczeducation.cn'],
    'report': ['https://events.baicizhan.com', 'https://events.bczeducation.cn', 'http://events.baicizhan.com', 'http://events.bczeducation.cn'],
    'course': ['https://learn.baicizhan.com', 'https://learn.bczeducation.cn', 'http://learn.baicizhan.com', 'http://learn.bczeducation.cn'],
    'pk': ['https://pk.baicizhan.com', 'https://pk.bczeducation.cn', 'http://pk.baicizhan.com', 'http://pk.bczeducation.cn'],
    'advertise': ['https://advertise.baicizhan.com', 'https://advertise.bczeducation.cn', 'http://advertise.baicizhan.com', 'http://advertise.bczeducation.cn'],
    'group': ['https://group.baicizhan.com', 'https://group.bczeducation.cn', 'http://group.baicizhan.com', 'http://group.bczeducation.cn'],
    'social': ['https://social.baicizhan.com', 'https://social.bczeducation.cn', 'http://social.baicizhan.com', 'http://social.bczeducation.cn'],
    "pkonline":['https://pkonline2.baicizhan.com']
}

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

def getHeaders(host: str, user_cookie: dict, time_long: int, wrap_url: str = '', index = 0):
    '''path的前后都不加左斜杠
    返回headers(非wrap_url)，返回headers_str(wrap_url)'''
    headers = default_headers[index].copy()
    # 将cookie中的时间戳更新
    for k, _ in headers['Cookie'].items():
        if k == 'client_time':
            headers['Cookie'][k] = str(time_long)
        elif k =='serial':
            device_id = headers['Cookie']['device_id']
            headers['Cookie'][k] = f"{device_id[:6]}{device_id[13:]}{str(time_long & 67108863)}"
        else:
            # 由于user_cookie并不是所有接口都需要的，所以需要判断一下
            headers['Cookie'][k] = user_cookie[k]
    # 将cookie转换为字符串
    headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in headers['Cookie'].items()])
    if host[0] == '$':
        # 需要将目标中的https://或http://去掉
        parsed = host_dict[host[1:]][0].split('://')
    else:
        parsed = host.split('://')
    if len(parsed) == 1:
        protocol = 'http'
    else:
        protocol = parsed[0]
    headers['Host'] = parsed[-1]
    
    if wrap_url == '':
        return headers
    
    # 生成用于socket的请求头
    # 将headers连接成字符串
    result = '\r\n'.join([f'{k}: {v}' for k, v in headers.items()])
    # 还差第一行的请求行
    return f'{result}\r\n\r\n'
    


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
def send_http2_request(method, url, headers, content):
    '''
    使用了http2尽可能复用tunnel，但5s闲置会断开连接
    此处没有gzip'''
    
    global client
    if client is None or client.is_closed:
        client = httpx.Client(http2=True, verify=certifi.where())

    client.headers.clear()  
    client.headers.update(headers)
    if method == 'POST':
        return client.post(url, data=content)
    elif method == 'GET':
        return client.get(url)
    elif method == 'OPTIONS':
        return client.options(url)
    else:
        return Exception('method not support')
    
class bcz_system:
    
    def bcz_system_check_infos(user_cookie=user_cookie, user_config=user_config):
        '''check_infos'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_check_infos()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, time_long)
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
        headers = getHeaders("$system", user_cookie, time_long)
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
        headers = getHeaders("$system", user_cookie, time_long)
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
        headers = getHeaders("$system", user_cookie, time_long)
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
        headers = getHeaders("$system", user_cookie, time_long)
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
        headers = getHeaders("$system", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$advertise", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        client.send_submit_win_streak_records(client_date=client_date, win_streak_dates=[client_date])
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, time_long)
        url = f'https://{headers["Host"]}/rpc/user_study/submit_win_streak_records/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_submit_win_streak_records()
        transport.close()

        return result


    def user_study_get_books_replace_info(user_cookie=user_cookie, user_config=user_config):
        '''get_books_replace_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_books_replace_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
        url = f'https://{headers["Host"]}/rpc/user_study/user_daka_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
        url = f'https://{headers["Host"]}/rpc/user_study/update_done_data/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
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
        headers = getHeaders("$learn", user_cookie, time_long)
        url = f'https://{headers["Host"]}/rpc/user_study/submit_experience_record/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = send_http2_request('POST', url, headers, content)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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
        headers = getHeaders("$learn", user_cookie, time_long)
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


    

class unified_user:
    def unified_user_get_bind_info(user_cookie=user_cookie, user_config=user_config):
        '''get_bind_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        client.send_get_bind_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$passport", user_cookie, time_long)
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
        headers = getHeaders("$passport", user_cookie, time_long)
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
        headers = getHeaders("$assistant", user_cookie, time_long)
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
        headers = getHeaders("$assistant", user_cookie, time_long)
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
        headers = getHeaders("$assistant", user_cookie, time_long)
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
            jsons.append(json.dumps(json_dict))
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
        headers = getHeaders("$report", user_cookie, time_long)
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
            headers = getHeaders('$report', user_cookie, time_long, index=1)
            # https://events.baicizhan.com/api/system/report_event
        else:
            headers = getHeaders('$system', user_cookie, time_long, index=1)
        headers['Content-Type'] = 'text/plain'

            # https://system.baicizhan.com/api/system/report_event
        url = f'https://{headers["Host"]}/api/system/report_event'
        result = send_http2_request('POST', url, headers, json.dumps(get_report_event_jsons(jsons, False)))

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
    headers = getHeaders("$notify", user_cookie, time_long)
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
    headers = getHeaders("$notify", user_cookie, time_long)
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
    headers = getHeaders("$resource", user_cookie, time_long)
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
    headers = getHeaders("$DATA", user_cookie, time_long)
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
daka_list = []
def heartbeat_demon(user_cookie=user_cookie, user_config=user_config):
    unique_id = user_config['unique_id']
    while unique_id in daka_list:
        payload=[
            {"index":0}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
        for i in range(30):
            time.sleep(1)
            if unique_id not in daka_list:
                break

def yzdd(user_cookie=user_cookie, user_config=user_config):
    '''一站到底'''
    # https://pkonline2.baicizhan.com/api/contest/2024/one_fight/get_exam_question?bczId=0&day=
    time_long = int(time.time() * 1000)
    headers = getHeaders("$pkonline", user_cookie, time_long, index=1)
    url = f'https://{headers["Host"]}/api/contest/2024/one_fight/get_exam_question?bczId=0&day='
    response = send_http2_request('GET', url, headers, None)
    data = response.json()['data']

    conn = sqlite3.connect('yzdd.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS yzdd (
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
        headers = getHeaders("$pkonline", user_cookie, time_long, index=1)
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
        headers = getHeaders("$pkonline", user_cookie, time_long, index=1)
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


def daka(user_cookie=user_cookie, user_config=user_config, only_yzdd=False):
    '''为用户打卡'''
    yield yzdd(user_cookie=user_cookie, user_config=user_config)
    if only_yzdd or user_config.get('only_yzdd', "False") == "True":
        return

    unique_id = user_config['unique_id']
    word_count = user_config.get('word_count', 5)
    
    response_wait_second = 0.3
    react_wait_second = 0.9
    message_str = f'#{user_config["book_id"]}书'
    yield message_str
    client_date = int(datetime.datetime.now().strftime('%Y%m%d'))

    global daka_list
    daka_list.append(unique_id)
    threading.Thread(target=heartbeat_demon, args=(user_cookie, user_config)).start()

    # 打卡状态检查链接：https://group.baicizhan.com/group/study_words_together_home_page
    def get_credit_status_desc(client_date):
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
        url = f'https://{headers["Host"]}/api/study/xMode/getCreditStatus?date={client_date}'
        response = send_http2_request('GET', url, headers, None)
        result = response.json()
        if result['code'] == 1:
            return result['data']['inExperiment'], result['data']['studyCreditObtained'], result['data']['reviewCreditObtained']
        return False, False, False
    
    iE, sCO, rCO = get_credit_status_desc(client_date)
    if not iE:
        message_str += '没有拼写奖励 '
        yield message_str
    message_str += f'本次{word_count}个词<br>'
    yield message_str
    # 开始新学5个单词
    book_finished = False
    learn_list = getRandomWordIDInBook('lookup.db', user_config['book_id'], word_count, get_learnt_list(unique_id))
    if (len(learn_list) < word_count):
        message_str += '新词不足 '
        yield message_str
        book_finished = True
        word_count = len(learn_list)

    add_learnt_list(unique_id, learn_list)
    
    learnt_count = 0
    message_str += f'完成新学轮数：'
    yield message_str
    for strategy_id in range(1, 4): # 图选、英选中、中选英
        for i in range(word_count):
            
            
            '''choice_topic_id -1斩,null拼写,其他正常'''
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], strategy_id)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(random.randint(1000, 2000) / 1000)
            # 选择单词
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":%d,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], strategy_id, learn_list[i])},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            learnt_count += 1
            if not sCO and learnt_count == 5:
                # 上传win_streak_status
                user_study.user_study_submit_win_streak_records(user_cookie=user_cookie, user_config=user_config)
            time.sleep(response_wait_second)
            if strategy_id == 1:
                payload = [
                    {"index": 9, "extra_info": "{\"topic_id\":%d,\"book_id\":%d,\"channel\":\"study_mainstream\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], user_config['book_id'])}
                ]
                report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
                # 学习单词
                time.sleep(random.randint(1000, 2000) / 1000)
            message_str += '.'
            yield message_str
        message_str += f'{strategy_id}'
        yield message_str

    def daka_desc(word_count: int, unique_id: str, client_date: str):
        # 根据用户unique_id计算一个固定的timedelta，范围-1000s到0
        time_long = int(time.time() * 1000) - (int(hashlib.md5(str(unique_id).encode('utf-8')).hexdigest(), 16) % 1000000)
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
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
        time.sleep(random.randint(3000, 6000) / 1000)
        payload = [
            {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":null,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], 4)},
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        time.sleep(response_wait_second)
        message_str += '.'
        yield message_str
        
    def receive_credit_desc(type: int, client_date: str):# 1 新学，2 复习
        type_str = 'study' if type == 1 else 'review'
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/study/xMode/receiveCredit?date={client_date}&type={type_str}', headers, None)
        result = response.json()
        return result['data']
    
    if iE and not sCO:
        message_str += f'拼写铜板x{receive_credit_desc(1, client_date)}<br>'
    else:
        message_str += '拼写完成<br>'
    yield message_str

    payload=[
        {"index": 11}# 拼写完成标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
    payload=[
        {"index": 12}# 复习过渡页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)   
    time.sleep(response_wait_second)
    payload=[
        {"index": 13}# 复习过渡页点击
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)

    # 复习列表是今天学过的+昨天的单词，昨天的复习时斩掉

    message_str += '开始复习 '
    yield message_str

    yesterday_list = get_history_learnt_list(unique_id, delta=1)
    the_day_before_list = get_history_learnt_list(unique_id, delta=2)
    review_count = len(yesterday_list)+len(the_day_before_list)
    message_str += f'共{review_count}个单词<br>'

    review_wrong_cnt = 0
    if review_count > 0:
        payload=[
            {"index": 14}# 复习开始
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
        
        # 复习选择题
        message_str += '复习选择'
        yield message_str
        for word in yesterday_list:
            # 昨天的单词：复习
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(random.randint(1000, 2000) / 1000)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":%d,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 2, word)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(response_wait_second)
            message_str += '.'
            yield message_str
        
        message_str += ' 前天'
        yield message_str
        for word in the_day_before_list:
            # 前天的单词：斩掉
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(random.randint(1000, 1500) / 1000)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":-1,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            time.sleep(response_wait_second)
            message_str += '.'
            yield message_str

        # 复习拼写
        def save_study_record_desc(topic_id: int, book_id: int, sleep_time_ms: int, wrong=False):
            time_long = int(time.time() * 1000)
            headers = getHeaders("$learn", user_cookie, time_long, index=1)
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
            
        message_str += ' 复习拼写'
        yield message_str
        for word in yesterday_list:
            # 昨天的单词：拼写
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 4)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
            sleep_time = (random.randint(3000, 6000) / 1000)
            if random.randint(1, 4) == 1:
                # 错题
                review_wrong_cnt += 1
                time.sleep(sleep_time)
                save_study_record_desc(word, user_config['book_id'], sleep_time * 1000, wrong=True)
                message_str += '`'
                yield message_str
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
            time.sleep(response_wait_second)
            message_str += '.'
            yield message_str

        # 复习完成
        daka_desc(word_count + review_count, unique_id, client_date)
        if iE and not rCO:
            message_str += f' 复习铜板x{receive_credit_desc(2, client_date)} '
        else:
            message_str += ' 复习完成 '
        yield message_str
        payload=[
            {"index": 15}# 复习完成标志
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)
    
    def win_streak_status_desc() -> bool:
        # https://learn.baicizhan.com/api/study/win-streak/status
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/status', headers, None)
        return response.json()['data']
    

    if win_streak_status_desc():
        message_str += '连胜'
        yield message_str
    else:
        message_str += '连胜上传失败'
        yield message_str
    
    def report_finish_daily_plan_desc(book_id, new_words_count, total_words_count, book_finished):
        # https://learn.baicizhan.com/api/study/reportFinishDailyPlan
        time_long = int(time.time() * 1000)
        payload = {
            "bookId": int(book_id),
            "totalWordsCount": int(total_words_count),
            "newWordsCount": int(new_words_count),
            "bookFinished": 'true' if (book_finished) else 'false'
        }
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
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

    # 获取不断电和学习分排行榜
    def daily_summary_desc(client_date):
        # https://learn.baicizhan.com/api/study/win-streak/dailySummary?clientDate=20240817
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/dailySummary?clientDate={client_date}', headers, None)
        return response.json()
    
    
    data = daily_summary_desc(client_date)['data']
    score = data['score']
    rank = data['rank']
    win_streak_days = data['winStreakDays']
    if rank is None:
        raise Exception('学习记录异常')
    rank = rank['level']
    level_in_rank = 1
    for person in data['rank']['rankList']:
        if person['score'] > score:
            level_in_rank += 1

    def get_monthly_task_desc():
        # https://social.baicizhan.com/api/task/v2/getOneUnEndTask
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, time_long, index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/task/v2/getOneUnEndTask', headers, None)
        return response.json()
    
    monthly_task_data = get_monthly_task_desc()['data']
    if monthly_task_data is None:
        progress = total = 'null'
    else:
        progress = monthly_task_data.get('progress', 'null')
        total = monthly_task_data.get('actionCnt', 'null')

    message_str += f'{win_streak_days}天<br>学习分{score}排{rank}段第{level_in_rank}名 月任务{progress}/{total}<br>分享中'
    yield message_str
    
    payload=[
        {"index": 16, "extra_info": "{\"word_num\":%d,\"experience\":%d}" % (word_count + review_count, score)} # 数据上传完成标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)

    time.sleep(react_wait_second)
    message_str += '.'
    yield message_str
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
    time.sleep(react_wait_second)
    message_str += '.'
    yield message_str
    
    payload=[
        {"index": 19},# 点击分享到微信
        {"index": 20, 'extra_info': "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\", \"share_channel\":\"weixin\"}" % poster_id}# 点击打卡
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
    time.sleep(react_wait_second)
    message_str += '.'
    yield message_str
    if social_send_share_success(user_cookie=user_cookie, user_config=user_config, channel=1):
        message_str += '分享成功'
        yield message_str
    result = user_study.user_study_share_bonus(user_cookie=user_cookie, user_config=user_config)
    time.sleep(react_wait_second)
    message_str += f'奖励+{result.coinCount}<br>'
    yield message_str

    # 返回主页
    payload=[
        {"index": 21, "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\",\"share_channel\":\"weixin\"}" % poster_id}# 返回首页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)

    # 前往一起背领取打卡奖励
    def get_task_status_desc():
        
        # https://social.baicizhan.com/api/task/accept_task
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, time_long, index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/task/accept_task', headers, '{}')

        # https://social.baicizhan.com/api/task/finish_task # 发一次空接收、完成请求以完成签到
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, time_long, index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = send_http2_request('POST', f'https://{headers["Host"]}/api/task/finish_task', headers, '{}')
        
        #  https://group.baicizhan.com/group/study_words_together_home_page
        time_long = int(time.time() * 1000)
        headers = getHeaders("$group", user_cookie, time_long, index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/group/study_words_together_home_page', headers, None)
        data = response.json()['data']

        # https://social.baicizhan.com/api/task/get_task_list
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, time_long, index=1)
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
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, time_long, index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/deskmate/home_page', headers, None)
        deskmate_data = response.json()['data']
        if deskmate_data['deskmate'] is None:
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
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, time_long, index=1)
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
        headers = getHeaders("$social", user_cookie, time_long, index=1)
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
            {"index": 23},# 点击领取班级奖励
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=0)

        time_long = int(time.time() * 1000)
        headers = getHeaders("$group", user_cookie, time_long, index=1)
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
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/homepage/get_home_page_info', headers, None)
        daily_credit_status = response.json()['data']['dailyCreditStatus']

        # https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit
        # 获取当前铜板数
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, time_long, index=1)
        response = send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/creditmall/get_credit', headers, None)
        balance = response.json()['data']
        
        if not daily_credit_status:
            # https://learn.baicizhan.com/api/mall/proxy/homepage/get_daily_reward
            time_long = int(time.time() * 1000)
            headers = getHeaders("$learn", user_cookie, time_long, index=1)
            response = send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/homepage/get_daily_reward', headers, None)
            return balance, response.json()['data']['credit']
        else:
            return balance, 0
    

    balance, daily_shop_reward_data = get_daily_shop_reward_desc(client_date)
    message_str += f'<br>商城日奖+{daily_shop_reward_data} 现有{balance + daily_shop_reward_data} '
    yield message_str
    time.sleep(react_wait_second)

    payload=[
        {"index": 24},# 点击
        {"index": 25} # 加载商城
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=0)
    payload=[
        {"index": 26},# heartbeat
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)
    time.sleep(react_wait_second)
    report_event(user_cookie=user_cookie, user_config=user_config, jsons=payload, type=1, host=1)

    # 前往个人中心
    result = user_study.user_study_credit_task_center(user_cookie=user_cookie, user_config=user_config)
    message_str += f'今日+{result.daily_inc_credit}'
    yield message_str


    # 删除daka_list中的unique_id
    new_daka_list = []
    for i in daka_list:
        if i != unique_id:
            new_daka_list.append(i) 
    daka_list = new_daka_list

    



if __name__ == '__main__':
    cold_launch.example()

