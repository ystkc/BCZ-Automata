import os
import csv
path = "./logs/"
# 打开目录下的"cheat_tracker.%YY-%MM-%DD.csv"文件

result = {}
result_not_daka = {}
for file in os.listdir(path):
    if file.startswith("cheat_tracker.") and file.endswith(".csv"):
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


import matplotlib.pyplot as plt
# 画两个图表，一个是已打卡的时间-词数-是否作弊，另一个是未打卡的时间-词数-是否作弊
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
# 第一个图表

def get_style(status): # 作弊1用宏色，正常0用蓝色，爆破成功3用绿色
    if status == 1:
        return "r"
    elif status == 0:
        return "b"
    else:
        return "g"

colors = [get_style(status) for word, time, status in result.values()]

# 画图(设置点小一点)
axes[0].scatter([time for word, time, status in result.values()], [word for word, time, status in result.values()], c=colors, s=1)

fig.suptitle("已打卡")
axes[0].set_xlabel("Time (UTC+8)")
axes[0].set_ylabel("Words")
# 第二个图表

colors = [get_style(status) for word, time, status in result_not_daka.values()]

# 画图
axes[1].scatter([time for word, time, status in result_not_daka.values()], [word for word, time, status in result_not_daka.values()], c=colors, s=1)

fig.suptitle("未打卡")
axes[1].set_xlabel("Time (UTC+8)")
axes[1].set_ylabel("Words")

plt.show()