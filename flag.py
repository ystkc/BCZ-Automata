
# flag.py
'''【独立工具】为所有写入的账号立flag'''
import json
import time
import requests
from src.thrift_utils import getHeaders, advertise, print_thrift_object
from src.http2_client import http2_client

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('user_cookie.json', 'r', encoding='utf-8') as f:
    cookie = json.load(f)

user0 = cookie[0]
http2_client_obj = http2_client()
adv = advertise(http2_client_obj)
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
for user in cookie:
    config = user['config']
    cookie = user['cookie']
    name = config['name']
    unique_id = config['unique_id']
    access_token = cookie['access_token']
    if not config.get('can_team', False) or not config.get('can_daka', False):
        print(f'{name}.{unique_id}未开启组队功能或未开启打卡功能，跳过')
        continue
    print(f'正在为{name}.{unique_id}立flag...')
    
    # https://activity.baicizhan.com/api/activity/bet/info?id=11
    time_long = int(time.time() * 1000)
    headers = getHeaders('$activity', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    url = f'https://activity.baicizhan.com/api/activity/bet/info?id={activity_id}'
    response = requests.get(url, headers=headers)
    time.sleep(0.8)
    data = response.json()['data']
    if data['home']['status'] == 1:
        print(f'{name}.{unique_id}已经立过flag，跳过')
        continue

    # https://activity.baicizhan.com/api/activity/bet/apply?type=2&id=11
    time_long = int(time.time() * 1000)
    headers = getHeaders('$activity', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    url = f'https://activity.baicizhan.com/api/activity/bet/apply?type=2&id={activity_id}'
    response = requests.post(url, headers=headers, data='{}')
    time.sleep(0.9)
    code = response.json()['code']
    if code == 1:
        print(f'{name}.{unique_id}立flag成功')
    else:
        print(f'{name}.{unique_id}立flag失败，原因：{response.json()["message"]}')
    time.sleep(1)
input('按任意键退出...')