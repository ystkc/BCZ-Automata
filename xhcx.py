# xhcx.py
'''【独立工具】小号查询器，从指定班级分享码查询班级成员IP和当日打卡时间。'''
'''声明：本程序获取的都是公开校牌信息，请勿用于违法用途。'''
import json
import threading
import time
import os
import random
from src.http2_client import http2_client
http2_client_obj = http2_client()
from src.get_headers import getHeaders

storage_path = "./storage/"

users = []
with open("user_cookie.json","r",encoding="utf-8") as f:
    users = json.load(f)

cookies = []
for user in users:
    cookies.append(user["cookie"])



target_share_key = input("请输入要查询的班级分享码：")
# 查询storage


ips = {}
member_cnt = 0
ips_completed_times = {}

# https://group.baicizhan.com/group/information?shareKey=
url = f'https://group.baicizhan.com/group/information?shareKey={target_share_key}'
headers = getHeaders("$group", cookies[0], int(time.time()), index=1)
response_json = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/information?shareKey={target_share_key}', headers, None, True)

group_info = response_json['data']['groupInfo']
members = response_json['data']['members']
member_cnt = len(members)

class_name = group_info['name']
group_id = group_info['id']
notice = group_info['notice']


def get_leader_info(members):
    for member in members:
        if member['leader'] == True:
            return member['uniqueId'], member['nickname']
    return '',''
leader_id, leader_name = get_leader_info(members)


print(f"班级名称：{class_name}({group_id})班长：{leader_name}({leader_id})")
print(f"公告：{notice}")
s = input("1 to continue:")
if s != '1':
    exit()

if os.path.exists(f"{storage_path}{target_share_key}.json"):
    with open(f"{storage_path}{target_share_key}.json","r",encoding="utf-8") as f:
        data = json.load(f)
        ips = data["ips"]
        member_cnt = sum(data["ips"].values())
        ips_completed_times = data["ips_completed_times"]
else:

    # 用cookie中的令牌请求接口，查询班内成员信息
    cookie_cnt = len(cookies)
    index = 0
    while index < member_cnt:
        member = members[index]
        unique_id = member['uniqueId']
        completed_times = member['completedTimes']
        completed_time = member['completedTime']
        def get_ip(unique_id):
            # 获取校牌，统计ip
            # https://social.baicizhan.com/api/deskmate/personal_details?uniqueId=
            url = f'https://social.baicizhan.com/api/deskmate/personal_details?uniqueId={unique_id}'
            headers = getHeaders("$social", cookies[index%cookie_cnt], int(time.time()), index=1)
            response = http2_client_obj.send_http2_request('GET', url, headers, None, True)
            if response['code'] == 1:
                ip = response['data']['ip']
                if ip not in ips:
                    ips[ip] = 0
                    ips_completed_times[ip] = []
                ips[ip] += 1
                if completed_time > 0:
                    ips_completed_times[ip].append(completed_time)
                print(f"查询{unique_id}:{completed_time};{ip}")
        threading.Thread(target=get_ip, args=(unique_id,)).start()
        index += 1
        time.sleep(random.randint(150,550)/1000)

print(f"共有{member_cnt}人，其中{len(ips)}个ip")
for ip, cnt in ips.items():
    print(f"{ip}：{cnt}人")

if not os.path.exists(storage_path):
    os.makedirs(storage_path)
with open(f"{storage_path}{target_share_key}.json","w",encoding="utf-8") as f:
    json.dump({"ips":ips, "ips_completed_times":ips_completed_times}, f, ensure_ascii=False, indent=4)


# 对于最多的ip，统计完成时间
max_ip = max(ips, key=ips.get)
max_ip_completed_times = ips_completed_times[max_ip]

import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from datetime import datetime

# 假设 ips 和 max_ip_completed_times 已经定义好
# ips = {"省份": 人数, ...}
# max_ip_completed_times = {"省份": [时间戳列表], ...}
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 动态设置字体，确保中文能够显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 动态设置字体，确保中文能够显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号

def plot_ips_and_times(class_name, ips, max_ip_completed_times):
    # 创建一个新的图形
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # 准备数据
    provinces = list(ips.keys())
    counts = list(ips.values())

    # 第一个子图 - 省份的人数分布
    bars = ax1.bar(provinces, counts, color='skyblue')
    ax1.set_title(f'{class_name} 各省人数统计')
    ax1.set_xlabel('省份')
    ax1.set_ylabel('人数')
    ax1.tick_params(axis='x', rotation=45)  # 旋转 x 轴标签以更好地适应

    # 在柱状图上标注数值
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{int(height)}',  # 显示整数
                 ha='center', va='bottom')

    # 获取今天的开始和结束时间戳
    today_start = int(datetime.combine(datetime.today(), datetime.min.time()).timestamp())
    today_end = int((datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

    # 过滤今天的打卡时间
    today_checkins = {province: [t for t in times if today_start <= t < today_end] for province, times in max_ip_completed_times.items()}

    # 第二个子图 - 今天内每个省份的打卡时间分布
    for province, times in today_checkins.items():
        if not times:
            continue  # 如果没有今天的打卡记录，则跳过该省份
        # 将时间戳转换为可读日期格式
        readable_dates = [datetime.fromtimestamp(t) for t in times]
        ax2.scatter([province]*len(times), readable_dates, label=province, s=2)  # 调整点的大小

    ax2.set_title(f'{class_name} 打卡时间分布')
    ax2.set_xlabel('省份')
    ax2.set_ylabel('打卡时间')
    ax2.tick_params(axis='x', rotation=45)
    
    # 设置 y 轴（时间轴）格式
    ax2.yaxis_date()
    ax2.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # 只显示小时和分钟
    ax2.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)

    # 设置 y 轴的范围为今天的开始到结束
    ax2.set_ylim([datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                  datetime.now()])

    # 显示图例
    ax2.legend(title='省份', bbox_to_anchor=(1.05, 1), loc='upper left')

    # 调整布局以防止重叠
    plt.tight_layout()

    # 显示图表
    plt.show()

# 假设 ips 和 max_ip_completed_times 已经定义好
# ips = {"省份": 人数, ...}
# max_ip_completed_times = {"省份": [时间戳列表], ...}

# 调用函数
plot_ips_and_times(class_name, ips, ips_completed_times)