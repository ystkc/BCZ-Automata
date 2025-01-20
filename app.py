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

from flask import Flask, Response, render_template, jsonify, request
from flask_socketio import SocketIO, emit


from src import bcz
from src.config import Config
import src.daka_utils as daka_utils
from src.daka_utils import daka_list_class, notice_subscriber
from src.daka_utils import getHeaders, daka_headless
from src.thrift_utils import http2_client
from append import append_user_data


from src.notice_parser import member_storage_class

from src.schedule import Schedule

logging.basicConfig(
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    level=level
)
config = Config()

logger = logging.getLogger('BCZ-Automata')
logger.setLevel(level)

http2_client_obj = http2_client()
daka_list_obj = daka_list_class(logger, http2_client_obj, config)

app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False
socketio = SocketIO(app, async_mode='gevent', logger=True)

notice_subscriber_obj = notice_subscriber(logger, http2_client_obj, config)

@socketio.on('daka')
def daka(data):
    '''打卡'''
    try:
        unique_id = data
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = daka_list_obj.get_user_dict(unique_id)
        user_cnt = daka_list_obj.get_user_cnt()
        for msg in daka_headless(daka_list_obj, user_dict['cookie'], user_dict['config'], http2_client_obj, user_cnt, -1, 0, True):
            emit('msg', msg)
    except Exception as e:
        err_str = traceback.format_exc()
        emit('error', f'打卡api出现错误{e}\n{err_str}')
        daka_list_obj.add_warning(f'打卡api出现错误{e}\n{err_str}')

@app.route('/get_bad_words', methods=['GET'])
def get_bad_words():
    '''获取坏词'''
    return restful(200, daka_list_obj.get_bad_words())

@app.route('/clear_bad_words', methods=['GET'])
def clear_bad_words():
    '''清空坏词'''
    daka_list_obj.clear_bad_words()
    daka_list_obj.close()
    return restful(200, '清空成功')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reload', methods=['GET'])
def reload_http2():
    http2_client_obj.reload_http2_client()
    return restful(200, '成功')


@app.route('/save', methods=['GET'])
def save_config():
    daka_list_obj.close()
    return restful(200, '保存成功')

@app.route('/check_daka', methods=['GET'])
def check_daka():
    '''检查打卡'''
    return restful(200, daka_list_obj.check_not_daka_users(include_not_daka=request.args.get('include_not_daka', 'false') == 'true'))

# member_storage = member_storage_class(logger)
def parse_notice_online(only_raw_notice=True):
    logger.info('开始更新违禁词库...')
    conn = sqlite3.connect('../BCZ-Notice-Examiner/bcz_notice.db')
    daka_list_obj.notice_parser.update_notice(conn, only_raw_notice=only_raw_notice) # 根据现有公告数据库自动更新
    conn.close()

def parse_notice_offline():
    try:
        logger.info('开始更新成员库...')
        member_storage = member_storage_class(logger)
        return
        member_storage.update_member_infos(logger, NO_EXCEL=False)

        parse_notice_online(only_raw_notice=False)
    except Exception as e:
        traceback.print_exc()

status = 0
@app.route('/update_notice', methods=['GET'])
def parse_notice():
    global status
    if time.time() - status < 10:
        return restful(200, '已更新过')
    try:
        parse_notice_online(only_raw_notice=False)
        
        status = time.time()
        return restful(200, '更新成功')
    except Exception as e:
        status = time.time()
        return restful(400, f'{e}\n{traceback.format_exc()}')

@app.route('/accounts', methods=['GET'])
def accounts():
    return render_template('accounts.html')

@app.route('/api/reply_and_ack', methods=['POST'])
def reply_and_ack():
    unique_id = request.json.get('unique_id', '')
    group_share_key = request.json.get('group_share_key', '')
    content = request.json.get('content', '')
    if not unique_id or not group_share_key or not content:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    user_dict = daka_list_obj.get_user_dict(unique_id)
    try:
        result_str, _ = notice_subscriber_obj.reply_and_ack(unique_id, user_dict, group_share_key, content)
        return restful(200, result_str)
    except Exception as e:
        return restful(400, f'{e}')

@app.route('/api/quit_group', methods=['POST'])
def quit_group():
    '''退出群组'''
    try:
        unique_id = request.json.get('unique_id', '')
        group_share_key = request.json.get('group_share_key', '')

        if not unique_id or not group_share_key:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = daka_list_obj.get_user_dict(unique_id)
        
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
        user_dict = daka_list_obj.get_user_dict(unique_id)
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

