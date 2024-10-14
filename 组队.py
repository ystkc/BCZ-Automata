# 组队.py
import json
import time
import sys
import requests
from src.thrift_utils import getHeaders, send_http2_request

cookie = []
with open('user_cookie.json', 'r', encoding='utf-8') as f:
    cookie = json.load(f)

if '--debug' in sys.argv:
    cookie = [cookie[-1]]

print('警告！请提前关闭magic_proxy')


current_code = []

def team_up_recite(publish_team=False):
    global current_code
    activity_id = str(input('请输入活动ID：(team-up-recite/home的请求JSON里面有，一般是1xx)'))
    for user in cookie:
        config = user['config']
        user_cookie = user['cookie']
        name = config['name']
        unique_id = config['unique_id']
        access_token = user_cookie['access_token']
        if name == '奶芋' or user_cookie.get('no_team', False):
            continue
        print(f'正在为{name}.{unique_id}组队...')

        # https://activity.baicizhan.com/api/activity/team-up-recite/home
        time_long = int(time.time() * 1000)
        headers = getHeaders('$activity', user_cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        url = 'https://activity.baicizhan.com/api/activity/team-up-recite/home'
        content = {
            'activityId': activity_id
        }
        response = requests.post(url, headers=headers, data=json.dumps(content))
        time.sleep(1)
        data = response.json()['data']
        count = data['count']
        code = data['code']
        nums = data['nums']
        is_published = data['isPublished']  
        print(f'当前队伍人数：{count}/{nums}')
        if count == 0:
            create_new = True
            valid_current_code = []
            for code in current_code:
                valid_current_code.push(code)
                print(f'未组队，尝试加入邀请码{code}')
                # https://activity.baicizhan.com/api/activity/team-up-recite/apply
                url = 'https://activity.baicizhan.com/api/activity/team-up-recite/apply'
                content = {
                    'activityId': activity_id,
                    'code': code,
                    'status': 0
                }
                time_long = int(time.time() * 1000)
                headers = getHeaders('$activity', user_cookie, time_long, index = 1)
                headers['Content-Type'] = 'application/json; charset=UTF-8'
                response = requests.post(url, headers=headers, data=json.dumps(content))
                print(response.json()['data']['type']) #  0成功 1过期 2无效 3已在队伍中  5已满
                if response.json()['data']['type'] == 0:
                    print('邀请码加入成功')
                    create_new = False
                    break
                if response.json()['data']['type'] == 3:
                    print('已在队伍中')
                    create_new = False
                    break
                if response.json()['data']['type'] == 5 or response.json()['data']['type'] == 2 or response.json()['data']['type'] == 1:
                    print('队伍已满/无效/过期')
                    valid_current_code.pop()
                time.sleep(1)
            current_code = valid_current_code
            if create_new:
                print('未组队，尝试创建队伍')
                # https://activity.baicizhan.com/api/activity/team-up-recite/get_random_name
                url = 'https://activity.baicizhan.com/api/activity/team-up-recite/get_random_name'
                content = {
                    'activityId': activity_id,
                    "count": 1
                }
                time_long = int(time.time() * 1000)
                headers = getHeaders('$activity', user_cookie, time_long, index = 1)
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
                headers = getHeaders('$activity', user_cookie, time_long, index = 1)
                headers['Content-Type'] = 'application/json; charset=UTF-8'
                content_str = json.dumps(content, ensure_ascii=False)
                print(content_str)
                response = send_http2_request('POST', url, headers, content_str)
                print(response.json()['data']['type']) # 0成功 1失败 2失败 3已在队伍中 4队名非法
                if response.json()['data']['type'] == 0:
                    current_code = response.json()['data']['code']
                    print(f'新队伍 邀请码：{current_code}')
                elif response.json()['data']['type'] == 3:
                    print('已在队伍中')
                else:
                    print('其他原因失败')
            # 获取用户头像框
            time_long = int(time.time() * 1000)
            headers = getHeaders('$activity', user_cookie, time_long, index = 1)
            headers['Content-Type'] = 'application/json; charset=UTF-8'
            url = 'https://activity.baicizhan.com/api/activity/team-up-recite/home'
            content = {
                'activityId': activity_id
            }
            response = requests.post(url, headers=headers, data=json.dumps(content))
            data = response.json()['data']
            my_tag = data['me']['tag']
            print(f'我的tag：{my_tag}(3靠谱，0不靠谱，1萌新)')

            time.sleep(1)
        elif count < nums:
            print('未满，记录邀请码')
            current_code.append(code)
        else:
            print('队伍已满，组队成功')

        
        print(f'公开状态：{is_published} 邀请码：{code}')
        if is_published == False and publish_team:
            # 公开
            # https://activity.baicizhan.com/api/activity/team-up-recite/publish_team

            url = 'https://activity.baicizhan.com/api/activity/team-up-recite/publish_team'
            content = {
                'activityId': activity_id
            }

            time_long = int(time.time() * 1000)
            headers = getHeaders('$activity', user_cookie, time_long, index = 1)
            headers['Content-Type'] = 'application/json; charset=UTF-8'
            response = requests.post(url, headers=headers, data=json.dumps(content))
            print(f'公开{response.json()["message"]}')
            
        
        print(f'{name}.{unique_id}组队完成')
        time.sleep(2)

if __name__ == '__main__':
    team_up_recite()
    if input(f'剩余{len(current_code)}个队伍可能未满，是否要公开剩余有效队伍？(y/n)') == 'y':
        team_up_recite(publish_team=True)
    

        
    


