# subscribe.py
'''【独立工具】查询已订阅的用户加入小班的公告更新'''
import os
import time
import requests
import argparse
from textwrap import dedent
from src.config import Config
config = Config()
base_url = f"http://{config.host}:{config.port}"

def fetch_data(url):
    """获取JSON数据"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def display_squares(dates):
    """将打卡数据转换为控制台可显示的字符"""
    squares = []
    for d in dates:
        if d == 1:
            squares.append('■')  # 绿色方块
        elif d == 0:
            squares.append('□')  # 灰色方块
        else:
            squares.append(' ')  # 透明/无效
    # 每7个换行显示两周数据
    return '\n'.join([' '.join(squares[i:i+7]) for i in range(0, len(squares), 7)])

def display_info(base_url, force_refresh) -> dict:
    # 获取用户信息
    url_str = f"{base_url}/subscribe/data"
    if force_refresh:
        url_str += '?force_refresh=true'
    user_data = fetch_data(url_str)
    if not user_data:
        print("无效的用户数据")
        return {}
    
    data = user_data['data']
    auth = data['notice_hash'] == 'auth'
    if auth:
        print("\033[1;31m发现了新的授权请求！ʕ⊙ᴥ⊙ʔ\033[0m")
    if not data['notice']:
        data['notice'] = '无通知'
    data['notice'] = data.get('notice', '').replace('<br>','\n')
    data['introduction'] = data.get('introduction', '').replace('<br>','\n')
    print(dedent(f"""
班长\033[1;33m{data['user_name']}\033[0m({data['unique_id']})的组
\033[1;36m{data['group_name']}\033[0m({data['group_id']})[{data['group_share_key']}]
来自{data.get('from_unique_id', '')}
介绍：{data['introduction']}
剩余{data['remain_count']}订阅"""))
    time.sleep(1)
    print(dedent(f"""通知：{data['notice']} ({data['notice_hash']})
    """))
    if data['unique_id'] == -1:
        return data

    # 获取打卡数据
    nickname_url = f"{base_url}/subscribe/get_nickname?unique_id={data['unique_id']}&group_share_key={data['group_share_key']}"
    nick_data = fetch_data(nickname_url)
    if not nick_data:
        return data

    print("\n打卡记录：")
    for unique_id, item in nick_data['data']['group_nickname'].items():
        print(dedent(f"""
{item['nickname']}({unique_id}): ({item['completed_times']}/{item['duration_days']})
组昵称: {item['group_nickname']}
{display_squares(item['two_week_daka_dates'])}
        """))
    
    print(f"我的回复: {nick_data['data']['my_reply']}")
    print(f"组长回复: {nick_data['data']['monitor_reply']}")
    
    return data

def send_reply(data, content, operation_code: int):
    """发送回复"""
    url = f"{base_url}/subscribe/reply"
    
    params = {
        'group_id': data['group_id'],
        'unique_id': data['unique_id'],
        'from_unique_id': data.get('from_unique_id', ''),
        'group_share_key': data['group_share_key'],
        'notice_hash': data['notice_hash'],
        'latest_timestamp': data['timestamp'],
    }
    try:
        response = requests.post(
            url,
            params=params,
            json={"reply_content": content, "code": operation_code},
            timeout=10
        ).json()
        if response['code'] == 200:
            print("操作成功！"+response['msg'])
        else:
            print(f"操作失败: {response['msg']}")
            input("按任意键继续...")
    except Exception as e:
        print(f"请求错误: {e}")
        input("按任意键继续...")

def main():
    action = ''
    # 否则显示信息并进入交互模式
    force_refresh = False
    while True:
        os.system('cls')
        data = display_info(base_url, force_refresh)
        force_refresh = False
        
        while True:
            action = input("\n请输入：\n1. 操作\n2. 刷新\n3. 强制刷新\n请选择（1/2/3）: ")
            if action == '1':
                print(f"操作提示: {data['operation']}")
                code = input("请输入操作码: ")
                reply_content = None
                if code == data.get('reply_required'):
                    reply_content = input("请输入回复内容: ")
                send_reply(data, reply_content, int(code))
                break
            elif action == '2':
                break
            elif action == '3':
                force_refresh = True
                break
                

if __name__ == "__main__":
    main()