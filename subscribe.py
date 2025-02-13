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

def display_info(base_url):
    # 获取用户信息
    user_data = fetch_data(f"{base_url}/subscribe/data")
    if not user_data:
        print("无效的用户数据")
        return
    

    data = user_data['data']
    data['notice'] = data['notice'].replace('<br>','\n')
    data['introduction'] = data['introduction'].replace('<br>','\n')
    print(dedent(f"""
用户\033[1;33m{data['user_name']}\033[0m({data['unique_id']})[{data['group_share_key']}]的组：
\033[1;36m{data['group_name']}\033[0m({data['group_id']})
介绍：{data['introduction']}
剩余{data['remain_count']}订阅"""))
    time.sleep(1)
    print(dedent(f"""通知：{data['notice']} ({data['notice_hash']})
    """))
    if data['unique_id'] == -1:
        return

    # 获取打卡数据
    nickname_url = f"{base_url}/subscribe/get_nickname?unique_id={data['unique_id']}&group_share_key={data['group_share_key']}"
    nick_data = fetch_data(nickname_url)
    if not nick_data:
        return

    print("\n打卡记录：")
    for unique_id, item in nick_data['data']['group_nickname'].items():
        print(dedent(f"""
{item['nickname']}({unique_id}): ({item['completed_times']}/{item['duration_days']})
组昵称: {item['group_nickname']}
{display_squares(item['two_week_daka_dates'])}
        """))
    
    print(f"我的回复: {nick_data['data']['my_reply']}")
    print(f"组长回复: {nick_data['data']['monitor_reply']}")

def send_reply(base_url, content, correspond=True):
    """发送回复"""
    user_data = fetch_data(f"{base_url}/subscribe/data")
    if not user_data:
        return

    data = user_data['data']
    params = {
        "unique_id": data['unique_id'],
        "group_id": data['group_id'],
        "notice_hash": data['notice_hash'],
        "group_share_key": data['group_share_key']
    }
    url = f"{base_url}/subscribe/reply"
    
    try:
        response = requests.post(
            url,
            params=params,
            json={"reply_content": content, "correspond": correspond}
        )
        if response.ok:
            print("操作成功！")
        else:
            print(f"操作失败: {response.status_code}")
    except Exception as e:
        print(f"请求错误: {e}")

def main():
    parser = argparse.ArgumentParser(description="订阅管理客户端")
    parser.add_argument("--reply", help="回复内容，留空则标记已读")
    args = parser.parse_args()

    if args.reply is not None:
        # 如果有回复参数则直接发送
        send_reply(base_url, args.reply, correspond=(args.reply != ""))
    else:
        # 否则显示信息并进入交互模式
        while True:
            os.system('cls')
            display_info(base_url)
            action = input("\n操作：\n1. 回复\n2. 标记已读\n3. 刷新\n请选择（1/2/3）: ")
            if action == '1':
                content = input("输入回复内容: ")
                # if content == '':
                    # if input("只收到不回复，确认吗？(y/n): ") != 'y':
                        # continue
                send_reply(base_url, content)
            elif action == '2':
                send_reply(base_url, "", correspond=False)
            elif action == '3':
                continue
            else:
                print("无效选择")

if __name__ == "__main__":
    main()