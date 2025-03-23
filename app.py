import asyncio
from contextlib import asynccontextmanager
import json
import sys
import time
import sqlite3
import logging
import queue
from urllib import parse

debug = True
if '--debug' in sys.argv:
    level = logging.DEBUG
    debug = True
else:
    level = logging.INFO
    debug = False

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import requests
import os
import hashlib
import random
import datetime
import traceback
import threading

from src import bcz
from src.config import Config
import src.daka_utils as daka_utils
from src.daka_utils import daka_list_class, notice_subscriber
from src.daka_utils import getHeaders, daka_all_headless, stargazer_class
from src.http2_client import http2_client
from append import append_user_data


from src.notice_parser import static_export_class

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    schedule = threading.Thread(target=schedule_task)
    broadcaster = threading.Thread(target=asyncio.run, args=(message_dispatcher(),))
    schedule.start()
    broadcaster.start()
    # prevent_sleep()
    yield
    user_messages.put(('end', 0, ''))
    for ws in connected_clients:
        try:
            await ws.close()
        except:
            pass
    schedule.join()
    broadcaster.join()
    allow_sleep()
app = FastAPI(lifespan=lifespan)
app.mount("/lib", StaticFiles(directory="static/lib"), name="lib")
app.mount("/img", StaticFiles(directory="static/img"), name="img")
@app.get('/favicon.ico') # 用mount会307+404，应该是只有文件夹可以
async def favicon(request: Request):
    return FileResponse('static/favicon.ico')

templates = Jinja2Templates(directory="templates")

notice_subscriber_obj = notice_subscriber(logger, http2_client_obj, config)
connected_clients = []
# 抽象行为：=[WebSocket] (相当于在里面插入一个抽象基类！笨蛋)
user_messages = queue.Queue()
star_gazer = stargazer_class(logger, http2_client_obj, config, daka_list_obj, user_messages)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    '''接受打卡请求'''
    await websocket.accept()
    connected_clients.append(websocket)
    # await websocket.send_text('ready##')
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith('daka: '):
                daka(data.split(' ')[1])
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def message_dispatcher():
    '''广播打卡状态消息'''
    while True:
        msg_type, unique_id, msg = user_messages.get()
        if msg_type == 'end':
            http2_client_obj.set_closing_state(True)
            while not daka_list_obj.is_empty():
                await asyncio.sleep(1)
            break
        try:
            # await asyncio.gather(*[client.send_text(data=f'{unique_id}#{msg_type}#{msg}') for client in connected_clients])
            for client in connected_clients:
                await client.send_text(data=f'{unique_id}#{msg_type}#{msg}')
        except:
            logger.error(f'websocket 发送失败{traceback.format_exc()}')

def daka(unique_id: str):
    '''打卡'''
    try:
        try:
            assert unique_id.isdigit()
            assert daka_list_obj.has_user(unique_id)
        except AssertionError:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = daka_list_obj.get_user_dict(unique_id)
        daka_all_headless(user_messages, daka_list_obj, http2_client_obj, -1, [user_dict], 0)
        return restful(200, f'已将{unique_id}加入打卡队列')
    except Exception as e:
        err_str = traceback.format_exc()
        user_messages.put(('error', unique_id, f'打卡出现错误{e}\n{err_str}'))
        daka_list_obj.add_warning(f'打卡api出现错误{e}\n{err_str}')

@app.get('/get_bad_words')
async def get_bad_words(request: Request):
    '''获取坏词'''
    return restful(200, daka_list_obj.get_bad_words())

@app.get('/clear_bad_words')
async def clear_bad_words(request: Request):
    '''清空坏词'''
    daka_list_obj.clear_bad_words()
    daka_list_obj.close()
    return restful(200, '清空成功')

@app.route('/')
async def index(request: Request):
    '''跳转到/accounts'''
    return templates.TemplateResponse('index.html', {'request': request})


# 以下是调试接口
@app.get('/buka')
async def buka(request: Request):
    '''测试接口'''
    return restful(200, f'buka cnt:{buka()}')

@app.get('/reload')
async def reload_http2(request: Request):
    '''重新加载http2客户端'''
    await http2_client_obj.reload_http2_client()
    return restful(200, '成功')


@app.get('/save')
async def save_config(request: Request):
    '''立即保存配置'''
    daka_list_obj.close(no_check_daka=True)
    return restful(200, '保存成功')

@app.get('/check_daka')
async def check_daka(request: Request, include_not_daka = False):
    '''检查打卡'''
    return restful(200, daka_list_obj.check_not_daka_users(include_not_daka=include_not_daka))


