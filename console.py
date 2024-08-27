import logging
import json
import time
import asyncio
import random
import hashlib
import gzip
import asyncio 
import base64 

import requests
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol

from src.thriftAPI.ttypes import UserSelectedBookInfo, select_book_args, update_done_data_args, login_with_phone_args, send_sms_verify_code_args
from src.thriftAPI.UserStudyApiService import UserDoneWordRecord, UserBookListInfo, UserBasicInfoPlusV2
from src.thriftAPI.UnifiedUserService import PhoneLoginRequest, PhoneVerifyCodeRequest, UserLoginResult

from src import bcz
from src.config import Config

class ProcessError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def base64_to_binary(base64_str):
    """
    将base64字符串转换为二进制数据，默认已经gzip压缩
    """
    

        
  
def test_task(access_token: list, period_s: int) -> list:
    async def _task(name, token, start_delay_s):  
        """模拟异步任务"""  
        print(f"Task {name} is ready")  
        await asyncio.sleep(start_delay_s)
        print(f"Task {name} is running...")  
        await asyncio.sleep(1)  
        return f"Result from {name}" 
    
    async def run_tasks_and_collect_results(*tasks):  
        # 使用asyncio.gather来并发运行所有任务并等待它们完成  
        results = await asyncio.gather(*tasks)  
        return results  
    
    tasks = []
    for i in range(len(access_token)):
        # 任务开始前给予0-period_s秒的延迟，模拟网络延迟等因素
        task = _task(f"{i+1}.{access_token[i]['name']}", access_token[i]["token"], random.randint(0, period_s * 1000) / 1000)
        tasks.append(task)  
    return asyncio.run(run_tasks_and_collect_results(*tasks))

