# total_length.py
'''【调试工具】用于计算某天的公告总长度'''
db_path = "../BCZ-Notice-Examiner/bcz_notice.db"
import sqlite3
conn = sqlite3.connect(db_path, uri=True)
c = conn.cursor()
# 读取数据库中所有今天的公告（TODAY_DATE 或 LATEST_DATE大于今天0点时间戳的）
import datetime
date = input("Please input the date (YYYYMMDD): ")
today_start = datetime.datetime.combine(datetime.datetime.strptime(date, '%Y%m%d'), datetime.time.min).timestamp()
today_end = datetime.datetime.combine(datetime.datetime.strptime(date, '%Y%m%d'), datetime.time.max).timestamp()
c.execute("SELECT CONTENT FROM notice WHERE (DATE >= ? AND DATE <= ?) OR (LATEST_DATE >= ? AND LATEST_DATE <= ?)", (today_start, today_end, today_start, today_end))
rows = c.fetchall()
conn.close()
total_length = 0
for row in rows:
    total_length += len(row[0])
print("Today's notices total length:", total_length)
print("Count: ", len(rows))
