# team.py
'''【独立工具】为用户组队或立flag'''
import json
import time
import sys
import requests
import random
from src.daka_utils import getHeaders, http2_client
from src.thrift_utils import advertise, print_thrift_object

http2_client_obj = http2_client()
cookie = []
with open('user_cookie.json', 'r', encoding='utf-8') as f:
    cookie = json.load(f)

if '--debug' in sys.argv:
    cookie = [cookie[-1]]

print('警告！请提前关闭magic_proxy（如果你不知道这是什么，那就继续）')


current_code = []
current_token = {}

def team_up_recite(publish_team=False):
    global current_code
    global current_token
    # https://activity.baicizhan.com/api/activity/team-up-recite/together_home
    time_long = int(time.time() * 1000)
    headers = getHeaders('$activity', cookie[0]['cookie'], time_long, index = 1)
    response = http2_client_obj.send_http2_request('GET', 'https://activity.baicizhan.com/api/activity/team-up-recite/together_home', headers, None)
    data = response.json()['data']
    activity_id = data['actId']
    input(f"请确认活动ID：{activity_id}")
    # activity_id = str(input('请输入活动ID：(team-up-recite/home的请求JSON里面有，一般是1xx)'))
    random.shuffle(cookie)
    for user in cookie:
        config = user['config']
        user_cookie = user['cookie']
        name = config['name']
        unique_id = config['unique_id']
        access_token = user_cookie['access_token']
        if name == '奶芋' or user_cookie.get('no_team', False) or not config.get('can_daka', False):
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
            valid_current_token = {}
            for code in current_code:
                print(f'未组队，尝试加入邀请码{code}')
                # https://activity.baicizhan.com/api/activity/team-up-recite/apply
                url = 'https://activity.baicizhan.com/api/activity/team-up-recite/apply'
                content = {
                    'activityId': activity_id,
                    'code': code,
                    'status': 1
                }
                time_long = int(time.time() * 1000)
                headers = getHeaders('$activity', user_cookie, time_long, index = 1)
                headers['Content-Type'] = 'application/json; charset=UTF-8'
                response = requests.post(url, headers=headers, data=json.dumps(content))
                print(response.json()['data']['type']) #  0成功 1过期 2无效 3已在队伍中  5已满
                if code not in valid_current_code:
                    valid_current_code.append(code)
                    valid_current_token[code] = access_token
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
                    valid_current_code.remove(code)
                    del valid_current_token[code]
                time.sleep(1)
            current_code = valid_current_code
            current_token = valid_current_token
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
                response = http2_client_obj.send_http2_request('POST', url, headers, content_str)
                print(response.json()['data']['type']) # 0成功 1失败 2失败 3已在队伍中 4队名非法
                if response.json()['data']['type'] == 0:
                    new_code = response.json()['data']['code']
                    print(f'新队伍 邀请码：{new_code}')
                    current_code.append(new_code)
                    current_token[new_code] = access_token
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
            if code not in current_code:
                current_code.append(code)
                current_token[code] = access_token
        else:
            print('队伍已满，组队成功')
        
        print(f'公开状态：{is_published} 邀请码：{code}')
def publish_team():
    user_cookie_template = cookie[0]['cookie'].copy()
    global current_code
    global current_token
    activity_id = str(input('请输入活动ID：(team-up-recite/home的请求JSON里面有，一般是1xx)'))
    for code in current_code:
        token = current_token[code]
        user_cookie_template['access_token'] = token
        # 公开
        # https://activity.baicizhan.com/api/activity/team-up-recite/publish_team

        url = 'https://activity.baicizhan.com/api/activity/team-up-recite/publish_team'
        content = {
            'activityId': activity_id
        }

        time_long = int(time.time() * 1000)
        headers = getHeaders('$activity', user_cookie_template, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = requests.post(url, headers=headers, data=json.dumps(content))
        print(f'公开{response.json()["message"]}')
        time.sleep(1)
        
    

def flag_bet():
    print("功能分离到flag.py中")
    # activity_id = str(input('请输入活动ID：(bet的请求JSON里面有，例如12)'))
    # for user in cookie:
    #     config = user['config']
    #     user_cookie = user['cookie']
    #     name = config['name']
    #     unique_id = config['unique_id']
    #     access_token = user_cookie['access_token']
    #     print(f'正在为{name}.{unique_id}立flag...')
    #     # https://activity.baicizhan.com/api/activity/bet/info?id=12
    #     url = f'https://activity.baicizhan.com/api/activity/bet/info?id={activity_id}'
    #     time_long = int(time.time() * 1000)
    #     headers = getHeaders('$activity', user_cookie, time_long, index = 1)
    #     response = requests.get(url, headers=headers)
    #     data = response.json()['data']
    #     home = data['home']
    #     status = home['status']
    #     can_apply = home['canApply']
    #     if can_apply == False:
    #         print('立flag活动已结束')
    #         return
    #     if status == 1:
    #         print('已立flag，跳过')
    #         time.sleep(1)
    #         continue
    #     # https://activity.baicizhan.com/api/activity/bet/apply?type=2&id=12
    #     url = f'https://activity.baicizhan.com/api/activity/bet/apply?type=2&id={activity_id}'
    #     content = {
    #     }
    #     time_long = int(time.time() * 1000)
    #     headers = getHeaders('$activity', user_cookie, time_long, index = 1)
    #     headers['Content-Type'] = 'application/json; charset=UTF-8'
    #     response = requests.post(url, headers=headers, data=json.dumps(content))
    #     print(response.json())
    #     print(f'{name}.{unique_id}立flag完成')
    #     # 重新获取队伍信息
    #     url = f'https://activity.baicizhan.com/api/activity/bet/info?id={activity_id}'
    #     time_long = int(time.time() * 1000)
    #     headers = getHeaders('$activity', user_cookie, time_long, index = 1)
    #     response = requests.get(url, headers=headers)
    #     data = response.json()['data']
    #     home = data['home']
    #     status = home['status']
    #     accumulative_task = home['accumulativeTask']
    #     credit_cnt_list = [(task['day'], task['creditCnt']) for task in accumulative_task]
    #     credit_cnt_list.extend([(task['day'], task['creditCnt']) for task in home['dailyTask']])
    #     print(f"status:{status} list:{credit_cnt_list}")
    #     time.sleep(random.randint(2, 4))



if __name__ == '__main__':
    if input("组队 or 立flag？(1/2)") == '1':
        team_up_recite()
        if input(f'剩余{len(current_code)}个队伍可能未满，是否要公开剩余有效队伍？(y/n)') == 'y':
            publish_team()
    else:
        flag_bet()
    

        
    


