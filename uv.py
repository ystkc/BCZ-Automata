# 读取./uv/下的所有文件夹名
import os
import datetime

if not os.path.exists("./uv/"):
    os.mkdir("./uv/")

result = []
for file in os.listdir("./uv/"):
    if os.path.isdir(os.path.join("./uv/", file)):
        result.append(file)

thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=35)).strftime("%Y%m%d")
dates = []
uvs = []
for dir in result: # 按格式dates-uvs读取文件夹名
    date, uv = dir.split("-")
    if date < thirty_days_ago:
        continue
    try:
        index = dates.index(date)
        uvs[index] = max(uvs[index], int(uv))
    except ValueError:
        dates.append(date)
        uvs.append(int(uv))

# matplotlib绘图（dates是%Y%m%d格式的日期，uvs是纵坐标）
import matplotlib.pyplot as plt

# 散点图+标记值
plt.scatter(dates, uvs)
for i in range(len(dates)):
    plt.text(dates[i], uvs[i], uvs[i], ha='center', va='bottom', fontsize=10)
plt.xlabel("Date")
plt.ylabel("UV Index")
plt.title("User Visit Index of Different Dates")
plt.show()
    