def parse_notice_online(only_raw_notice=True):
    logger.info('开始更新违禁词库...')
    conn = sqlite3.connect(config.database_path)
    daka_list_obj.notice_parser.update_notice(conn, only_raw_notice=only_raw_notice) # 根据现有公告数据库自动更新
    conn.close()

status = 0
@app.get('/update_notice')
async def parse_notice(request: Request):
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

@app.get('/accounts')
async def accounts(request: Request):
    return templates.TemplateResponse('accounts.html', {'request': request})

@app.post('/api/reply_and_ack')
async def reply_and_ack(request: Request, item: dict):
    unique_id = item.get('unique_id', '')
    group_share_key = item.get('group_share_key', '')
    content = item.get('content', '')
    if not unique_id or not group_share_key or not content:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    user_dict = daka_list_obj.get_user_dict(unique_id)
    try:
        result_str, _ = notice_subscriber_obj.reply_and_ack(unique_id, user_dict, group_share_key, content)
        return restful(200, result_str)
    except Exception as e:
        return restful(400, f'{e}')

@app.post('/api/quit_group')
async def quit_group(request: Request, item: dict):
    '''退出群组'''
    try:
        unique_id = item.get('unique_id', '')
        group_share_key = item.get('group_share_key', '')

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
        
@app.post('/api/join_group')
async def join_group(request: Request, item: dict):
    '''加入群组'''
    try:
        unique_id = item.get('unique_id', '')
        group_share_key = item.get('share_key', '')
        group_invite_key = item.get('invite_code', '')
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

@app.get('/append')
async def append_accounts(request: Request):
    '''添加或更新用户配置信息（用excel表格导入）'''
    return templates.TemplateResponse('append.html', {'request': request})

@app.post('/append/submit')
async def append_accounts_submit(request: Request, item: dict):
    try:
        text = item.get('content', '')
        if not text:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        return restful(200, append_user_data(text))
    except Exception as e:
        return restful(400, f'{e}{traceback.format_exc()}')

@app.post('/accounts/delete')
async def accounts_delete(request: Request, item: dict):
    '''删除用户'''
    try:
        unique_id = item.get('unique_id', '')
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        daka_list_obj.delete_accounts(unique_id)
        return restful(200, '删除成功')
    except Exception as e:
        return restful(400, f'{e}{traceback.format_exc()}')


@app.get('/accounts/reload')
async def accounts_reload(request: Request):
    '''重新加载用户列表'''
    daka_list_obj.reload_user_dict()
    return await accounts_list(request)


@app.get('/accounts/list')
async def accounts_list(request: Request):
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


@app.get('/api/change_notice_sse')
async def change_notice_sse(request: Request, unique_id: int=0, group_share_key: str='', group_id: str=''):
    '''获取通知'''
    try:
        unique_id = int(unique_id)
        content = ''
        global notice_list
        for notice in notice_list:
            if notice['unique_id'] == unique_id and notice['group_share_key'] == group_share_key:
                content = notice['content']
                mentioned_ids = notice['mentioned_ids']
                notice_list.remove(notice)
                break
        if content == '':
            return restful(400, '通知内容为空')
        return StreamingResponse(change_notice_sse_func(unique_id, group_share_key, content, mentioned_ids, group_id), media_type='text/event-stream')
    except Exception as e:
        return restful(400, f'{e}')

@app.post('/api/change_notice')
async def change_notice(request: Request, item: dict):
    '''获取通知'''
    try:
        unique_id = int(item.get('unique_id', ''))
        group_share_key = item.get('group_share_key', '')
        content = item.get('content', '')
        mentioned_ids = item.get('mentioned_ids', '')
        if not unique_id or not group_share_key or not content:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        global notice_list
        notice_list.append({'unique_id': unique_id, 'group_share_key': group_share_key, 'content': content, 'mentioned_ids': mentioned_ids})
        return restful(200, '通知已收到')
    except Exception as e:
        return restful(400, f'{e}')
    
@app.get('/subscribe')
async def subscribe(request: Request):
    '''生成html页面，供用户查看公告(一个)'''
    return templates.TemplateResponse('subscribe.html', {'request': request})

@app.get('/subscribe/data')
async def subscribe_data(request: Request):
    top_notice = notice_subscriber_obj.get_top_notice(daka_list_obj)
    top_notice['introduction'] = top_notice['introduction'].replace('\n', '<br>')
    top_notice['notice'] = top_notice['notice'].replace('\n', '<br>')
    return restful(200, '获取公告成功', top_notice)

