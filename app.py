import sys
import time
import sqlite3
import logging

debug = True
if '--debug' in sys.argv:
    level = logging.DEBUG
    debug = True
else:
    level = logging.INFO
    debug = False

if debug:
    from werkzeug.serving import WSGIRequestHandler, _log
    WSGIRequestHandler.address_string = lambda self: self.headers.get('x-real-ip', self.client_address[0])
    class MyRequestHandler(WSGIRequestHandler):
        def log(self, type, message, *args):
            _log(type, f'{self.address_string()} {message % args}\n')
else:
    # import waitress # waitress 不支持websocket

    from gevent import monkey
    monkey.patch_all() # 如果出现gevent导致SSL无限递归，将这两行移到requests前面。
    # 这两行可以让gevent高并发执行，否则跟开发服务器一样
    from gevent.pywsgi import WSGIServer
    
import requests
import json
import os
import httpx
import hashlib
import certifi
import random
import datetime
import traceback
import threading

from flask import Flask, Response, render_template, jsonify, request
from flask_socketio import SocketIO, emit


from src import bcz
from src.config import Config
import src.thrift_utils as thrift_utils
from src.thrift_utils import user_dict, daka_list_class
from src.thrift_utils import getHeaders, send_http2_request, get_http2_client
from src.notice_parser import update_notice, member_storage_class
from src.schedule import Schedule


daka_list_obj = daka_list_class()


logging.basicConfig(
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    level=level
)


app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False
socketio = SocketIO(app, async_mode='gevent', logger=True)



config = Config()
user_dict_obj = user_dict()



def daka_sse(unique_id):
    global daka_cnt
    daka_cnt += 1
    index, user_dict = user_dict_obj.find(unique_id)
    user_dict['config']['user_index'] = index
    user_dict_list = user_dict_obj.user_dict_list
    user_cnt = len(user_dict_list)
    # yield f' {unique_id} 开始打卡{daka_cnt}<br>\n\n'
    # time.sleep(1)
    # yield f' {unique_id} 开始打卡{daka_cnt}<br>.\n\n'
    # time.sleep(1)
    # yield f' {unique_id} 开始打卡{daka_cnt}<br>..\n\n'
    # time.sleep(1)
    # yield f' {unique_id} 开始打卡{daka_cnt}<br>...\n\n'
    # time.sleep(1)
    # yield f' {unique_id} 开始打卡{daka_cnt}<br>....\n\n'
    for msg in thrift_utils.daka(daka_list_obj, user_cookie = user_dict['cookie'], user_config = user_dict['config'], total_user_cnt=user_cnt):
        yield f'{msg}\n\n'
    daka_cnt -= 1
            
@socketio.on('daka')
def daka(data):
    '''打卡'''
    try:
        # request_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        unique_id = data
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        for msg in daka_sse(unique_id):
            emit('msg', msg)
    except Exception as e:
        err_str = traceback.format_exc()
        # with open(f'error_{unique_id}_{int(time.time())}.txt', 'w', encoding='utf-8') as f:
        #     f.write(str(e))
        #     f.write(err_str)
        emit('error', f'$打卡失败{e}{err_str}')
        print(err_str)

@app.route('/get_bad_words', methods=['GET'])
def get_bad_words():
    '''获取坏词'''
    return restful(daka_list_obj.get_bad_words())

@app.route('/preserved_daka', methods=['GET'])
def preserved_daka():
    '''预约打卡，懒人选项，不设参数'''
    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    user_dict_list = user_dict_obj.user_dict_list
    user_cnt = len(user_dict_list)
    if user_cnt == 0:
        print('没有可预约的打卡用户')
        return restful(400, '没有可预约的打卡用户')
    # 预约明天早上4:30打卡，大概5点打完
    Schedule("* 4-7 * * * daka_schedule", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_patch=False))
    # Schedule("* 6 * * * patch_schedule", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_patch=True))
    # 目前来说，应该是服务器app会被休眠，但是Schedule类可以一直运行，即便合上电脑也不会停止。
    return restful(200, '预约成功.请插电并主动锁定设备')



@app.route('/')
def index():
    return render_template('index.html')

