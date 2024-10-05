from mitmproxy import http
import hashlib
import traceback
import json
import winreg
import socket
import os

proxy_token = ''
proxy_device_id = ''
enable_fiddler_proxy = True
proxy_id = 0

def cookie_parser(cookie_str: str):
    cookie_dict = {}
    if cookie_str:
        # 将逗号替换成分号
        # cookie_str = cookie_str.replace(',', ';')
        for cookie in cookie_str.split(';'):
            try:
                key, value = cookie.strip().split('=')
                # print(key, value)
            except :
                print("Invalid cookie:", cookie)
            cookie_dict[key] = value
    return cookie_dict

def cookie_encoder(cookie_dict):
    cookie_str = ''
    for key, value in cookie_dict.items():
        cookie_str += key + '=' + value + '; '
    return cookie_str.strip()

def request(flow: http.HTTPFlow) -> None:
    global proxy_token
    global proxy_device_id
    global proxy_id
    
    if 'baicizhan.com/change_token' in flow.request.url:
        proxy_token = flow.request.url.split('/')[4] # www.baicizhan.com/change_token/xxx
        proxy_id = int(flow.request.url.split('/')[5])
        # 使用md5
        proxy_device_id = hashlib.md5(proxy_token.encode('utf-8')).hexdigest()[:16]
        print("\033[32mPROXY_TOKEN CHANGED, New proxy token:\033[0m", proxy_token)
        # 不发送请求，直接返回200
        flow.response = http.Response.make(200, f"BCZ_AUTOMATA: PROXY_TOKEN CHANGED {proxy_token} {proxy_device_id}", {"Content-Type": "text/plain"})
        return
    
    if proxy_token == '':
        print("\033[31mPROXY_TOKEN NOT SET, Please set proxy token first.\033[0m")
        return

    if 'baicizhan.com' in flow.request.url:
        
        # print('original cookie:', flow.request.headers.get('Cookie'))
        cookie = cookie_parser(flow.request.headers.get('Cookie'))
        register = False
        try:
            if 'register' in flow.request.url:
                register = True
                print("\033[32mREGISTER REQUEST\033[0m original content:", flow.request.content)
                # 加载请求中的json
                content = json.loads(flow.request.content.decode(encoding='utf-8'))
                content['deviceId'] = proxy_device_id
                content['bczId'] = proxy_id
                # 重新编码json
                flow.request.content = json.dumps(content).encode(encoding='utf-8')
                print(" modified content:", flow.request.content)
                
        except:
            traceback.print_exc()
            print('\033[31mInvalid REGISTER request json format.\033[0m')
            pass

        o = 0
        if 'access-token' in cookie:
            if cookie['access-token'] != proxy_token:
                cookie['access-token'] = proxy_token
                o = 1
        
        if 'access_token' in cookie:
            if cookie['access_token'] != proxy_token:
                cookie['access_token'] = proxy_token
                o = 1
        
        if 'device_id' in cookie:
            if cookie['device_id'] != proxy_device_id:
                cookie['device_id'] = proxy_device_id
                o = 1

        if 'serial' in cookie:
            # 将前5位替换成proxy_device_id前五位，第6-10位替换成proxy_device_id后五位，其余不变
            cookie['serial'] = proxy_device_id[:5] + proxy_device_id[-5:] + cookie['serial'][10:]
            # print(f" modified serial:\033[31m{proxy_device_id[:5] }\033[32m{proxy_device_id[-5:]}\033[31m{cookie['serial'][10:]}\033[0m")
            o = 1
        
        # if 'tfstk' in cookie:
        #     del cookie['tfstk']
        #     o = 1
            
        if o == 1:
            flow.request.headers['Cookie'] = cookie_encoder(cookie)
            # print(" modified cookie:", flow.request.headers.get('Cookie'))
        
        return
    

addons = [  
    (request, 'test_addon'),
]

def set_proxy(enable=True, proxy_server="http://127.0.0.1:8080"):
    if enable:
        print("Setting proxy to:", proxy_server)
    else:
        print("Disabling proxy...")
    internet_settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                       r'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings',
                                       0, winreg.KEY_ALL_ACCESS)
    if enable:
        winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(internet_settings, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
    else:
        winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 0)
    winreg.CloseKey(internet_settings)

def test_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', port))
        s.shutdown(2)
        return True
    except:
        return False
    
def main():# 注意：if __name__ == "__main__": 内不能用global关键字
    global enable_fiddler_proxy
    try:
        print('使用方式:运行magic_proxy.py,然后运行app.py点击魔法账号,然后启动客户端/模拟器,如果魔法未生效则手动设置代理本机ip:8080')
        print('若使用fiddler，请【先启动fiddler】，【再启动本程序】')
        # 检测8888端口是否被占用
        if test_port(8888):
            enable_fiddler_proxy = False
            print('端口8888被占用,将转发至该端口,请手动设置第一级代理为8080端口')
            os.system('mitmdump -s magic_proxy.py --set tls_version_client_min=UNBOUNDED ')
        else:    
            set_proxy(enable=True)
            os.system('mitmdump -s magic_proxy.py --set tls_version_client_min=UNBOUNDED ')
    except:
        pass
    finally:
        if enable_fiddler_proxy:
            set_proxy(enable=False)


if __name__ == "__main__":
    main()