@app.post('/subscribe/reply')
async def subscribe_reply(request: Request, item: dict, unique_id: str='', group_share_key: str='', group_id: str='', notice_hash: str=''):
    # 从content中获取reply_content
    reply_content = item.get('reply_content', '')
    correspond = item.get('correspond', True)
    if not unique_id or not group_id or not group_share_key or not notice_hash:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    user_dict = daka_list_obj.get_user_dict(unique_id)
    code, result_str = notice_subscriber_obj.read_reply_and_ack(unique_id, user_dict, group_share_key, group_id, notice_hash, reply_content, correspond)
    return restful(code, result_str)

@app.post('/api/change_avatar')
async def change_avatar(request: Request, unique_id: str='', img_data: UploadFile=File(...)):
    '''将用户头像上传到服务器'''
    try:
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = daka_list_obj.get_user_dict(unique_id)
        if not user_dict:
            return restful(400, '用户不存在')
        access_token = parse.unquote(user_dict['cookie']['access_token']).encode('utf-8')
        boundary = b'0xKhTmLbOuNdArY-12EA39A8-13AD-4DD1-A552-9E9D3F35390A'
        img_content = await img_data.read()
        form_data = b"--" + boundary + b"\r\nContent-Disposition: form-data; name=\"token\"\r\n\r\n" + access_token + b"\r\n--" + boundary + b"\r\nContent-Disposition: form-data; name=\"image\"; filename=\"avatar.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n" + img_content + b"\r\n--" + boundary + b"--\r\n"
        headers = {
            'Cookie': f'access_token={access_token}',
            'Content-Type': 'multipart/form-data; charset=utf-8; boundary=0xKhTmLbOuNdArY-12EA39A8-13AD-4DD1-A552-9E9D3F35390A',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; DCO-AL00 Build/9aaea7d.0)',
            'Host': 'avatar.baicizhan.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'Content-Length': str(len(form_data))
        }
        response = http2_client_obj.post('https://avatar.baicizhan.com/avatar/upload', headers=headers, json=form_data)
        result_json = response.json()
        return restful(200, str(result_json), result_json)
    except Exception as e:
        return restful(400, f'{e}')

@app.get("/own_groups")  
async def own_groups(request: Request, unique_id: str=''):
    # return restful(200, '获取用户群组成功', [{'name': '用户年级组10', 'share_key': '', 'rank': '10已打卡于2022-01-01 00:00:00', 'introduction': '加入上限10', 'notice': '授权上限10', 'group_nickname': ''}])
    try:
        if not unique_id:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        user_dict = daka_list_obj.get_user_dict(unique_id)
        time_long = int(time.time() * 1000)
        headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = await http2_client_obj.asyncFetch('https://group.baicizhan.com/group/own_groups?uniqueId=0', 'GET', headers=headers, payload=None) # 我的小班
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
        response = await http2_client_obj.asyncFetch('https://group.baicizhan.com/group/study_words_together_home_page', 'GET', headers=headers, payload=None)
        response_json = response.json()
        today_daka = '1已打卡' if response_json['data']['todayDaka'] else '0未打卡'

        # 'https://group.baicizhan.com/group/get_group_user_info'
        response = await http2_client_obj.asyncFetch('https://group.baicizhan.com/group/get_group_user_info', 'GET', headers=headers, payload=None)
        data = response.json()['data']

        result = bcz.userBasicInfo(user_dict['cookie']['access_token'], http2_client_obj.get_http2_client())
        daka_timestamp = result.learn_info.last_sync_done_score_time
        user_dict['config']['book_id'] = result.user_info.current_word_level_id
        user_ip_desc = result.user_info.ip_desc
        # user_school_name = result.user_info.user_education_info.school_name
        

        date = datetime.datetime.fromtimestamp(daka_timestamp).strftime('%Y-%m-%d %H-%M-%S')
        user_dict['config']['grade'] = data['grade']
        cooper = user_dict['config'].get('cooper', -1)
        daka_list_obj.update_user_dict(user_dict)
        unique_id = user_dict['config']['unique_id']
        groups.append({
            'name': f'<img src="{result.user_info.avatar}" style="width: 30px; height: 30px;" onclick="changeAvatar({unique_id})"/><br>({result.user_info.nickname})<br>年级{data["grade"]}书本{user_dict["config"]["book_id"]}(新学{result.learn_info.daily_plan_count}复习{result.learn_info.review_plan_count})/{user_ip_desc}',
            'share_key': '',
            'rank': f'{today_daka}于{date}<br>+<span class="cooper">{cooper}</span>',
            'introduction': data["groupLimiteNumber"],
            'notice': f'授权上限{data["groupAuthorizationLimiteNumber"]}',
            'group_nickname': ''
        })

        return restful(200, '获取用户群组成功', groups)
    except Exception as e:
        return restful(400, traceback.format_exc())