proxy_token = ''
@app.route('/proxy_token', methods=['POST'])
def proxy_token():
    global proxy_token
    try:
        token = request.json.get('token', '')
        if not token:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        proxy_token = token
        return restful(200, '设置成功')
    except Exception as e:
        return restful(400, f'{e}')
    

@app.route('/proxy', methods=['CONNECT', 'GET', 'POST', 'OPTIONS'])
def proxy():
    try:
        print('p')
        print(request.url)
        if request.method == 'CONNECT':  # 处理https请求
            # 发送connection established
            return Response(status=200)
        elif request.method == 'OPTIONS':  # 直接发送options请求，不做处理
            return send_http2_request(request.method, request.url, headers=request.headers, data=request.data)
        elif request.method == 'GET':
            if proxy_token != '':
                print('a')
                cookie = request.headers['Cookie'].split('; ')
                cookie['access_token'] = proxy_token
                headers = request.headers.copy()
                headers['Cookie']= '; '.join(cookie),
                return send_http2_request(request.method, request.url, headers=headers, data=request.data)
            return send_http2_request(request.method, request.url, headers=request.headers, data=request.data)
        elif request.method == 'POST':
            if proxy_token != '':
                print('b')
                cookie = request.headers['Cookie'].split('; ')
                cookie['access_token'] = proxy_token
                headers = request.headers.copy()
                headers['Cookie']= '; '.join(cookie),
                return send_http2_request(request.method, request.url, headers=headers, data=request.data)
            return send_http2_request(request.method, request.url, headers=request.headers, data=request.data)
        else:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    except Exception as e:
        return restful(400, f'{e}')
        

status = 0
@app.route('/update_notice', methods=['GET'])
def parse_notice():
    global status
    if status == 1:
        return restful(200, '更新中')
    status = 1
    try:
        logger.info('开始更新...')
        member_storage = member_storage_class()
        member_storage.update_member_infos(logger)
        status = 0
        return restful(200, '更新成功')
        conn = sqlite3.connect('../BCZ-Notice-Examiner/bcz_notice.db')
        update_notice(conn) # 根据现有公告数据库自动更新
        conn.close()
        
        status = 0
        return restful(200, '更新成功')
    except Exception as e:
        status = 0
        return restful(400, f'{e}\n{traceback.format_exc()}')

@app.route('/accounts', methods=['GET'])
def accounts():
    return render_template('accounts.html')
@app.route('/api/reply_and_ack', methods=['POST'])
def reply_and_ack():
    '''回复公告+收到'''

    try:
        unique_id = request.json.get('unique_id', '')
        group_share_key = request.json.get('group_share_key', '')
        content = request.json.get('content', '')
        if not unique_id or not group_share_key or not content:
            print(unique_id, group_share_key, content)
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        _, user_dict = user_dict_obj.find(unique_id)
        client = httpx.Client(http2=True, verify=certifi.where())
        time_long = int(time.time() * 1000)
        payload = {
            'shareKey': group_share_key,
            'nickname': content,
        }
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = client.post(f'https://group.baicizhan.com/group/set_nickname', headers=headers, content = json.dumps(payload, ensure_ascii=False)).json()
        result_str = ''
        if response_json['code'] == 1:
            result_str = '回复成功<br>'
        else:
            result_str = f'回复失败{response_json["message"]}<br>'
        time_long = int(time.time() * 1000)
        response_json = client.get(f'https://group.baicizhan.com/group/information?shareKey={group_share_key}', headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)).json()
        if response_json['code'] == 1:
            group_info = response_json['data']['groupInfo']
            group_id = group_info['id']
            members = response_json['data']['members']
            for member in members:
                if member['uniqueId'] == unique_id:
                    result_str += f'现在名字{member["nickname"]}<br>'
                    break
            # 收到
            time_long = int(time.time() * 1000)
            headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
            headers['Content-Type'] = 'application/json; charset=UTF-8'
            response_json = client.post(f'https://group.baicizhan.com/group/receive_notice?groupId={group_id}', content='{}', headers=headers).json()
            if response_json['code'] == 1:
                result_str += '收到成功<br>'
            else:
                result_str += f'收到失败{response_json["message"]}<br>'
        else:
            result_str += f'获取群组信息失败{response_json["message"]}<br>'
        client.close()
        return restful(200, result_str)
    except Exception as e:
        raise e
        return restful(400, f'{e}')
    

