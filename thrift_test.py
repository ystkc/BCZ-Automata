# test if the new thrift struct is working
# methods: "check_infos"
# return_struct: "check_infos"

# thrift.exe -gen py d:/dotoro/project/#python/BCZ-Automata/src/thrift_test.thrift

from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol
from src.thriftAPI.ttypes import get_startup_ad_args, get_startup_ad_result, StartupAdRequest
from src.thriftAPI import check_infos_service, get_switches_service, get_startup_ad_service
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

check_infos_task = {
    "host": "$system",
    "path": 'rpc/bcz_system/check_infos',
    "method": "POST",
    "Headers": {
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
        "Transfer-Encoding": "chunked",
        "Host": "system.baicizhan.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
}
check_infos_task = {
    "host": "$system",
    "path": 'rpc/bcz_system/check_infos',
    "method": "POST",
    "Headers": {
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
        "Transfer-Encoding": "chunked",
        "Host": "system.baicizhan.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
}
get_switches_task = {
    "host": "$system",
    "path": 'rpc/bcz_system/get_switches',
    "method": "POST",
    "Headers": {
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
        "Transfer-Encoding": "chunked",
        "Host": "system.baicizhan.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
}
get_startup_ad_task = {
  "path": "rpc/advertise/get_startup_ad",
  "host": "$advertise",
  "method": "POST",
  "Headers": {
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
    "Content-Type": "application/x-thrift",
    "Host": "advertise.baicizhan.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
  }
}

with open("user_cookie.json", 'r', encoding='utf-8') as f:
    user_cookie = json.load(f)

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
# http = urllib3.PoolManager(
#     cert_reqs='CERT_REQUIRED',
# )
def getHeaders(task: dict, user_cookie: dict, params: str = '', socket: bool = False):
    '''path的前后都不加左斜杠
    返回headers和url(非socket)，返回headers_str(socket)'''
    headers = task['Headers'].copy()
    # 将cookie中的时间戳更新
    for k, _ in headers['Cookie'].items():
        if k == 'client_time':
            headers['Cookie'][k] = str(round(time.time()))
        elif k =='serial':
            headers['Cookie'][k] = f"{headers['Cookie'][k][10:]}{str(round(time.time())%100000000)}"
        else:
            # 由于user_cookie并不是所有接口都需要的，所以需要判断一下
            headers['Cookie'][k] = user_cookie[k]
    # 将cookie转换为字符串
    headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in headers['Cookie'].items()])
    if task['host'][0] == '$':
        # 需要将目标中的https://或http://去掉
        parsed = host_dict[task['host'][1:]][0].split('://')
        
    else:
        parsed = task['host'].split('://')
    if len(parsed) == 1:
        protocol = 'http'
    else:
        protocol = parsed[0]
    headers['Host'] = parsed[-1]
    url = f"{protocol}://{headers['Host']}/{task['path']}"
    
    if params == '$time_stamp_long':
        params = f'/{round(time.time()*1000)}'
    if not socket:
        return headers, f'{url}{params}'
    
    # 生成用于socket的请求头
    # 将headers连接成字符串
    result = '\r\n'.join([f'{k}: {v}' for k, v in headers.items()])
    result = f"{task['method']} {url}{params} HTTP/1.1\r\n{result}\r\n\r\n" 
    return result
    

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



def generator(content):
    # 压缩数据
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    yield content

def send_request(method, url, headers, content = None):
    # print(f'\033[1;36m{method}\033[0m {url}')
    # print(f'\033[1;36mheaders:\033[0m {headers}')
    if check_infos_task['method'] == 'POST':
        response = requests.post(url, headers=headers, data=generator(content))
    elif check_infos_task['method'] == 'GET':
        response = requests.get(url, headers=headers)
    elif check_infos_task['method'] == 'OPTIONS':
        response = requests.options(url, headers=headers)
    else:
        raise Exception('method not support')
    if response.status_code != 200:
        raise Exception(f'http status code: {response.status_code}')
    return response

async_content = []
def send_async_request(method, url, headers, content = None) -> list | None:
    '''当url是#时，发送历史的请求
    当url是其他时，加入队列，等待发送
    content可以是generator，使用http2尽可能复用tunnel，但需要在5s内'''
    async def _task(content):  
        """模拟异步任务"""
        method = content[0]
        url = content[1]
        headers = content[2]
        content_ = content[3]
        async with httpx.AsyncClient(http2=True, verify=certifi.where()) as client:
            client.headers.update(headers)
            # await asyncio.sleep(random.randint(1500, 2000) / 1000)
            if method == 'POST':
                # 考虑content_可能是个generator的情况
                try:
                    while True:
                        response = await client.post(url, data=next(content_))
                        if response.status_code != 200:
                            print(f'\033[1;31mhttp status code: {response.status_code}\033[0m')
                except StopIteration:   
                    pass
                except TypeError:
                    response = await client.post(url, data=content_)


            elif method == 'GET':
                response = await client.get(url)
            elif method == 'OPTIONS':
                response = await client.options(url)
            else:
                raise Exception('method not support')
        if response.status_code != 200:
            print(f'\033[1;31mhttp status code: {response.status_code}\033[0m')
        return response
    async def run_tasks_and_collect_results(*tasks):  
        # 使用asyncio.gather来并发运行所有任务并等待它们完成  
        results = await asyncio.gather(*tasks)  
        return results  
    if url == '#':
        tasks = []
        for i in async_content:
            # 任务开始前给予0-period_s秒的延迟，模拟网络延迟等因素
            task = _task(i)
            tasks.append(task)  
        return asyncio.run(run_tasks_and_collect_results(*tasks))
    else:
        content = generator(content)
        async_content.append([method, url, headers, content])
    

# 下面是正式task接口

def check_infos_api():
    '''sync'''
    transport = TTransport.TMemoryBuffer()
    # 发送请求
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = check_infos_service.Client(protocol)
    client.send_check_infos()
    content = transport.getvalue()
    # print(f'content: {content}')
    transport.close()

    # 持续性socket用http2模拟即可，其余统一requests解决
    headers, url = getHeaders(check_infos_task, user_cookie, f'$time_stamp_long')
    response = send_request(check_infos_task['method'], url, headers, content)
    
    # response.content已经解压，但是跟request一样，前四个字节是长度，要去掉
    result = response.content[4:]
    # print(f'result: {result}')
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = check_infos_service.Client(protocol)
    result = client.recv_check_infos()
    transport.close()
    return result

def get_switches_and_startup_ad_api(device_id):
    '''async'''
    '''get_switches'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = get_switches_service.Client(protocol)
    client.send_get_switches()
    content = transport.getvalue()
    transport.close()

    headers, url = getHeaders(get_switches_task, user_cookie, f'$time_stamp_long')
    send_async_request(get_switches_task['method'], url, headers, content)

    '''get_startup_ad'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = get_startup_ad_service.Client(protocol)
    args = StartupAdRequest(720, 1280, device_id, 'unknown')
    request = get_startup_ad_args(args)
    client.send_get_startup_ad(request)
    content = transport.getvalue()
    transport.close()

    headers, url = getHeaders(get_startup_ad_task, user_cookie, f'$time_stamp_long')
    send_async_request(get_switches_task['method'], url, headers, content)

    '''response'''
    responses = send_async_request('#', '#', {})
    result = responses[0].content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = get_switches_service.Client(protocol)
    result_switches = client.recv_get_switches()
    transport.close()
    
    result = responses[1].content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = get_startup_ad_service.Client(protocol)
    result_startup_ad = client.recv_get_startup_ad()
    transport.close()

    return result_switches, result_startup_ad





if __name__ == '__main__':
    # print('\033[1;36m[check_infos]\033[0m')
    # bcz_check_infos_dns = check_infos_api()
    # print('\033[1;32mdata_dns:\033[0m', bcz_check_infos_dns.data_dns)
    # print('\033[1;32mresource_dns:\033[0m', bcz_check_infos_dns.res_dns)
    # print('\033[1;32mtls_dns:\033[0m', '\n'.join(f'\033[1;33m{key}\033[0m: {list_value}' for key, list_value in bcz_check_infos_dns.tls_dns.items()))
    # print('\033[1;32mother_dns:\033[0m', '\n'.join(f'\033[1;33m{key}\033[0m: {list_value}' for key, list_value in bcz_check_infos_dns.other_dns.items()))
    # host_dict = bcz_check_infos_dns.other_dns
    # host_dict['RES'] = bcz_check_infos_dns.res_dns
    # host_dict['DATA'] = bcz_check_infos_dns.data_dns

    print('\033[1;36m[get_switches]\033[0m')
    bcz_switches, bcz_startup_ad = get_switches_and_startup_ad_api(user_cookie['device_id'])
    print(f'allow_fast_login: {bcz_switches.allow_fast_login}\nallow_try_user: {bcz_switches.allow_try_user}')
    
# struct AdLink{
#     1: i32 jump_type,
#     2: string link,
#     3: string mini_program_id,
#     4: string mini_program_path
# }
# struct StartupAd{
#     1: i32 ad_id,
#     2: i32 ad_type,
#     3: AdLink backup_link,
#     4: i64 end_time,
#     5: string ext_ad_id,
#     6: i32 full,
#     7: string img,
#     8: AdLink link,
#     9: i32 show_seconds,
#     10: i32 show_times,
#     11: i64 start_time
# }
    
    print('\033[1;36m[get_startup_ad]\033[0m')
    def print_ad_link(link):    
        if link is None:
            return 'None'
        return f'jump_type: {link.jump_type}\nlink: {link.link}\nmini_program_id: {link.mini_program_id}\nmini_program_path: {link.mini_program_path}'
    for ad in bcz_startup_ad:
        print(f'''get_startup_ad: 
    ad_id: {ad.ad_id}
    ad_type: {ad.ad_type}
    backup_link: {print_ad_link(ad.backup_link)}
    end_time: {ad.end_time}
    ext_ad_id: {ad.ext_ad_id}
    full: {ad.full}
    img: {ad.img}
    link: {print_ad_link(ad.link)}
    show_seconds: {ad.show_seconds}
    show_times: {ad.show_times}
    start_time: {ad.start_time}''')





# fiddler_filter: regex:^https://system\.baicizhan\.com.+(0|1|2|3|4|5|6|7|8|9)$
    

