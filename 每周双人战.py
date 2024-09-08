# 每周双人战.py
import json
import time
import requests
import random
import threading
from src.thrift_utils import getHeaders, send_http2_request

with open('user_cookie.json', 'r', encoding='utf-8') as f:
    cookie = json.load(f)

def run(user, random_delay_thresh = 20):
    
    data = {}

    config = user['config']
    cookie = user['cookie']
    name = config['name']
    unique_id = config['unique_id']
    access_token = cookie['access_token']
    random_delay = random.randint(0, random_delay_thresh)
    while random_delay > 0:
        print(f'{name} 等待{random_delay}秒')
        time.sleep(1)
        random_delay -= 1

    # https://social.baicizhan.com/api/deskmate/game/start_word_match_game
    time_long = int(time.time() * 1000)
    headers = getHeaders('$social', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json'
    response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/start_word_match_game', headers, '{}')
    print(f'{name} 开始每周双人战{response.json()}')
    if response.json()['code'] == 100:
        return
    
    
    
    while True:
        # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
        time_long = int(time.time() * 1000)
        headers = getHeaders('$social', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json'
        response = send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
        data = response.json()['data']
        if data.get('needCompletedTopicList', None) is not None:
            break
        time.sleep(1)

    if data['newUserGuide']['status'] == 0:
        print('播放新手指南4s')
        # https://social.baicizhan.com/api/deskmate/game/finish_new_user_guide
        time_long = int(time.time() * 1000)
        headers = getHeaders('$social', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json'
        time.sleep(4)
        response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/finish_new_user_guide', headers, '{}')


    while True:
        cnt = data['mine']['finishCount']
        if cnt >= 50:
            break
        topic_list = data['needCompletedTopicList']
        deskmate_completed_list = data['deskmate']['completedTopicList']
        my_completed_list = data['mine']['completedTopicList']
        finished_topic_ids = [t['topicId'] for t in deskmate_completed_list]
        finished_topic_ids.extend([t['topicId'] for t in my_completed_list])
        # 找第一个同桌未完成的题目
        found = 0
        
        for topic in topic_list:
            if topic['topicId'] not in finished_topic_ids:
                found = 1
                topic_id = topic['topicId']
                topic_option = topic['topicOption']
                break
        if found == 0:
            raise '没有找到未完成的题目'

        time.sleep(random.randint(3000, 4000) / 1000)

        # https://social.baicizhan.com/api/deskmate/game/word_match
        # {"topicId":45,"topicOption":"疼痛"}
        time_long = int(time.time() * 1000)
        headers = getHeaders('$social', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json'
        response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/word_match', headers, json.dumps({"topicId":topic_id,"topicOption":topic_option}, ensure_ascii=False))
        response_json = response.json()['data']
        # 刷新
        while True:
            # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            response = send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
            data = response.json()['data']
            if data['needCompletedTopicList'] is not None:
                break
            time.sleep(1)
        
        cnt = data['mine']['finishCount']
        print(f'{name} 完成第{cnt}次对战{response_json}')
        if response_json['credit'] > 0:
            print(f'铜板+{response_json["credit"]}')
            time.sleep(0.5)
        if cnt >= 50:
            break
    print(f'{name} 每周双人战结束')

    if data['status'] == 3:# 结束
        if data['wordMatchReward']['status'] == 0:
            # https://social.baicizhan.com/api/deskmate/game/send_word_match_reward
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            headers['Content-Type'] = 'application/json'
            response = send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/send_word_match_reward', headers, '{}')

            # 检验是否领取成功
            # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            response = send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
            data = response.json()['data']
            if data['wordMatchReward']['status'] == 1:
                print('00 每周双人战奖励领取成功')
            else:
                print('01 领取失败')
        else:
            print('02 奖励已领取')
    else:
        print('03 等待同桌完成')
            

tids = []
for user in cookie:
    tids.append(threading.Thread(target=run, args=(user,20)))
    tids[-1].start()

for tid in tids:
    tid.join()
    