@app.route('/api/quit_group', methods=['POST'])
def quit_group():
    '''退出群组'''
    try:
        unique_id = request.json.get('unique_id', '')
        group_share_key = request.json.get('group_share_key', '')

        if not unique_id or not group_share_key:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        _, user_dict = user_dict_obj.find(unique_id)
        
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = requests.post(f'https://group.baicizhan.com/group/quit?shareKey={group_share_key}', data='{}', headers=headers).json()
        if response_json['code'] == 1:
            return restful(200, '退出群组成功')
        else:
            return restful(400, f'退出群组失败{response_json["message"]}')
        
    except Exception as e:
        return restful(400, f'{e}')
        
@app.route('/api/join_group', methods=['POST'])
def join_group():
    '''加入群组'''
    try:
        unique_id = request.json.get('unique_id', '')
        group_share_key = request.json.get('share_key', '')
        group_invite_key = request.json.get('invite_code', '')
        if not unique_id or (not group_share_key and not group_invite_key):
            print(unique_id, group_share_key, group_invite_key)
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        _, user_dict = user_dict_obj.find(unique_id)
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        if group_share_key != '':
            payload = {
                'shareKey': group_share_key,
                'source': 3
            }
            response_json = requests.post(f'https://group.baicizhan.com/group/join', json=(payload), headers=headers).json()
            if response_json['code'] == 1:
                return restful(200, '加入群组成功')
            else:
                return restful(400, f'加入群组失败{response_json["message"]}')
        else:
            payload = {
                'inviteKey': group_invite_key,
                'source': 0
            }
            response_json = requests.post(f'https://group.baicizhan.com/group/join', json=(payload), headers=headers).json()
            if response_json['code'] == 1:
                return restful(200, '加入群组成功')
            else:
                return restful(400, f'加入群组失败{response_json["message"]}')
    except Exception as e:
        raise e
        return restful(400, f'{e}')

@app.route('/accounts/reload', methods=['GET'])
def accounts_reload():
    '''重新加载用户列表'''
    global user_dict_obj
    del user_dict_obj
    user_dict_obj = user_dict()
    return accounts_list()


@app.route('/accounts/list', methods=['GET'])
def accounts_list():
    '''获取用户列表'''
    try:
        result = []
        user_dict_list = user_dict_obj.user_dict_list
        if debug:
            # 只获取3个用户
            user_dict_list = user_dict_list[:3]
        for user in user_dict_list:
            user['cookie']['device_id'] = hashlib.md5(str(user['cookie']['access_token']).encode('utf-8')).hexdigest()[:16]
            result.append({
                'name': user['config']['name'],
                'unique_id': user['config']['unique_id'],
                'device_id': user['cookie']['device_id'],
                'access_token': user['cookie']['access_token']
            })
        return restful(200, '获取用户列表成功', result)
    except Exception as e:
        return restful(400, f'{e}')
    
notice_list = []
pace = 6
def change_notice_sse_func(unique_id, group_share_key, content, mentioned_ids, group_id):
    for event in change_notice_sse_func_(unique_id, group_share_key, content, mentioned_ids, group_id):
        target = event.replace('\n', '<br>')
        target = target.replace('\r', '<br>')
        target = target.replace('<br><br>', '<br>')
        # print(target)
        yield f"data: {target}\n\n"
