import sys
import time
import logging
import requests
import json
import httpx
import hashlib
import certifi
import random
import datetime
import traceback

from flask import Flask, Response, render_template, jsonify, request
from werkzeug.serving import WSGIRequestHandler, _log

from src import bcz
from src.config import Config
import src.thrift_utils as thrift_utils
from src.thrift_utils import user_dict
from src.thrift_utils import getHeaders

# if '--debug' in sys.argv or (hasattr(sys, 'gettrace') and sys.gettrace() is not None):
if '--debug' in sys.argv:
    level = logging.DEBUG
else:
    level = logging.INFO

logging.basicConfig(
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    level=level
)

WSGIRequestHandler.address_string = lambda self: self.headers.get('x-real-ip', self.client_address[0])
class MyRequestHandler(WSGIRequestHandler):
    def log(self, type, message, *args):
        _log(type, f'{self.address_string()} {message % args}\n')


app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False

config = Config()
user_dict_obj = user_dict()
user_dict_list = user_dict_obj.user_dict_list

@app.route('/')
def index():
    return render_template('index.html')

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
        user_dict = user_dict_obj.find(unique_id)
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
        user_dict = user_dict_obj.find(unique_id)
        
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
        user_dict = user_dict_obj.find(unique_id)
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

@app.route('/accounts/list', methods=['GET'])
def accounts_list():
    '''获取用户列表'''
    try:
        result = []
        for user in user_dict_list:
            result.append({
                'name': user['config']['name'],
                'unique_id': user['config']['unique_id'],
                'device_id': user['cookie']['device_id'],
                'access_token': user['cookie']['access_token']
            })
        return restful(200, '获取用户列表成功', result)
    except Exception as e:
        return restful(400, f'{e}')
@app.route('/accounts/add', methods=['POST'])
def accounts_add():
    '''添加用户'''
    try:
        name = request.json.get('name', '')
        unique_id = request.json.get('unique_id', '')
        access_token = request.json.get('access_token', '')
        device_id = hashlib.md5(str(access_token).encode('utf-8')).hexdigest()[:16]
        if not name or not unique_id or not access_token:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        if user_dict_obj.find(unique_id) is not None:
            return restful(400, '用户已存在')
        user_dict_obj.add_user(access_token, unique_id, name, device_id)
        return restful(200, '添加用户成功')
    except Exception as e:
        return restful(400, f'{e}')

@app.route('/accounts/delete', methods=['POST'])
def accounts_delete():
    '''删除用户'''
    try:
        unique_id = request.json.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict_obj.del_user(unique_id)
        return restful(200, '删除用户成功')
    except Exception as e:
        raise e
        return restful(400, f'{e}')
    
notice_list = []
pace = 6
def change_notice_sse_func(unique_id, group_share_key, content):
    for event in change_notice_sse_func_(unique_id, group_share_key, content):
        target = event.replace('\n', '<br>')
        target = target.replace('\r', '<br>')
        target = target.replace('<br><br>', '<br>')
        # print(target)
        yield f"data: {target}\n\n"
def change_notice_sse_func_(unique_id, group_share_key, content):
    # print(content)
    # yield content
    # return
    user_dict = user_dict_obj.find(unique_id)
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
        yield '通知发送成功<br><br>' + content
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
        yield f'通知发送失败{response_json["message"]}<br>'


@app.route('/api/change_notice_sse', methods=['GET'])
def change_notice_sse():
    '''获取通知'''
    try:
        unique_id = int(request.args.get('unique_id', ''))
        group_share_key = request.args.get('group_share_key', '')
        content = ''
        for notice in notice_list:
            if notice['unique_id'] == unique_id and notice['group_share_key'] == group_share_key:
                content = notice['content']
                notice_list.remove(notice)
                break
        if content == '':
            return restful(400, '通知内容为空')
        return Response(change_notice_sse_func(unique_id, group_share_key, content), mimetype='text/event-stream')
    except Exception as e:
        return restful(400, f'{e}')
        
@app.route('/api/change_notice', methods=['POST'])
def change_notice():
    '''获取通知'''
    try:
        unique_id = int(request.json.get('unique_id', ''))
        group_share_key = request.json.get('group_share_key', '')
        content = request.json.get('content', '')
        if not unique_id or not group_share_key or not content:
            print(unique_id, group_share_key, content)
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        notice_list.append({'unique_id': unique_id, 'group_share_key': group_share_key, 'content': content})
        return restful(200, '通知已收到')
    except Exception as e:
        return restful(400, f'{e}')
    
@app.route("/own_groups", methods=['GET'])
def own_groups():
    try:
        unique_id = request.args.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = user_dict_obj.find(unique_id)
        time_long = int(time.time() * 1000)
        response = requests.get('https://group.baicizhan.com/group/own_groups?uniqueId=0', headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)) # 我的小班
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
                'name': group['name'],
                'share_key': group['shareKey'],
                'rank': group['rank'],
                'introduction': introduction,
                'notice': notice,
                'leader': group['leader'],
                'group_nickname': '未获取'
            })

        #  https://group.baicizhan.com/group/study_words_together_home_page
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = requests.get('https://group.baicizhan.com/group/study_words_together_home_page', headers=headers)
        response_json = response.json()
        # print(response_json['data']['todayDaka'])
        today_daka = '1已打卡' if response_json['data']['todayDaka'] else '0未打卡'
        
        response = requests.get('https://group.baicizhan.com/group/get_group_user_info', headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)) # 我的小班
        result = bcz.userBasicInfo(user_dict['cookie']['access_token'])
        user_dict_obj.update_book_id(unique_id, result.user_info.current_word_level_id)
        daka_timestamp = result.learn_info.last_sync_done_score_time
        date = datetime.datetime.fromtimestamp(daka_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        data = response.json()['data']
        groups.append({
            'name': f'用户年级组{data["grade"]}',
            'share_key': '',
            'rank': f'{today_daka}于{date}',
            'introduction': f'加入上限{data["groupLimiteNumber"]}',
            'notice': f'授权上限{data["groupAuthorizationLimiteNumber"]}',
            'group_nickname': ''
        })

        return restful(200, '获取用户群组成功', groups)
    except Exception as e:
        raise e
    #     return restful(400, f'{e}')
    


@app.route('/api/daka', methods=['GET'])
def daka():
    '''打卡'''
    try:
        unique_id = request.args.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        # sse
        return Response(daka_sse(unique_id), mimetype='text/event-stream')
    except Exception as e:
        with open(f'error_{unique_id}_{int(time.time())}.txt', 'w', encoding='utf-8') as f:
            f.write(str(e))
        return restful(400, f'{e}')


    
def daka_sse(unique_id):
    try:
        index, user_dict = user_dict_obj.find(unique_id)
        user_dict['config']['user_index'] = index
        user_cnt = len(user_dict_list)
        for msg in thrift_utils.daka(user_cookie = user_dict['cookie'], user_config = user_dict['config'], total_user_cnt=user_cnt):
            yield f'data: {msg}\n\n'
    except Exception as e:
        with open(f'error_{unique_id}_{int(time.time())}.txt', 'w', encoding='utf-8') as f:
            f.write(str(e))
            f.write(traceback.format_exc())
            raise e 
            
        

@app.route('/api/more_groups', methods=['POST'])
def more_groups():
    '''开班位'''
    try:

        unique_id = request.json.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = user_dict_obj.find(unique_id)
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
    logging.info('BCZ-Automata 启动中...')
    app.run(config.host, config.port, request_handler=MyRequestHandler, debug=True)