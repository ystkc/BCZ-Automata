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
import gzip
import struct
import time
import json
import asyncio
import httpx
import certifi
import datetime
import sqlite3
import random
import threading


default_headers = {
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
}

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

with open("user_cookie.json", 'r', encoding='utf-8') as f:
    user_dict_list = json.load(f)
    user_cookie = user_dict_list[0]['cookie'] # 默认第一个是咕咕
    user_config = user_dict_list[0]['config']
    # config中包含book_id
    # 410：中考词汇

report_json = [
    {
        "event_id": "bcz_active_heartbeat_detail",
        "extra_info": "{\"period\":30,\"plan_type\":\"\"}",
        "log_time": "1725061321587",
        "product_id": "bcz_app",
        "stat_group": "heartbeat-common"
    },
    {
        "event_id": "close-notify",
        "extra_info": "{\"adv_id\":\"100240167527175029\"}",
        "log_time": "1723850458343",
        "notify_title": "100240167527175029",
        "product_id": "bcz_app",
        "stat_group": "notify-popup"
    },
    {
        "event_id": "enter-main-view",
        "log_time": "1725062704325",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {
        "event_id": "homepage-book-adv-show",
        "extra_info": "{\"adv_id\":\"100213198904513909\",\"id\":\"100213198904513909\",\"book_id\":\"410\"}",
        "log_time": "1725062704865",
        "product_id": "bcz_app",
        "stat_group": "adv-common"
    },
    {
        "event_id": "homepage-banner-show",
        "extra_info": "{\"adv_id\":\"166102\",\"id\":\"166102\"}",
        "log_time": "1725063038669",
        "product_id": "bcz_app",
        "stat_group": "adv-common"
    },
    {
        "event_id": "push_curr_permission",
        "extra_info": "{\"status\":\"1\"}",
        "log_time": "1725063038837",
        "product_id": "bcz_app",
        "stat_group": "push-common"
    },
    {
        "event_id": "cold_launch",
        "extra_info": "{\"device_id\":\"DCO-AL00-HUAWEI-8d946f2ddaf90f18\",\"channel\":\"Rongyao\"}",
        "log_time": "1725063036294",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
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
    'advertise': ['https://advertise.baicizhan.com', 'https://advertise.bczeducation.cn', 'http://advertise.baicizhan.com', 'http://advertise.bczeducation.cn']
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

def getHeaders(host: str, user_cookie: dict, time_long: int, wrap_url: str = ''):
    '''path的前后都不加左斜杠
    返回headers(非wrap_url)，返回headers_str(wrap_url)'''
    headers = default_headers.copy()
    # 将cookie中的时间戳更新
    for k, _ in headers['Cookie'].items():
        if k == 'client_time':
            headers['Cookie'][k] = str(time_long)
        elif k =='serial':
            headers['Cookie'][k] = f"{headers['Cookie'][k][10:]}{str(time_long & 67108863)}"
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
    
    def bcz_system_check_infos(user_cookie=user_cookie):
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


    def bcz_system_get_switches(user_cookie=user_cookie):
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


    def bcz_system_get_static_config(user_cookie=user_cookie):
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


    def bcz_system_get_domain_whitelist(user_cookie=user_cookie):
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


    def bcz_system_get_privacy_agreement_version(user_cookie=user_cookie):
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


    def bcz_system_get_app_beta_update_info(user_cookie=user_cookie):
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

    def advertise_get_startup_ad(user_cookie=user_cookie, screen_length=1920, screen_width=1080):
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


    def advertise_get_mall_tab_icon_info(user_cookie=user_cookie):
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


    def advertise_get_practice_popup_adv(user_cookie=user_cookie):
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


    def advertise_get_explore_popup_adv(user_cookie=user_cookie):
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


    def advertise_get_loading_ad_items(user_cookie=user_cookie):
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


    def advertise_get_loading_ad_info(user_cookie=user_cookie):
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


    def advertise_get_live_streaming_info(user_cookie=user_cookie):
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


    def advertise_get_main_view_bottom_advs_v2(user_cookie=user_cookie):
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


    def advertise_get_main_view_top_banner_advs(user_cookie=user_cookie):
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


    def advertise_get_practice_popup_adv(user_cookie=user_cookie):
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
    

    def advertise_get_practice_banner_adv(user_cookie=user_cookie):
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
    def user_study_user_basic_info_v2(user_cookie=user_cookie):
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


    def user_study_get_user_study_config(user_cookie=user_cookie):
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


    def user_study_get_user_study_mode(user_cookie=user_cookie):
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




    def user_study_user_limit_info_v2(user_cookie=user_cookie):
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


    def user_study_win_streak_status(user_cookie=user_cookie, date=int(datetime.datetime.now().strftime('%Y%m%d'))):
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


    def user_study_get_books_replace_info(user_cookie=user_cookie):
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


    def user_study_get_main_page_js(user_cookie=user_cookie):
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

    def user_study_user_daka_v2(user_cookie=user_cookie, daka_dates=[]):
        '''user_daka_v2
        params: daka_dates: list of (year, month, day, timestamp), the whole month(1 to today), ascending'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        user_daka_dates = []
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


    def user_study_get_train_page_resource(user_cookie=user_cookie):
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

class unified_user:
    def unified_user_get_bind_info(user_cookie=user_cookie):
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


    def unified_user_check_access_token(user_cookie=user_cookie):
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
    def assistant_check_feedback_msg(user_cookie=user_cookie):
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

    def assistant_get_activity_updated_time(user_cookie=user_cookie):
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


    def assistant_get_beta_user_types_v2(user_cookie=user_cookie):
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



def get_report_event_jsons(args: list) -> list[str]:
    jsons = []
    for arg in args:
        json_dict = report_json[arg['index']].copy()
        json_dict['log_time'] = str(int(time.time() * 1000))
        if 'extra_info' in arg:
            json_dict['extra_info'] = arg['extra_info']
        jsons.append(json.dumps(json_dict))
    return jsons

def report_event(user_cookie=user_cookie, jsons=[]):
    '''report_event
    args:jsons[{"index":int,"extra_info":str}]'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = bcz_report_service.Client(protocol)
    client.send_report_event(get_report_event_jsons(jsons))
    content = transport.getvalue()
    time_long = int(time.time() * 1000)
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

# 下面是notify接口
def notify_get_remind_info(user_cookie=user_cookie):
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

def notify_get_latest_notify(user_cookie=user_cookie):
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
def resource_get_book_resource_update_info(user_cookie=user_cookie, book_id=user_config['book_id']):
    '''get_book_resource_update_info'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = resource_api_service.Client(protocol)
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
    def user_study_cold_launch(cold_launch=True, daka_dates=[]):
        '''user_study_cold_launch'''
        if cold_launch:
            yield user_study.user_study_user_basic_info_v2()
            yield user_study.user_study_get_user_study_config()
            yield user_study.user_study_get_user_study_mode()
        yield user_study.user_study_user_limit_info_v2()
        yield user_study.user_study_win_streak_status()
        if cold_launch:
            yield user_study.user_study_get_books_replace_info()
            yield user_study.user_study_get_main_page_js()
            yield user_study.user_study_user_daka_v2(daka_dates=daka_dates)
            yield user_study.user_study_get_train_page_resource()


    def bcz_system_cold_launch(cold_launch=True):
        '''bcz_system_cold_launch'''
        yield bcz_system.bcz_system_check_infos()
        if cold_launch:
            yield bcz_system.bcz_system_get_switches()
            yield bcz_system.bcz_system_get_static_config()
            yield bcz_system.bcz_system_get_domain_whitelist()
            yield bcz_system.bcz_system_get_privacy_agreement_version()
            yield bcz_system.bcz_system_get_app_beta_update_info()



    def advertise_cold_launch(cold_launch=True):
        '''advertise_cold_launch'''
        yield advertise.advertise_get_startup_ad()
        if cold_launch:
            yield advertise.advertise_get_mall_tab_icon_info()
        yield advertise.advertise_get_practice_popup_adv()
        yield advertise.advertise_get_explore_popup_adv()
        yield advertise.advertise_get_loading_ad_items()
        yield advertise.advertise_get_loading_ad_info()
        yield advertise.advertise_get_live_streaming_info()
        yield advertise.advertise_get_main_view_bottom_advs_v2()
        yield advertise.advertise_get_main_view_top_banner_advs()
        if cold_launch:
            yield advertise.advertise_get_practice_banner_adv()
        


    def assistant_cold_launch(cold_launch=True):
        '''assistant_cold_launch'''
        yield assistant.assistant_check_feedback_msg()
        yield assistant.assistant_get_activity_updated_time()
        yield assistant.assistant_get_beta_user_types_v2()

    def report_event_cold_launch(cold_launch=True):
        '''report_event_cold_launch'''
        cold_launch_report_event = [
            {"index": 0},
            {"index": 2},
            {"index": 4, "extra_info": "{" + f"adv_id\":\"{user_config['adv_id']}\",\"id\":\"{user_config['adv_id']}\"" + "}"},
            {"index": 5},
            {"index": 6, "extra_info": "{" + f"\"device_id\":\"{get_device_str(user_cookie['device_id'])}\",\"channel\":\"{user_config['app_channel']}\"" + "}"},
        ]
        yield report_event(jsons = cold_launch_report_event)


    def notify_cold_launch(cold_launch=True):
        '''notify_cold_launch'''

        yield notify_get_remind_info()
        yield notify_get_latest_notify()

    def resource_cold_launch(cold_launch=True):
        '''resource_cold_launch'''
        if cold_launch:
            yield resource_get_book_resource_update_info()

    def unified_user_cold_launch(cold_launch=True):
        '''unified_user_cold_launch'''
        if cold_launch:
            yield unified_user.unified_user_get_bind_info()
        yield unified_user.unified_user_check_access_token()


    def example():

            logger = thrift_logger()
            print('\033[1;37m--[$bcz_system]\033[0m')
            logger.run(cold_launch.bcz_system_cold_launch())
            
            print('\033[1;37m--[$advertise]\033[0m')
            logger.run(cold_launch.advertise_cold_launch())

            print('\033[1;37m--[$passport/unified_user_service]\033[0m')
            logger.run(cold_launch.unified_user_cold_launch())

            print('\033[1;37m--[$assistant]\033[0m')
            logger.run(cold_launch.assistant_cold_launch())

            print('\033[1;37m--[$notify]\033[0m')
            notify_generator = cold_launch.notify_cold_launch()
            logger.run(notify_generator)

            print('\033[1;37m--[$resource]\033[0m')
            resource_generator = cold_launch.resource_cold_launch()
            logger.run(resource_generator)
            
            
            print('\033[1;37m--[$learn/user_study]\033[0m')
            def get_this_month_timestamp(year, month, day):
                # 获取当月第一天的日期
                timestamp = int(datetime.datetime(year, month, 1).timestamp()) + 1
                result = []
                for i in range(day):
                    result.append([year, month, i+1, timestamp + i*86400])
                return result
            
            today_date = datetime.datetime.now().date()
            year = today_date.year
            month = today_date.month
            day = today_date.day
            daka_dates = get_this_month_timestamp(year, month, day)
            user_study_generator = cold_launch.user_study_cold_launch(cold_launch=True, daka_dates=daka_dates)
            logger.run(user_study_generator)
            print('\033[1;37m--[$report]\033[0m')
            logger.run(cold_launch.report_event_cold_launch())

            logger.close()


if __name__ == '__main__':
    cold_launch.example()