def change_notice_sse_func_(unique_id, group_share_key, content, mentioned_ids, group_id):
    # print(content)
    # print(mentioned_ids)
    # yield f'{content}{mentioned_ids}'
    # return
    message_str = ""
    _, user_dict = user_dict_obj.find(unique_id)
    time_long = int(time.time() * 1000)
    headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    payload = {
        "shareKey": group_share_key,
        "notice": content
    }
    # https://group.baicizhan.com/group/set_notice
    response_json = requests.post(f'https://group.baicizhan.com/group/set_notice', json=(payload), headers=headers).json()
    if response_json['message'] == None:
        message_str = f'通知发送成功<br><br>'
        yield message_str
    elif response_json['message'] == '小班公告内容涉嫌违规，请修改':
        reversed = False
        if content[0] == '#':
            message_str = f'{response_json["message"]}<br>{content}'
            yield message_str
            return
        if content[0] == '<' or content[0] == '>':
            reversed = True
            response_json['message'] += '_reversed'
            content = content[1:]
        acceptable = False
        message_str = f'{response_json["message"]}<br>{content}'
        yield message_str
        content_accept_part = ''
        check_part = ''
        if not reversed:
            while not acceptable:
                # 将content最后的pace个字符加入到check_part
                content_accept_part = check_part + content_accept_part
                check_part = content[-pace:]
                content = content[:-pace]
                message_str = f'{response_json["message"]}<br>{content}<u>{check_part}</u><s>{content_accept_part}</s>'
                yield message_str
                # 发送content
                payload = {
                    "shareKey": group_share_key,
                    "notice": content
                }
                headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
                headers['Content-Type'] = 'application/json; charset=UTF-8'
                response_json = requests.post(f'https://group.baicizhan.com/group/set_notice', json=(payload), headers=headers).json()
                if response_json['message'] == None:
                    message_str = f'{response_json["message"]}<br>{content}<u>{check_part}</u><s>{content_accept_part}</s>'
                    yield message_str
                    acceptable = True
                    break
                # 随机延迟
                time.sleep(random.randint(750, 1500) / 1000)
        else:
            # 从前面往后找
            while not acceptable:
                # 将content最前的pace个字符加入到check_part

                content_accept_part += check_part
                check_part = content[:pace]
                content = content[pace:]
                message_str = f'{response_json["message"]}_reversed<br><s>{content_accept_part}</s><u>{check_part}</u>{content}'
                
                yield message_str
                # 发送content
                payload = {
                    "shareKey": group_share_key,
                    "notice": content
                }
                headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
                headers['Content-Type'] = 'application/json; charset=UTF-8'
                response_json = requests.post(f'https://group.baicizhan.com/group/set_notice', json=(payload), headers=headers).json()
                if response_json['message'] == None:
                    message_str = f'{response_json["message"]}<br><s>{content_accept_part}</s><u>{check_part}</u>{content}'
                    yield message_str
                    acceptable = True
                    break
                # 随机延迟
                time.sleep(random.randint(750, 1500) / 1000)
    else:
        message_str = f'通知发送失败{response_json["message"]}<br><br>'
    # 发送mention
    if len(mentioned_ids) > 0:
        # https://group.baicizhan.com/group/batch_send_notice_to_mentioned_users
        # 先去重
        mentioned_ids = list(set(mentioned_ids))
        payload = {
            "groupId": group_id,
            "uniqueIds": mentioned_ids,
        }
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = requests.post(f'https://group.baicizhan.com/group/batch_send_notice_to_mentioned_users', json=(payload), headers=headers).json()
        if response_json['code'] == 1:
            message_str += f'@发送成功x{len(mentioned_ids)}<br><br>' + content
        else:
            message_str += f'@发送失败x{len(mentioned_ids)}{response_json}<br><br>' + content
        yield message_str


@app.route('/api/change_notice_sse', methods=['GET'])
def change_notice_sse():
    '''获取通知'''
    try:
        unique_id = int(request.args.get('unique_id', ''))
        group_share_key = request.args.get('group_share_key', '')
        group_id = request.args.get('group_id', '')
        content = ''
        for notice in notice_list:
            if notice['unique_id'] == unique_id and notice['group_share_key'] == group_share_key:
                content = notice['content']
                mentioned_ids = notice['mentioned_ids']
                notice_list.remove(notice)
                break
        if content == '':
            return restful(400, '通知内容为空')
        return Response(change_notice_sse_func(unique_id, group_share_key, content, mentioned_ids, group_id), mimetype='text/event-stream')
    except Exception as e:
        return restful(400, f'{e}')
        
