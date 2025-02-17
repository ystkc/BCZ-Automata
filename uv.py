# uv.py
'''【独立工具】读取./uv/下的所有文件夹名，然后绘User Visit Index图（数据来源：automata的shutdown_sallow_unotice_getuv）'''
import os
import sqlite3
import datetime

def load_result_from_dir_name():
    if not os.path.exists("./uv/"):
        os.mkdir("./uv/")

    result = []
    for file in os.listdir("./uv/"):
        if os.path.isdir(os.path.join("./uv/", file)):
            result.append(file.split("-"))
    return result

def load_result_from_db():
    db_name = '../BCZ-Notice-Examiner/bcz_notice.db'
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT TODAY_DATE, UV_INDEX FROM OTHER_INFO")
    result = c.fetchall()
    conn.close()
    if len(result) == 0:
        return []
    return result[:-1]

result = load_result_from_db()
thirty_days_ago = ((datetime.datetime.now() - datetime.timedelta(days=35)).strftime("%Y%m%d"))
dates = []
uvs = []
for dir in result: # 按格式dates-uvs读取文件夹名
    date, uv = dir
    date = str(date)
    uv = int(uv)
    # if date < thirty_days_ago:
    #     continue
    try:
        index = dates.index(date)
        uvs[index] = max(uvs[index], int(uv))
    except ValueError:
        dates.append(date)
        uvs.append(int(uv))

# matplotlib绘图（dates是%Y%m%d格式的日期，uvs是纵坐标）
import matplotlib.pyplot as plt

# 折线散点图+标记值
plt.plot(dates, uvs, marker='o', linestyle='-')
for i in range(len(dates)):
    plt.text(dates[i], uvs[i], uvs[i], ha='center', va='bottom', fontsize=10)
plt.xlabel("Date")
# x倾斜45度
plt.xticks(rotation=45)
plt.ylabel("UV Index")
plt.title("23:58 Daka Count")
plt.show()
    