@app.route('/append', methods=['GET'])
def append_accounts():
    '''添加或更新用户配置信息（用excel表格导入）'''
    return render_template('append.html')

@app.route('/append/submit', methods=['POST'])
def append_accounts_submit():
    try:
        text = request.json.get('content', '')
        if not text:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        return restful(200, append_user_data(text))
    except Exception as e:
        return restful(400, f'{e}{traceback.format_exc()}')

@app.route('/accounts/reload', methods=['GET'])
def accounts_reload():
    '''重新加载用户列表'''
    daka_list_obj.reload_user_dict()
    return accounts_list()


@app.route('/accounts/list', methods=['GET'])
def accounts_list():
    '''获取用户列表'''
    try:
        result = []
        user_dict_list = daka_list_obj.get_user_dict_list()
        if debug:
            # 只获取3个用户
            user_dict_list = user_dict_list[:3]
        for user in user_dict_list:
            user['cookie']['device_id'] = hashlib.md5(str(user['cookie']['access_token']).encode('utf-8')).hexdigest()[:16]
            result.append({
                'name': user['config']['name'],
                'unique_id': user['config']['unique_id'],
                'device_id': user['cookie']['device_id'],
                'access_token': user['cookie']['access_token'],
                'can_daka': user['config']['can_daka']
            })
        return restful(200, '获取用户列表成功', result)
    except Exception as e:
        return restful(400, f'{e}{traceback.format_exc()}')
    
notice_list = []
pace = config.check_notice_pace
def change_notice_sse_func(unique_id, group_share_key, content, mentioned_ids, group_id):
    for event in change_notice_sse_func_(unique_id, group_share_key, content, mentioned_ids, group_id):
        target = event.replace('\n', '<br>')
        target = target.replace('\r', '<br>')
        target = target.replace('<br><br>', '<br>')
        yield f"data: {target}\n\n"
def change_notice_sse_func_(unique_id, group_share_key, content, mentioned_ids, group_id):
    message_str = ""
    user_dict = daka_list_obj.get_user_dict(unique_id)
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
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        notice_list.append({'unique_id': unique_id, 'group_share_key': group_share_key, 'content': content, 'mentioned_ids': mentioned_ids})
        return restful(200, '通知已收到')
    except Exception as e:
        return restful(400, f'{e}')
    
@app.route('/subscribe', methods=['GET'])
def subscribe():
    '''生成html页面，供用户查看公告(一个)'''
    return render_template('subscribe.html')

@app.route('/subscribe/data', methods=['GET'])
def subscribe_data():
    top_notice = notice_subscriber_obj.get_top_notice(daka_list_obj)
    top_notice['introduction'] = top_notice['introduction'].replace('\n', '<br>')
    top_notice['notice'] = top_notice['notice'].replace('\n', '<br>')
    return jsonify(top_notice)

@app.route('/subscribe/reply', methods=['POST'])
def subscribe_reply():
    unique_id = request.args.get('unique_id', '')
    group_id = request.args.get('group_id', '')
    group_share_key = request.args.get('group_share_key', '')
    notice_hash = request.args.get('notice_hash', '')
    # 从content中获取reply_content
    reply_content = request.json.get('reply_content', '')
    correspond = request.json.get('correspond', True)
    if not unique_id or not group_id or not group_share_key or not notice_hash:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    user_dict = daka_list_obj.get_user_dict(unique_id)
    code, result_str = notice_subscriber_obj.read_reply_and_ack(unique_id, user_dict, group_share_key, group_id, notice_hash, reply_content, correspond)
    return restful(code, result_str)
    
