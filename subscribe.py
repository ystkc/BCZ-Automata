# subscribe.py
'''【独立工具】查询已订阅的用户加入小班的公告更新'''
import os
import time
import requests
import argparse
from textwrap import dedent
from src.config import Config
from prompt_toolkit.widgets import TextArea, Label
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import D
os.chdir(os.path.dirname(os.path.abspath(__file__)))
config = Config()
base_url = f"http://{config.host}:{config.port}"

def fetch_data(url):
    """获取JSON数据"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e} {response.text}")
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

def display_info(base_url, force_refresh, force_id) -> dict:
    # 获取用户信息
    url_str = f"{base_url}/subscribe/data"
    if force_refresh:
        url_str += f'?force_refresh=true&force_refresh_only_id={force_id}'
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
    if not data.get('memberlist_required', False):
        return data
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
        'latest_timestamp': data.get('timestamp'),
    }
    try:
        response = requests.post(
            url,
            params=params,
            json={"reply_content": content, "code": operation_code},
            timeout=10
        ).json()
        if response['code'] == 200:
            print("成功 "+response['msg'])
            input("按任意键继续...")
        elif response['code'] == 455:
            print(response['msg'] + " 正在刷新")
            input("按任意键继续...")
        else:
            print(f"失败 {response['msg']}")
            input("按任意键继续...")
    except Exception as e:
        print(f"请求错误: {e}")
        input("按任意键继续...")

def edit_text(notice) -> str:
    text_area = TextArea(
        scrollbar=True,       # 滚动条
        line_numbers=True,    # 行号
        wrap_lines=True,     # 自动换行
        multiline=True,
        width=80,
        height=D(preferred=20),
        prompt='',
        text=notice,
    )

    # 创建字符计数器标签
    char_count_label = Label(
        text=f' 当前字符数: {len(notice)}  上限150  Ctrl+C取消并退出  Ctrl+S确认并退出',
        style='bg:blue fg:white',
    )

    # 定义文本变化回调函数
    def update_char_count(event):
        char_count_label.text = f' 当前字符数: {len(text_area.text)}  上限150  Ctrl+C取消并退出  Ctrl+S确认并退出'

    kb = KeyBindings()
    @kb.add('c-s')
    def cs(event):
        event.app.exit()
    
    @kb.add('c-c')
    def cc(event):
        text_area.text = notice
        update_char_count(None)
        event.app.exit()

    # 绑定文本变化事件
    text_area.buffer.on_text_changed += update_char_count

    
    app = Application(
        layout=Layout(HSplit([text_area, char_count_label])),
        key_bindings=kb,
        full_screen=True,
    )
    app.run()
    return text_area.text
    

def main():
    action = ''
    # 否则显示信息并进入交互模式
    force_refresh = False
    force_id = ''
    while True:
        os.system('cls')
        data = display_info(base_url, force_refresh, force_id)
        force_refresh = False
        
        while True:
            print(f"操作提示: {data.get('operation', '')}")
            action = input("\n请输入：\n数字会被识别为操作\nr. 刷新\nfr. 强制刷新\n请选择（数字/r/fr）: ")
            try:
                code = int(action)
                reply_content = None
                if code == data.get('reply_required') or code in range(data.get('reply_required_min', -2147483647), data.get('reply_required_max', -2147483647) +1):
                    if data.get('textarea_required'):
                        reply_content = edit_text(data['notice'])
                    else:
                        reply_content = input("请输入回复内容: ")
                send_reply(data, reply_content, int(code))
                break
            except ValueError:
                if action == 'r':
                    break
                elif action == 'fr':
                    force_id = input('请输入强制刷新ID（-1表示所有）:')
                    force_refresh = True
                    break
                

if __name__ == "__main__":
    main()