@app.route('/api/change_notice', methods=['POST'])
def change_notice():
    '''获取通知'''
    try:
        unique_id = int(request.json.get('unique_id', ''))
        group_share_key = request.json.get('group_share_key', '')
        content = request.json.get('content', '')
        mentioned_ids = request.json.get('mentioned_ids', '')
        if not unique_id or not group_share_key or not content:
            print(unique_id, group_share_key, content)
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        notice_list.append({'unique_id': unique_id, 'group_share_key': group_share_key, 'content': content, 'mentioned_ids': mentioned_ids})
        return restful(200, '通知已收到')
    except Exception as e:
        return restful(400, f'{e}')
    
@app.route("/own_groups", methods=['GET'])
def own_groups():
    # return restful(200, '获取用户群组成功', [{'name': '用户年级组10', 'share_key': '', 'rank': '10已打卡于2022-01-01 00:00:00', 'introduction': '加入上限10', 'notice': '授权上限10', 'group_nickname': ''}])
    try:
        unique_id = request.args.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        _, user_dict = user_dict_obj.find(unique_id)
        time_long = int(time.time() * 1000)
        headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = send_http2_request('GET', 'https://group.baicizhan.com/group/own_groups?uniqueId=0', headers=headers, content=None) # 我的小班
        response_json = response.json()

        

        groups = []
        for group in response_json['data']['list']:
            
            # 要将introduction和notice中的换行符替换成<br>
            if group['introduction'] is None:
                group['introduction'] = ''
            if group['notice'] is None:
                group['notice'] = ''
            # 检查如果introduction和notice中有连续2个以上换行符，则替换成一个换行符
            while group['introduction'].count('\n\n\n') > 0:
                group['introduction'] = group['introduction'].replace('\n\n\n', '\n')
            while group['notice'].count('\n\n\n') > 0:
                group['notice'] = group['notice'].replace('\n\n\n', '\n')
            introduction = group['introduction'].replace('\n', '<br>')
            notice = group['notice'].replace('\n', '<br>')
            groups.append({
                'name': f"{group['name']}<br>(加入{group['joinDays']}天)",
                'share_key': group['shareKey'],
                'group_id': group['id'],
                'rank': group['rank'],
                'introduction': introduction,
                'notice': notice,
                'leader': group['leader'],
                'group_nickname': '未获取'
            })

        #  https://group.baicizhan.com/group/study_words_together_home_page
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = send_http2_request('GET', 'https://group.baicizhan.com/group/study_words_together_home_page', headers=headers, content=None)
        response_json = response.json()
        today_daka = '1已打卡' if response_json['data']['todayDaka'] else '0未打卡'

        # 'https://group.baicizhan.com/group/get_group_user_info'
        response = send_http2_request('GET', 'https://group.baicizhan.com/group/get_group_user_info', headers=headers, content=None)
        data = response.json()['data']

        result = bcz.userBasicInfo(user_dict['cookie']['access_token'], get_http2_client())
        daka_timestamp = result.learn_info.last_sync_done_score_time
        user_dict['config']['book_id'] = result.user_info.current_word_level_id
        

        date = datetime.datetime.fromtimestamp(daka_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        user_dict['config']['grade'] = data['grade']
        groups.append({
            'name': f'用户年级组{data["grade"]}书本{user_dict["config"]["book_id"]}',
            'share_key': '',
            'rank': f'{today_daka}于{date}',
            'introduction': data["groupLimiteNumber"],
            'notice': f'授权上限{data["groupAuthorizationLimiteNumber"]}',
            'group_nickname': ''
        })

        return restful(200, '获取用户群组成功', groups)
    except Exception as e:
        raise e
    #     return restful(400, f'{e}')


daka_cnt = 0
@app.route('/api/mm', methods=['GET'])
def mm():
    import pyautogui
    # 不断以正方形移动鼠标
    while daka_cnt == 0:
        time.sleep(1)
    while daka_cnt > 0:
        pyautogui.moveTo(100, 100, duration=0.5)
        pyautogui.moveTo(300, 100, duration=0.5)
        pyautogui.moveTo(300, 300, duration=0.5)
        pyautogui.moveTo(100, 300, duration=0.5)
        time.sleep(3)
    
    




    
        
@app.route('/api/get_nickname', methods=['GET'])
def notice():
    '''（改公告时）获取班内改昵称的列表'''
    try:
        last_monday = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday() + 7)
        unique_id = request.args.get('unique_id', '')
        group_share_key = request.args.get('group_share_key', '')
        _, user_dict = user_dict_obj.find(unique_id)


        # 1.从https://group.baicizhan.com/group/get_week_rank?shareKey=xxx&week=1/2获取班内昵称，1本周
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        rank = requests.get(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=1', headers=headers)
        last_week_rank = requests.get(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=2', headers=headers)
        member_list = rank.json()['data']['list']
        last_week_member_list = last_week_rank.json()['data']['list']
        group_nickname = {}
        my_reply = ""
        for member in member_list:
            unique_id = member['uniqueId']
            nickname = member['nickname']
            duration_days = member['durationDays']
            week_daka_dates = member['weekDakaDates']
            # 从本周一遍历
            if unique_id == user_dict['config']['unique_id']:
                my_reply = nickname
            # two_week_daka_dates是14个0、1，表示两周内每天的打卡情况
            two_week_daka_dates = [0] * 14
            wd = datetime.datetime.now().weekday()
            # 如果duration_days不够两周，后面的标记-2
            if duration_days < 7 + wd:
                for i in range(7 + wd - duration_days):
                    two_week_daka_dates[i] = -2
            # 将本周未到达的日期设置为-1
            for i in range(wd):
                two_week_daka_dates[-1-i] = -1
            for date in week_daka_dates:
                # 计算距离上周一的天数
                delta = (datetime.datetime.strptime(date, '%Y-%m-%d') - last_monday).days + 1
                two_week_daka_dates[delta] = 1

            group_nickname[unique_id] = {
                "group_nickname": nickname,
                "two_week_daka_dates": two_week_daka_dates
            }

        # 2.再获取默认昵称https://group.baicizhan.com/group/information?shareKey=xxx
        main_cookie = user_dict['cookie'].copy()
        main_cookie['access_token'] = config.main_token
        headers = getHeaders('$group', main_cookie, time_long, index = 1)
        response = requests.get(f'https://group.baicizhan.com/group/information?shareKey={group_share_key}', headers=headers)
        response_json = response.json()
        group_member_list = response_json['data']['members']
        # 遍历，如果有人的default_nickname和昵称相同，则是没改过昵称。
        for member in group_member_list:
            unique_id = member['uniqueId']
            if unique_id in group_nickname:
                if group_nickname[unique_id]['group_nickname'] == member['nickname']:
                    del group_nickname[unique_id]
                else:
                    group_nickname[unique_id]['nickname'] = member['nickname']
                    group_nickname[unique_id]['completed_times'] = member['completedTimes']
                    group_nickname[unique_id]['duration_days'] = member['durationDays']


        # 3.补全上周打卡情况
        for member in last_week_member_list:
            unique_id = member['uniqueId']
            if unique_id in group_nickname:
                last_week_daka_dates = member['weekDakaDates']
                two_week_daka_dates = group_nickname[unique_id]['two_week_daka_dates']
                for date in last_week_daka_dates:
                    # 计算距离上周一的天数
                    delta = (datetime.datetime.strptime(date, '%Y-%m-%d') - last_monday).days + 1
                    two_week_daka_dates[delta] = 1

        return restful(200, '获取班内改昵称的列表成功', {'my_reply': my_reply, 'group_nickname': group_nickname})
    except Exception as e:
        traceback.print_exc()
        return restful(400, f'{e}')
    
@app.route('/change_token', methods=['POST'])
def change_token():
    '''修改魔法token'''
    try:
        access_token = request.json.get('access_token', '')
        unique_id = request.json.get('unique_id', '')
        if not access_token:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        response = requests.get(f'http://mitm.it')
        if 'traffic is not passing through mitmproxy' in response.text:
            return restful(400, '请先启动BCZ-Automata的mitmproxy脚本，并正确设置代理')
        response = requests.get(f'http://www.baicizhan.com/change_token/{access_token}/{unique_id}')
        return restful(200, response.text)
    except Exception as e:
        return restful(400, f'{e}')
    
@app.route('/api/more_groups', methods=['POST'])
def more_groups():
    '''开班位'''
    try:

        unique_id = request.json.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        _, user_dict = user_dict_obj.find(unique_id)
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = requests.post('https://group.baicizhan.com/group/add_group_limit_num', headers=headers, data='{}')
        response_json = response.json()
        if response_json['code'] == 1:
            return restful(200, '开班位成功')
        else:
            return restful(400, f'开班位失败{response_json["message"]}')
    except Exception as e:
        raise e
        return restful(400, f'{e}')

# from src.thrift_utils import send_http2_request
@app.route('/login', methods=['GET'])
def login():
    # response = send_http2_request('GET', 'https://www.baidu.com', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}, content=None)
    # return response.content.decode('utf-8')
    return render_template('login.html')

@app.route('/user', methods=['GET'])
def user():
    return render_template('user.html')

@app.route('/send_sms', methods=['POST'])
def send_sms():
    '''发送短信验证码'''
    phone = request.json.get('phone', '')
    if not phone:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        bcz.sendSmsVerifyCode(phone)
        return restful(200, '验证码已发送到您的手机，请查收')
    except Exception as e:
        return restful(400, f'{e}')

@app.route('/user_login', methods=['POST'])
def user_login():
    '''用户登陆'''
    phone = request.json.get('phone', '')
    code = request.json.get('code', '')
    '''
    UserLoginResult(
        access_token='',
        is_new_user=None,
        email='',
        public_key='',
        last_device='',
        unique_id=,
        phone='',
        force_bind_phone=None,
        role_new=1,
        role=RoleInfo(role_up=None, grade=6)
    )
    '''
    data = {
        'user_id': '',
        'token': '',
    }
    # return restful(200, '登陆成功', data)
    if not phone or not code:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        result = bcz.loginWithPhone(phone, code)
        data = {
            'user_id': result.unique_id,
            'token': result.access_token,
        }
        print(result)
        return restful(200, '登陆成功', data)
    except Exception as e:
        return restful(400, f'{e}')

def restful(code: int, msg: str = '', data: dict = {}) -> Response:
    '''以RESTful的方式进行返回响应'''
    retcode = 1
    if code == 200:
        retcode = 0
    return jsonify({'code': code,
            'retcode': retcode,
            'msg': msg,
            'data': data
    }), code
    
if __name__ == '__main__':
    
    for name in logging.Logger.manager.loggerDict.keys():
        logger = logging.getLogger(name)
        if 'httpx' in name: # 输出http2多路请求的日志，如需要requests的日志，则加入'urllib3' in name
            logger.setLevel(logging.DEBUG)

    logging.info('BCZ-Automata 启动中...')
    if debug:
        # app.run(debug=True, host='127.0.0.1', port=8850, request_handler=MyRequestHandler)
        socketio.run(app, debug=True, host='127.0.0.1', port=8850)
    else:
        if '--static' not in sys.argv:
            logger.info('若未充满电，请设置屏幕关闭和睡眠时间为3小时以上')
            Schedule("15-59 4-7 * * 0 daka_schedule", lambda: thrift_utils.daka_all_headless(daka_list_obj,-1))
            Schedule("35-59 5-7 * * 1-6 daka_schedule", lambda: thrift_utils.daka_all_headless(daka_list_obj,-1))

            Schedule("15-59 23 * * * rank_and_notice_bronze", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=1))
            Schedule("20-59 23 * * * rank_and_notice_silver", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=2))
            Schedule("25-59 23 * * * rank_and_notice_gold", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=3))
            Schedule("30-59 23 * * * rank_and_notice_platinum", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=4))
            Schedule("35-59 23 * * * rank_and_notice_diamond", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=5))
            Schedule("40-59 23 * * * rank_and_notice_stellar", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=6))
            Schedule("45-59 23 * * * rank_and_notice_champion", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=7))
            # 以后可能加一个legend(doge)
            Schedule("50-59 23 * * * rank_and_notice_official", lambda: thrift_utils.daka_all_headless(daka_list_obj, only_rank_and_notice=0))



        # waitress.serve(app, host=config.host, port=config.port, threads=6, expose_tracebacks = True)
        http_server = WSGIServer((config.host, config.port), socketio.run(app, host=config.host, port=config.port), log=logging)
        http_server.serve_forever()