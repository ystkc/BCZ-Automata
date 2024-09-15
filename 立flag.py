
# 立flag.py
import json
import time
import requests
from src.thrift_utils import getHeaders, send_http2_request

with open('user_cookie.json', 'r', encoding='utf-8') as f:
    cookie = json.load(f)


for user in cookie:
    config = user['config']
    cookie = user['cookie']
    name = config['name']
    unique_id = config['unique_id']
    access_token = cookie['access_token']
    print(f'正在为{name}.{unique_id}立flag...')
    
    # https://activity.baicizhan.com/api/activity/bet/info?id=11
    time_long = int(time.time() * 1000)
    headers = getHeaders('$activity', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    url = 'https://activity.baicizhan.com/api/activity/bet/info?id=11'
    response = requests.get(url, headers=headers)
    time.sleep(2)
    data = response.json()['data']
    if data['home']['status'] == 1:
        print(f'{name}.{unique_id}已经立过flag，跳过')
        continue

    # https://activity.baicizhan.com/api/activity/bet/apply?type=2&id=11
    time_long = int(time.time() * 1000)
    headers = getHeaders('$activity', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    url = 'https://activity.baicizhan.com/api/activity/bet/apply?type=2&id=11'
    response = requests.post(url, headers=headers, data='{}')
    time.sleep(1)
    code = response.json()['code']
    if code == 1:
        print(f'{name}.{unique_id}立flag成功')
    else:
        print(f'{name}.{unique_id}立flag失败，原因：{response.json()["message"]}')
    time.sleep(1)
    