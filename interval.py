'''【独立工具】读取记录中序列+2到-1的时间差并作图'''
import sqlite3
# 设置运行路径为文件路径
import os
import matplotlib.pyplot as plt
os.chdir(os.path.dirname(__file__))

# 连接数据库
conn = sqlite3.connect('stargazer.db')
cursor = conn.cursor()
data = []
# 遍历每个表
for table_name in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    # 打印表名
    print(table_name[0])
    result = cursor.execute("SELECT TIMESTAMP, STAR FROM " + table_name[0]).fetchall()
    prev_star = 0
    prev_timestamp = 0
    status = 0
    for row in result:
        curr_timestamp = row[0]
        curr_star = row[1]
        if status == 1 and curr_star == prev_star + 1:
            data.append(curr_timestamp - prev_timestamp)
            status = 0
        if curr_star == prev_star + 2:
            status = 1
        prev_star = curr_star
        prev_timestamp = curr_timestamp

    # 作图
    plt.plot(data, label=table_name[0])
    data = []

plt.xlabel('次数')
plt.ylabel('间隔时间')
plt.title('Stargazer Interval')
plt.legend()
plt.show()

        
