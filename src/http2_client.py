
import asyncio
import threading
import time

import certifi
import httpx
import importlib
import winreg


FULL_ASYNC = False
NO_RETRY_STATUS_CODE = (200, 404, 400, 204, 418)

# def send_request(method, url, headers, content = None):
#     '''此处没有gzip'''
#     if method == 'POST':
#         response = requests.post(url, headers=headers, data=content)
#     elif method == 'GET':
#         response = requests.get(url, headers=headers)
#     elif method == 'OPTIONS':
#         response = requests.options(url, headers=headers)
#     else:
#         raise Exception('method not support')
#     if response.status_code not in RETRY_STATUS_CODE:
#         raise Exception(f'http status code: {response.status_code}')
#     return response

class http2_client:
    def __init__(self):
        self.client = None
        self.async_client = None
        self.lock = threading.Lock()
        self._closing_state = False # 用于结束多个线程

    def set_closing_state(self, state):
        self._closing_state = state

    def check_closing_state(self):
        if self._closing_state: # 结束当前线程
            raise AssertionError('http2 client is closing')
        
    def set_proxy(self, enable=True, proxy_server="http://127.0.0.1:8080"):
        '''因为某人总是忘记取消代理，服务器环境一般不需要的'''
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
        
    def send_http2_request(self, method: str, url: str, headers: dict, content: dict, retry: bool=True) -> httpx.Response:
        '''同步http2请求（可多线程并发使用，但不适用于FastAPI）
        当FULL_ASYNC=True时，本函数将使用异步请求（兼容性考虑）'''
        self.check_closing_state()
        if FULL_ASYNC:
            return self.rua(self.asyncFetch(url, method, headers, content))
        method = method.upper()
        if method == 'POST':
            return self.__post(url, headers=headers, json=content, timeout=10, retry=retry)
        elif method == 'GET':
            return self.__get(url, headers=headers, timeout=10, retry=retry)
        elif method == 'OPTIONS':
            return self.__options(url, headers=headers, timeout=10, retry=retry)

    def __options(self, url, headers=None, timeout=10, retry: bool=True):
        '''同步options'''
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                response = client.options(url, headers=headers, timeout=timeout)
                if response.status_code not in NO_RETRY_STATUS_CODE and retry:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                if not retry:
                    return None
                print(f'http2 options error: {e} {url}')
                if client.is_closed:
                    client = self.get_http2_client()
                    continue
                time.sleep(1.2)
                failed_count += 1
                if failed_count > 7:
                    Warning('http2 error, failed_count > 7')
                    self.rua(self.reload_http2_client())
                    self.set_proxy(False)
                    time.sleep(60)
                    failed_count = 0
                continue

    def __post(self, url, headers=None, json=None, timeout=10, retry: bool=True):
        '''同步post'''
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                if headers.get('Content-Type', '').startswith('application/json'):
                    response = client.post(url, headers=headers, json=json, timeout=timeout)
                else:
                    response = client.post(url, headers=headers, data=json, timeout=timeout) # thrift
                if response.status_code not in NO_RETRY_STATUS_CODE and retry:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                if not retry:
                    return None
                print(f'http2 post error: {e} {url}')
                if client.is_closed:
                    client = self.get_http2_client()
                    continue
                time.sleep(1.2)
                failed_count += 1
                if failed_count > 7:
                    Warning('http2 error, failed_count > 7')
                    self.rua(self.reload_http2_client())
                    self.set_proxy(False)
                    time.sleep(60)
                    failed_count = 0
                continue

    def __get(self, url, headers=None, timeout=10, retry: bool=True):
        '''同步get'''
        if FULL_ASYNC:
            return self.rua(self.asyncFetch(url, 'GET', headers))
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                response = client.get(url, headers=headers, timeout=timeout)
                if response.status_code not in NO_RETRY_STATUS_CODE and retry:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                if not retry:
                    return None
                print(f'http2 get error: {e} {url}')
                if client.is_closed:
                    client = self.get_http2_client()
                    continue
                time.sleep(1.2)
                failed_count += 1
                if failed_count > 7:
                    Warning('http2 error, failed_count > 7')
                    self.rua(self.reload_http2_client())
                    self.set_proxy(False)
                    time.sleep(60)
                    failed_count = 0
                continue

    async def asyncFetch(self, url: str, method: str = 'GET', headers: dict = {}, payload = None) -> httpx.Response:
        '''异步网络请求，适合FastAPI。同步函数建议使用self.rua(self.asyncFetch(...))而不是asyncio.run'''
        method = method.upper()
        self.check_closing_state()
        if method == 'GET':
            return await self.__async_get(url, headers=headers)
        elif method == 'POST':
            return await self.__async_post(url, headers=headers, json=payload)
        elif method == 'OPTIONS':
            return await self.__async_options(url, headers=headers)
        
    async def __async_post(self, url, headers=None, json=None, timeout=10):
        '''异步post'''
        client = self.get_http2_client(async_client=True)
        failed_count = 0
        while True:
            try:
                if headers.get('Content-Type', '').startswith('application/json'):
                    response = await client.post(url, headers=headers, json=json, timeout=timeout)
                else:
                    response = await client.post(url, headers=headers, data=json, timeout=timeout) # thrift
                if response.status_code not in NO_RETRY_STATUS_CODE:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'async http2 post error: {e} {url}')
                # print(url, headers, json, timeout)
                if client.is_closed:
                    client = self.get_http2_client(async_client=True)
                    continue
                await asyncio.sleep(1.2)
                failed_count += 1
                if failed_count > 7:
                    Warning('async http2 error, failed_count > 7')
                    await self.reload_http2_client()
                    self.set_proxy(False)
                    await asyncio.sleep(60)
                    failed_count = 0
                continue
    
    async def __async_get(self, url, headers=None, timeout=10):
        '''异步get'''
        client = self.get_http2_client(async_client=True)
        failed_count = 0
        while True:
            try:
                response = await client.get(url, headers=headers, timeout=timeout)
                if response.status_code not in NO_RETRY_STATUS_CODE:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'async http2 get error: {e} {url}')
                # print(url, headers, timeout)
                if client.is_closed:
                    client = self.get_http2_client(async_client=True)
                    continue
                await asyncio.sleep(1.2)
                failed_count += 1
                if failed_count > 7:
                    Warning('async http2 error, failed_count > 7')
                    await self.reload_http2_client()
                    self.set_proxy(False)
                    await asyncio.sleep(60)
                    failed_count = 0
                continue
    
    async def __async_options(self, url, headers=None, timeout=10):
        '''异步options'''
        client = self.get_http2_client(async_client=True)
        failed_count = 0
        while True:
            try:
                response = await client.options(url, headers=headers, timeout=timeout)
                if response.status_code not in NO_RETRY_STATUS_CODE:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'async http2 options error: {e} {url}')
                if client.is_closed:
                    client = self.get_http2_client(async_client=True)
                    continue
                await asyncio.sleep(1.2)
                failed_count += 1
                if failed_count > 7:
                    Warning('async http2 error, failed_count > 7')
                    await self.reload_http2_client()
                    self.set_proxy(False)
                    await asyncio.sleep(60)
                    failed_count = 0
                continue

    def get_http2_client(self, async_client=False):
        '''获取client，避免重复创建'''
        with self.lock:
            if async_client:
                if self.async_client is None or self.async_client.is_closed:
                    self.async_client = httpx.AsyncClient(http2=True, verify=certifi.where())
                return self.async_client
            else:
                if self.client is None or self.client.is_closed:
                    self.client = httpx.Client(http2=True, verify=certifi.where())
                return self.client

    async def reload_http2_client(self):
        '''重新加载http2_client(例如启动或关闭fiddler后更新代理)'''
        with self.lock:
            if not(self.client is None or self.client.is_closed):
                self.client.close()
            if not(self.async_client is None or self.async_client.is_closed):
                self.async_client.aclose()
            self.client = httpx.Client(http2=True, verify=certifi.where())
            self.async_client = httpx.AsyncClient(http2=True, verify=certifi.where())
            print('---http2 client reloaded---')

    def __del__(self):
        if not(self.client is None or self.client.is_closed):
            self.client.close()
        if not(self.async_client is None or self.async_client.is_closed):
            self.rua(self.async_client.aclose())

    def rua(self, async_corutine):
        '''在同步函数中调用异步函数，效果类似asyncio.run()
        极端高并发场景下，仍会出现set_event_loop后还没有调用run_until_complete就被修改loop的情况，报错bind to different loop。不会影响业务逻辑，但会影响性能。
        此时建议外层函数也改成异步然后使用asyncFetch，或使用同步模式send_http2_request'''
        # 多用asyncio.run()，即可点亮破大防三件套: Event loop was closed、bind to different loop、no available event loop
        with self.lock:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
            except Exception:
                loop = asyncio.new_event_loop()
            finally:
                asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_corutine)
        return result
