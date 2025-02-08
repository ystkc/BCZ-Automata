# cheat.py
'''【独立工具】绘图显示昨日500词以上用户的作弊、爆破情况，来自目录下的"cheat_tracker.%YY-%MM-%DD.csv"文件，数据来源于automata的notice_and_rank'''
import os
import csv
path = "./logs/"

date_str = input('请输入日期(格式如2021-01-01):')
target_name = f'cheat-tracker_{date_str} .csv'
result = {}
result_not_daka = {}
for file in os.listdir(path):
    if file == target_name:
        with open(os.path.join(path, file), "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                timestamp = int(row[2])
                status = int(row[3]) # 1作弊 0正常
                # 转换为UTC+8的今日秒数
                if timestamp == 0:
                    result_not_daka[row[0]] = (int(row[1]), 0, int(row[3])) # 对应word,time,status
                else:
                    result[row[0]] = (int(row[1]), (timestamp + 28800) % 86400, int(row[3])) # 对应word,time,status
        break


import matplotlib.pyplot as plt
# 画两个图表，一个是已打卡的时间-词数-是否作弊，另一个是未打卡的时间-词数-是否作弊
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
# 第一个图表

def get_style(status): # 作弊1用宏色，正常0用蓝色，爆破成功3用绿色
    if status == 1:
        return "red"
    elif status == 0:
        return "grey"
    else:
        return "blue"

colors = [get_style(status) for word, time, status in result.values()]

# 画图(设置点小一点)
axes[0].scatter([time for word, time, status in result.values()], [word for word, time, status in result.values()], c=colors, s=1, cmap="Set1")

fig.suptitle("已打卡")
axes[0].set_xlabel("Time (UTC+8)")
axes[0].set_ylabel("Words")
# 第二个图表

colors = [get_style(status) for word, time, status in result_not_daka.values()]

# 画图
axes[1].scatter([time for word, time, status in result_not_daka.values()], [word for word, time, status in result_not_daka.values()], c=colors, s=1, cmap="Set1")

fig.suptitle("未打卡")
axes[1].set_xlabel("Time (UTC+8)")
axes[1].set_ylabel("Words")

plt.show()