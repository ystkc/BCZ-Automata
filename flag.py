# flag.py
'''【独立工具】为所有写入的账号立flag'''
import traceback
import threading
import random
import json
import time
from src.thrift_utils import getHeaders, advertise, print_thrift_object
from src.http2_client import http2_client

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('user_cookie.json', 'r', encoding='utf-8') as f:
    cookies = json.load(f)


http2_client_obj = http2_client()
adv = advertise(http2_client_obj)
def flag(user_cookie, user_config, user_name, randsec, i):
    time.sleep(randsec)
    unique_id = user_config['unique_id']
    print(f'正在为[{i}]{user_name}.{unique_id}立flag...')
    
    try:
        # https://activity.baicizhan.com/api/activity/bet/info?id=11
        time_long = int(time.time() * 1000)
        headers = getHeaders('$activity', user_cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        url = f'https://activity.baicizhan.com/api/activity/bet/info?id={activity_id}'
        response = http2_client_obj.send_http2_request('GET', url, headers, {})
        time.sleep(0.8)
        data = response.json()['data']
        if data['home']['status'] == 1:
            print(f'{user_name}.{unique_id}已经立过flag，跳过')
            return

        # https://activity.baicizhan.com/api/activity/bet/apply?type=2&id=11
        time_long = int(time.time() * 1000)
        headers = getHeaders('$activity', user_cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        url = f'https://activity.baicizhan.com/api/activity/bet/apply?type=2&id={activity_id}'
        response = http2_client_obj.send_http2_request('POST', url, headers, {})
        time.sleep(0.9)
        code = response.json()['code']
        if code == 1:
            print(f'{user_name}.{unique_id}立flag成功')
        else:
            print(f'\033[31m{user_name}.{unique_id}立flag失败，原因：{response.json()["message"]}\033[0m')
    except:
        print(f'\033[31m{user_name}.{unique_id}立flag出现错误，原因如下：\n{traceback.format_exc()}\033[0m')

user0 = cookies[0]
top_banner_adv_infos = adv.advertise_get_main_view_top_banner_advs(user0['cookie'], user0['config'])
print_thrift_object(top_banner_adv_infos)
activity_id = None
if len(top_banner_adv_infos) == 0:
    activity_id = input('没有获取到广告数据，请手动输入id')
else:
    activity_id = top_banner_adv_infos[0].link.split('id=')[1].split('&')[0]
    if activity_id == '':
        activity_id = input('没有获取到广告数据，请手动输入id')
    else:
        print(f'获取到广告数据，id为{activity_id}')

if activity_id is None:
    input('无效id...')
    exit()
else:
    input('回车开始...')
for i, user in enumerate(cookies):
    try:
        config = user['config']
        user_cookie = user['cookie']
        user_name = config['name']
        unique_id = config['unique_id']
        access_token = user_cookie['access_token']
    except:
        print(f'\033[31m{user}配置无效，跳过\033[0m')
        continue
    if not config.get('can_team', False) or not config.get('can_daka', False):
        print(f'{user_name}.{unique_id}未开启组队功能或未开启打卡功能，跳过')
        continue
    threading.Thread(target=flag, args=(user_cookie, config, user_name, random.randint(0, len(cookies)*10)/50, i)).start()
    
input('按任意键退出...')