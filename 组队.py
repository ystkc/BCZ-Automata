# 组队.py
import json
import time
import requests
from src.thrift_utils import getHeaders, send_http2_request

with open('user_cookie.json', 'r', encoding='utf-8') as f:
    cookie = json.load(f)

activity_id = str(input('请输入活动ID：'))

for user in cookie:
    config = user['config']
    cookie = user['cookie']
    name = config['name']
    unique_id = config['unique_id']
    access_token = cookie['access_token']
    if name == '奶芋' or cookie.get('no_team', False):
        continue
    print(f'正在为{name}.{unique_id}组队...')

    # https://activity.baicizhan.com/api/activity/team-up-recite/home
    time_long = int(time.time() * 1000)
    headers = getHeaders('$activity', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    url = 'https://activity.baicizhan.com/api/activity/team-up-recite/home'
    content = {
        'activityId': activity_id
    }
    response = requests.post(url, headers=headers, data=json.dumps(content))
    time.sleep(1)
    data = response.json()['data']
    count = data['count']
    is_published = data['isPublished']  
    print(f'当前队伍人数：{count}')
    if count == 0:
        print('未组队，建队')
        # https://activity.baicizhan.com/api/activity/team-up-recite/get_random_name
        url = 'https://activity.baicizhan.com/api/activity/team-up-recite/get_random_name'
        content = {
            'activityId': activity_id,
            "count": 1
        }
        time_long = int(time.time() * 1000)
        headers = getHeaders('$activity', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = requests.post(url, headers=headers, data=json.dumps(content))
        random_name = response.json()['data'][0]
        print(random_name)
        time.sleep(1)
        # https://activity.baicizhan.com/api/activity/team-up-recite/apply

        url = 'https://activity.baicizhan.com/api/activity/team-up-recite/apply'
        content = {
            'activityId': activity_id,
            'teamName': random_name,
            'nums': 3,
            'status': 0
        }
        time_long = int(time.time() * 1000)
        headers = getHeaders('$activity', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        content_str = json.dumps(content, ensure_ascii=False)
        print(content_str)
        response = send_http2_request('POST', url, headers, content_str)
        print(response.json()['message'])
        time.sleep(1)
    
    print(f'公开状态：{is_published}')
    if count <= 1 and is_published == False:
        # 公开
        # https://activity.baicizhan.com/api/activity/team-up-recite/publish_team

        url = 'https://activity.baicizhan.com/api/activity/team-up-recite/publish_team'
        content = {
            'activityId': activity_id
        }

        time_long = int(time.time() * 1000)
        headers = getHeaders('$activity', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = requests.post(url, headers=headers, data=json.dumps(content))
        print(f'公开{response.json()["message"]}')
        
    
    print(f'{name}.{unique_id}组队完成')
    time.sleep(2)

        
    