serial_init_timestamp = 1701232600 # 原理暂不详
    
        
default_cookie = {
    "tfstk":""
    ,"access_token":""
    ,"Pay-Support-H5":"alipay_mob_client:weixin_app:qq_app"
    ,"device_name":"android/DCO-AL00-HUAWEI"
    ,"bcz_dmid":"2a16dfbb"
    ,"device_version":"12"
    ,"device_id":""
    ,"app_name":"7060100"
    ,"channel":"qq"
    ,"client_time":"1723800601"
}
daka_tasklist = [
    {
        "url":"https://learn.baicizhan.com/new-test-taking/"
        # 进入学习页面
        ,"method":"GET"
        ,"Headers":{
            "Host": "learn.baicizhan.com"
            ,"Connection": "keep-alive"
            ,"Upgrade-Insecure-Requests": "1"
            ,"User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI"
            ,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
            ,"cookie": {}
            ,"pay-support": "alipay_mob_client;weixin_app;qq_app;"
            ,"X-Requested-With": "com.jiongji.andriod.card"
            ,"Sec-Fetch-Site": "none"
            ,"Sec-Fetch-Mode": "navigate"
            ,"Sec-Fetch-User": "?1"
            ,"Sec-Fetch-Dest": "document"
            ,"Accept-Encoding": "gzip, deflate"
            ,"Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    },
    {
        # 相同Header的请求放一起处理
        "url":["https://learn.baicizhan.com/api/study/xMode/getSettings"
        # 暂无用处
               ,"https://learn.baicizhan.com/api/study/xMode/getCreditStatus"]
        # ?date=20240816，获取用户是否有拼写奖励
        ,"method":"GET"
        ,"Headers":{
            "Host": "learn.baicizhan.com"
            ,"Connection": "keep-alive"
            ,"User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI"
            ,"Accept": "*/*"
            ,"X-Requested-With": "com.jiongji.andriod.card"
            ,"Sec-Fetch-Site": "same-origin"
            ,"Sec-Fetch-Mode": "cors"
            ,"Sec-Fetch-Dest": "empty"
            ,"Referer": "https://learn.baicizhan.com/new-test-taking/"
            ,"Accept-Encoding": "gzip, deflate"
            ,"Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            ,"Cookie": {}
        }
    },
    {
        "url":"https://resource.baicizhan.com/api/resource/xMode"
        ,"method":"OPTIONS"
        # 预请求，获取资源服务器的跨域配置
        ,"Headers":{
            "Host": "resource.baicizhan.com"
            ,"Connection": "keep-alive"
            ,"Accept": "*/*"
            ,"Access-Control-Request-Method": "POST"
            ,"Access-Control-Request-Headers": "content-type"
            ,"Origin": "https://learn.baicizhan.com"
            ,"User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI"
            ,"Sec-Fetch-Mode": "cors"
            ,"X-Requested-With": "com.jiongji.andriod.card"
            ,"Sec-Fetch-Site": "same-site"
            ,"Sec-Fetch-Dest": "empty"
            ,'Referer': "https://learn.baicizhan.com/"
            ,"Accept-Encoding": "gzip, deflate"
            ,"Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    },
    {
        "url":"https://resource.baicizhan.com/api/resource/xMode"
        # 客户端提交需要学习的单词，包括书本id和单词topic_id
        ,"method":"POST"
        ,"Headers":{
            "Host": "resource.baicizhan.com"
            ,"Connection": "keep-alive"
            ,"Content-Length": 55
            ,"User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI"
            ,"Content-Type": "application/json"
            ,"Accept": "*/*"
            ,"Origin": "https://learn.baicizhan.com"
            ,"X-Requested-With": "com.jiongji.andriod.card"
            ,"Sec-Fetch-Site": "same-site"
            ,"Sec-Fetch-Mode": "cors"
            ,"Sec-Fetch-Dest": "empty"
            ,"Referer": "https://learn.baicizhan.com/"
            ,"Accept-Encoding": "gzip, deflate"
            ,"Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            ,"Cookie": {}
        }
    },
    {
        "url":"#word_resource"
        ,"method":"GET"
        ,"Headers":{
            "Host": "vol.bczcdn.com"
            ,"Connection": "Keep-Alive"
            ,"Accept-Encoding": "gzip"
            ,"User-Agent": "okhttp/4.9.3"
        }
    },
    {
        "url":"https://events.baicizhan.com/api/system/report_event"
        ,"method":"POST"
        ,"Headers":{
            "Host": "events.baicizhan.com"
            ,"Connection": "keep-alive"
            ,"Content-Length": 214
            ,"User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI"
            ,"Content-Type": "text/plain"
            ,"Accept": "*/*"
            ,"Origin": "https://learn.baicizhan.com"
            ,"X-Requested-With": "com.jiongji.andriod.card"
            ,"Sec-Fetch-Site": "same-site"
            ,"Sec-Fetch-Mode": "cors"
            ,"Sec-Fetch-Dest": "empty"
            ,"Referer": "https://learn.baicizhan.com/"
            ,"Accept-Encoding": "gzip, deflate"
            ,"Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            ,"Cookie": {}
        }
        ,"content":[
            {
                "log_time": 1723807165698
                ,"product_id": "bcz_app_h5"
                ,"stat_group": "study-detail-common"
                ,"event_id": "strategy_study_enter"
                ,"extra_info": "{\"topic_id\":5165,\"strategy_id\":\"q1\",\"plan_type\":\"XModelNewStudy\"}"
            }
        ]
    }

]
def daka_task(access_token: list, period_s: int, date: str, count: int) -> list:
    async def _task(name, token, start_delay_s, date, count): 
        """为用户打卡
        Args:
            token (str): 用户令牌
            date (str): 打卡日期
            count (int): 打卡单词数
        """    
        print(f"Task {name} is ready")  
        await asyncio.sleep(start_delay_s)
        print(f"{name} 打卡中...")  
        url = "https://learn.baicizhan.com/api/study/xMode/daka"
        timestamp = round(time.time()*1000)
        device_id = hashlib.md5(token.encode("utf-8")).hexdigest()[:16]
        serial = hashlib.md5(token.encode("utf-8")).hexdigest()[:24]
        headers = {
            "Accept": "*/*",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "bcz_app/android/7.6.5",
            "Host": "learn.baicizhan.com",
            "Cookie": (
                f"access_token={token}; app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
                f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
            ),
        }
        response = requests.post(url, headers=headers, data=f"date={date}&count={count}")
        if response.status_code != 200:
            raise ProcessError(f'{response.status_code} {response.content}')
        try:
            result = response.json()
            if result.get('code') != 1:
                raise ProcessError(result.get('message'))
            else:
                print(f"Task {name} is done")
        except:
            raise ProcessError(f'{response.status_code} {response.content}')
    
    async def run_tasks_and_collect_results(*tasks):  
        # 使用asyncio.gather来并发运行所有任务并等待它们完成  
        results = await asyncio.gather(*tasks)  
        return results  
    
    tasks = []
    for i in range(len(access_token)):
        # 任务开始前给予0-period_s秒的延迟，模拟网络延迟等因素
        task = _task(f"{i+1}.{access_token[i]['name']}", access_token[i]["token"], random.randint(0, period_s * 1000) / 1000)
        tasks.append(task)  
    return asyncio.run(run_tasks_and_collect_results(*tasks))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config = Config()
    with open('access_token.json', 'r', encoding='utf-8') as f:
        access_token = json.load(f) 
    
    print(test_task(access_token, 10))
    
    