async def get_nickname(main_token, http2_client_obj: http2_client, unique_id, group_share_key, user_dict):
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
    rank = await http2_client_obj.asyncFetch(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=1', 'GET', headers=headers, payload=None)
    # last_week_rank = requests.get(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=2', headers=headers)
    last_week_rank = await http2_client_obj.asyncFetch(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=2', 'GET', headers=headers, payload=None)
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
    # 遍历，如果有人的async default_nickname和昵称相同，则是没改过昵称。
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

@app.get('/subscribe/get_nickname')
@app.get('/api/get_nickname')
async def get_nickname_(request: Request, unique_id: str='', group_share_key: str=''):
    '''（改公告时）获取班内改昵称的列表'''
    try:
        user_dict = daka_list_obj.get_user_dict(unique_id)
        my_reply, monitor_reply, group_nickname = await get_nickname(config.main_token, http2_client_obj, unique_id, group_share_key, user_dict)
        return restful(200, '获取班内改昵称的列表成功', {'my_reply': my_reply, 'monitor_reply': monitor_reply, 'group_nickname': group_nickname})
    except Exception as e:
        traceback.print_exc()
        return restful(400, f'{e}')

@app.post('/change_token')
async def change_token(request: Request, item: dict):
    '''修改魔法token'''
    try:
        unique_id = item.get('unique_id', '')
        access_token = daka_list_obj.get_access_token(unique_id)
        if not access_token:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        response = requests.get(f'http://mitm.it')
        if 'traffic is not passing through mitmproxy' in response.text:
            return restful(400, '请先启动BCZ-Automata的mitmproxy脚本，并正确设置代理')
        response = requests.get(f'http://www.baicizhan.com/change_token/{access_token}/{unique_id}')
        return restful(200, response.text)
    except Exception as e:
        return restful(400, f'{e}')
    
@app.post('/api/more_groups')
async def more_groups(request: Request, item):
    '''开班位'''
    try:

        unique_id = item.get('unique_id', '')
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

@app.get('/blacklist')
async def blacklist(request: Request):
    '''导出黑名单'''
    try:
        exporter = static_export_class()
        exporter.export_black_list()
        return restful(200, '导出黑名单成功')
    except Exception as e:
        return restful(400, f'{e}')

@app.get('/login')
async def login(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})

@app.get('/user')
async def user(request: Request):
    return templates.TemplateResponse('user.html', {'request': request})

@app.post('/send_sms')
async def send_sms(request: Request, item: dict):
    '''发送短信验证码'''
    phone = item.get('phone', '')
    if not phone:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        bcz.sendSmsVerifyCode(phone)
        return restful(200, '验证码已发送到您的手机，请查收')
    except Exception as e:
        return restful(400, f'{e}')

@app.post('/user_login')
async def user_login(request: Request, item: dict):
    '''用户登陆'''
    phone = item.get('phone', '')
    code = item.get('code', '')
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
        if os.system(config.shutdown_command):
            logger.error('关闭失败')
        else:
            logger.info('BCZ-Automata 关闭命令执行成功')
    except:
        pass


def restful(code: int, msg: str = '', data: dict = {}) -> Response:
    '''以RESTful的方式进行返回响应'''
    retcode = 1
    if code == 200:
        retcode = 0
    return Response(
        content=json.dumps({'code': code,
            'retcode': retcode,
            'msg': msg,
            'data': data
    }, ensure_ascii=False), status_code=code, media_type='application/json; charset=UTF-8')

def prevent_sleep():
    '''防止系统进入休眠'''
    # 注意：对于笔记本电脑，还需要手动设置关上盖子不睡眠
    os.system(config.prevent_sleep_command)

def allow_sleep():
    '''允许系统进入休眠'''
    os.system(config.allow_sleep_command)

def shutdown_sallow_unotice_getuv(): # 在每天的58-59 23 * * 运行，根据星期执行不同的功能
    '''关闭系统/允许休眠/升级通知'''
    weekday = datetime.datetime.now().weekday() # 要立即获取，也就是前一天的星期
    # 等待直到主线程运行完毕
    while not daka_list_obj.is_empty() or daka_list_obj.is_closing():
        time.sleep(10)
    daka_list_obj.export_2048_group_info() # 在主线程保存完毕后才导出

    if weekday == 6: # 星期日晚上
        ...
    elif weekday >= 0 and weekday <= 5: # 星期一到星期六晚上
        shutdown() # 180s内关机（否则会被休眠）
        allow_sleep() # 设置180s休眠

def buka():
    not_daka_users = daka_list_obj.check_not_daka_users(include_not_daka=True)
    print(f"正在为{len(not_daka_users)}人补卡")
    if len(not_daka_users) > 0: # -1 正常打卡，-2 补卡
        daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=-2, user_dict_list=not_daka_users, random_delay=180)
    return len(not_daka_users)