@app.route("/own_groups", methods=['GET'])
def own_groups():
    # return restful(200, '获取用户群组成功', [{'name': '用户年级组10', 'share_key': '', 'rank': '10已打卡于2022-01-01 00:00:00', 'introduction': '加入上限10', 'notice': '授权上限10', 'group_nickname': ''}])
    try:
        unique_id = request.args.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = daka_list_obj.get_user_dict(unique_id)
        time_long = int(time.time() * 1000)
        headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/own_groups?uniqueId=0', headers=headers, content=None) # 我的小班
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
        response = http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/study_words_together_home_page', headers=headers, content=None)
        response_json = response.json()
        today_daka = '1已打卡' if response_json['data']['todayDaka'] else '0未打卡'

        # 'https://group.baicizhan.com/group/get_group_user_info'
        response = http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/get_group_user_info', headers=headers, content=None)
        data = response.json()['data']

        result = bcz.userBasicInfo(user_dict['cookie']['access_token'], http2_client_obj.get_http2_client())
        daka_timestamp = result.learn_info.last_sync_done_score_time
        user_dict['config']['book_id'] = result.user_info.current_word_level_id
        user_ip_desc = result.user_info.ip_desc
        # user_school_name = result.user_info.user_education_info.school_name
        

        date = datetime.datetime.fromtimestamp(daka_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        user_dict['config']['grade'] = data['grade']
        cooper = user_dict['config'].get('cooper', -1)
        daka_list_obj.update_user_dict(user_dict)
        groups.append({
            'name': f'用户年级{data["grade"]}书本{user_dict["config"]["book_id"]}/{user_ip_desc}',
            'share_key': '',
            'rank': f'{today_daka}于{date}<br>+<span class="cooper">{cooper}</span>',
            'introduction': data["groupLimiteNumber"],
            'notice': f'授权上限{data["groupAuthorizationLimiteNumber"]}',
            'group_nickname': ''
        })

        return restful(200, '获取用户群组成功', groups)
    except Exception as e:
        return restful(400, traceback.format_exc())


def get_nickname(main_token, http2_client_obj: http2_client, unique_id, group_share_key, user_dict):
    '''返回班内昵称和打卡情况
    my_reply: str
    group_nickname[unique_id]: {
    "group_nickname": "xxx",
    "nickname": "xxx",
    "two_week_daka_dates": [-2, -2, -2, -2, -2, -2, -2, 1, 1, 0, 0, 1, -1, -1],
    "completed_times": 3,
    "duration_days": 5,
    }'''
    last_monday = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday() + 7)
    # 1.从https://group.baicizhan.com/group/get_week_rank?shareKey=xxx&week=1/2获取班内昵称，1本周
    time_long = int(time.time() * 1000)
    headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
    # rank = requests.get(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=1', headers=headers)
    rank = http2_client_obj.send_http2_request('GET', f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=1', headers=headers, content=None)
    # last_week_rank = requests.get(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=2', headers=headers)
    last_week_rank = http2_client_obj.send_http2_request('GET', f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=2', headers=headers, content=None)
    member_list = rank.json()['data']['list']
    last_week_member_list = last_week_rank.json()['data']['list']
    group_nickname = {}
    my_reply = ""
    monitor_reply = ""
    wd = datetime.datetime.now().weekday()
    for member in member_list:
        unique_id = member['uniqueId']
        nickname = member['nickname']
        duration_days = member['durationDays']
        week_daka_dates = member['weekDakaDates']
        if member['leader'] == 1:
            monitor_reply = nickname
        if unique_id == user_dict['config']['unique_id']:
            my_reply = nickname
        # two_week_daka_dates是14个0、1，表示两周内每天的打卡情况
        two_week_daka_dates = [0] * 14
        # 如果duration_days不够两周，后面的标记-2
        if duration_days < 8 + wd:
            for i in range(8 + wd - duration_days):
                two_week_daka_dates[i] = -2
        # 将本周未到达的日期设置为-1
        for i in range(6-wd):
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
    main_cookie['access_token'] = main_token
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
    return my_reply, monitor_reply, group_nickname

@app.route('/subscribe/get_nickname', methods=['GET'])
@app.route('/api/get_nickname', methods=['GET'])
def get_nickname_():
    '''（改公告时）获取班内改昵称的列表'''
    try:
        unique_id = request.args.get('unique_id', '')
        group_share_key = request.args.get('group_share_key', '')
        user_dict = daka_list_obj.get_user_dict(unique_id)
        my_reply, monitor_reply, group_nickname = get_nickname(config.main_token, http2_client_obj, unique_id, group_share_key, user_dict)
        return restful(200, '获取班内改昵称的列表成功', {'my_reply': my_reply, 'monitor_reply': monitor_reply, 'group_nickname': group_nickname})
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
        user_dict = daka_list_obj.get_user_dict(unique_id)
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
    
def shutdown():
    if not config.local: # 仅本地模式（呃，懒？）
        return
    try:
        logger.info('BCZ-Automata 关闭中...')
        os.system('shutdown -s -t 120')
    except:
        pass


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

def prevent_sleep():
    '''防止系统进入休眠'''
    # 注意：对于笔记本电脑，还需要手动设置关上盖子不睡眠
    os.system(config.prevent_sleep_command)

def allow_sleep():
    '''允许系统进入休眠'''
    os.system(config.allow_sleep_command)

def shutdown_sallow_unotice_getuv(): # 在每天的59 23 * * 运行，根据星期执行不同的功能
    '''关闭系统/允许休眠/升级通知/获取总uv'''
    weekday = datetime.datetime.now().weekday()
    user_dict = daka_list_obj.get_user_dict(0) # 获取一个默认用户令牌
    # 星期一：parse_notice_offline()
    if weekday == 6: # 星期日晚上
        ...
        # parse_notice_offline()
    # 星期二-星期日：allow_sleep()、shutdown()、parse_notice_online()
    elif weekday >= 0 and weekday <= 5: # 星期一到星期六晚上
        allow_sleep()
        # parse_notice_online(only_raw_notice=True)
        shutdown()

def buka():
    not_daka_users = daka_list_obj.check_not_daka_users(include_not_daka=True)
    print(f"正在为{len(not_daka_users)}人补卡")
    if len(not_daka_users) > 0: # -1 正常打卡，-2 补卡
        daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=-2, user_dict_list=not_daka_users, random_delay=180)

def sync_and_subscribe():
    '''同步和订阅服务'''
    # 同步服务
    try:
        for comm in config.sync_command:
            os.system(comm)
        # path = os.path.dirname(os.path.abspath(__file__)).split('BCZ-Automata')[0]
        # spliter = path[-1]
        # path = f"explorer.exe /select,\"{path}BCZ-Notice-Examiner{spliter}bcz_notice.db\""
        # os.system(path)
    except Exception as e:
        logger.error(f"执行同步命令失败：{e}")
    # 订阅服务(仅本地模式，服务器模式请访问/subscribe/)
    if config.local:
        ...
        
    
if __name__ == '__main__':
    for name in logging.Logger.manager.loggerDict.keys():
        if 'httpx' in name: # 输出http2多路请求的日志，如需要requests的日志，则加入'urllib3' in name
            tlogger = logging.getLogger(name)
            tlogger.setLevel(logging.DEBUG)

    logger.info('BCZ-Automata 启动中...')
    if debug:
        # app.run(debug=True, host='127.0.0.1', port=8850, request_handler=MyRequestHandler)
        socketio.run(app, debug=True, host=config.host, port=config.port)
    else:
        if '--static' not in sys.argv:
            Schedule("58-59 23 * * 0-6 shutdown_sallow_unotice_getuv", lambda: shutdown_sallow_unotice_getuv())

            Schedule("* 4-8 * * 0 daka_schedule", lambda: daka_utils.daka_all_headless(daka_list_obj,http2_client_obj,-1, random_delay=3000))
            Schedule("* 5-8 * * 1-6 daka_schedule", lambda: daka_utils.daka_all_headless(daka_list_obj,http2_client_obj,-1, random_delay=2000))
            Schedule("* 6-8 * * 0-6 sync_and_subscribe", lambda: sync_and_subscribe())
            Schedule("* 4-8,21-23 * * 0-6 prevent_sleep", lambda: prevent_sleep())

            if '--test' in sys.argv:
                Schedule("* * * * * tester", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=6, random_delay=11))
            Schedule("31-59 23 * * * rank_and_notice_bronze", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=1, random_delay=121))
            Schedule("34-59 23 * * * rank_and_notice_silver", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=2, random_delay=121))
            Schedule("37-59 23 * * * rank_and_notice_gold", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=3, random_delay=121))
            Schedule("40-59 23 * * * rank_and_notice_platinum", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=4, random_delay=121))
            Schedule("43-59 23 * * * rank_and_notice_diamond", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=5, random_delay=121))
            Schedule("46-59 23 * * * rank_and_notice_stellar", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=6, random_delay=121))
            # Schedule("* 6-8 * * * champion_dawn", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=7, random_delay=181))
            Schedule("* 12-14 * * * champion_noon", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=7, random_delay=181))
            Schedule("49-59 23 * * * rank_and_notice_champion", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=7, random_delay=121))
            # 以后可能加一个legend(doge)
            Schedule("52-59 23 * * * rank_and_notice_official", lambda: daka_utils.daka_all_headless(daka_list_obj, http2_client_obj, only_rank_and_notice=0, random_delay=121))
            Schedule("30-59 23 * * * buka", lambda: buka()) # 补卡

        daka_list_obj.init_notice_storage(logger)
        # waitress.serve(app, host=config.host, port=config.port, threads=6, expose_tracebacks = True)
        http_server = WSGIServer((config.host, config.port), socketio.run(app, host=config.host, port=config.port), log=logging)
        http_server.serve_forever()
        # 如果是服务器，要在每天早上打卡后重新加载daka_list_obj，以刷新cheat_tracker和member_list