def sync_and_subscribe():
    '''同步和订阅服务'''
    try:
        for comm in config.sync_command:
            os.system(comm)
    except Exception as e:
        logger.error(f"执行同步命令失败：{e}")
        
def notice_collector():
    '''按照schedule_task的配置，收集公告'''
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=1, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=2, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=3, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=4, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=5, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=6, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=7, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=0, random_delay=168)
    time.sleep(200)
    daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=2048, random_delay=168)
    logger.info("公告收集完成!")

@app.get('/collect_notice')
async def collect_notice(request: Request):
    '''收集公告'''
    try:
        threading.Thread(target=notice_collector).start()
        return restful(200, '收集公告任务已启动')
    except Exception as e:
        return restful(400, f'{e}')
    
def schedule_task():
    if config.stargazer_enable:
        star_gazer.start()
    if not debug and '--static' not in sys.argv:
        Schedule("58-59 23 * * 0-6 shutdown_sallow_unotice_getuv", lambda: shutdown_sallow_unotice_getuv())

        Schedule("* 5-10 * * 0 daka_schedule", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj,http2_client_obj,-1, random_delay=3000))
        Schedule("* 5-10 * * 1-6 daka_schedule", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj,http2_client_obj,-1, random_delay=2000))
        Schedule("* 6-7 * * 0-6 sync_and_subscribe", lambda: sync_and_subscribe())
        Schedule("* 4-8,21-23 * * 0-6 prevent_sleep", lambda: prevent_sleep())

        if '--test' in sys.argv:
            Schedule("* * * * * tester", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=2048, random_delay=21))
        if config.archiever_enable: # 收集打卡数据、公告数据
            Schedule("30-59 23 * * * rank_and_notice_bronze", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=1, random_delay=168))
            Schedule("33-59 23 * * * rank_and_notice_silver", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=2, random_delay=168))
            Schedule("36-59 23 * * * rank_and_notice_gold", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=3, random_delay=168))
            Schedule("39-59 23 * * * rank_and_notice_platinum", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=4, random_delay=168))
            Schedule("42-59 23 * * * rank_and_notice_diamond", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=5, random_delay=168))
            Schedule("45-59 23 * * * rank_and_notice_stellar", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=6, random_delay=168))
            Schedule("* 6-8 * * 6 champion_dawn", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=7, random_delay=168))
            Schedule("* 12-14 * * 6 champion_noon", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=7, random_delay=168))
            Schedule("48-59 23 * * * rank_and_notice_champion", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=7, random_delay=168))
            # 以后可能加一个legend(doge)
            Schedule("51-59 23 * * * rank_and_notice_official", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=0, random_delay=168))
            Schedule("54-59 23 * * * rank_and_notice_2048", lambda: daka_utils.daka_all_headless(user_messages, daka_list_obj, http2_client_obj, only_rank_and_notice=2048, random_delay=168))
        Schedule("30-59 23 * * * buka", lambda: buka()) # 补卡
    try:
        daka_list_obj.init_notice_storage(logger)
    except Exception as e:
        logger.error(f"初始化公告存储失败：{e}")
        http2_client_obj.set_closing_state(True)

if __name__ == '__main__':
    for name in logging.Logger.manager.loggerDict.keys():
        if 'httpx' in name: # 输出http2多路请求的日志，如需要requests的日志，则加入'urllib3' in name
            tlogger = logging.getLogger(name)
            tlogger.setLevel(logging.DEBUG)

    logger.info('BCZ-Automata 启动中...')
    if debug:
        uvicorn.run(app, host=config.host, port=config.port, log_level='debug')
    else:
        uvicorn.run(app, host=config.host, port=config.port, log_level='info')
