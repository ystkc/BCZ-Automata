import sqlite3

# 连接到数据库
conn = sqlite3.connect('../BCZ-Notice-Examiner/bcz_notice.db')
cursor = conn.cursor()
cursor.execute("""
               

ALTER TABLE MEMBERS DROP COLUMN COMPLETED_TIMES_6;""")
cursor.execute("""ALTER TABLE MEMBERS DROP COLUMN DURATION_DAYS_6;
""")
conn.commit()
conn.close()
exit(0)
# 数据结构：
'''4881484	0.656	1
1906185	0.256	2
480217	0.064	3
110136	0.014	4
36587	0.005	5
16353	0.002	6'''
# 期望小班数：1.45
# N=1000000, DAY = 30
'''CREATE TABLE IF NOT EXISTS MEMBERS (
    USER_ID INTEGER,             -- 用户ID 4bytes
    COMPLETED_TIME INTEGER,      -- 打卡时间 4bytes
    TODAY_DATE INTEGER,          -- 记录日期 * MMDD 2bytes
    WORD_COUNT INTEGER,          -- 今日词数 2bytes
    STUDY_CHEAT INTEGER,         -- 是否作弊 1bytes
    BOOK_NAME INTEGER,           -- 学习词书 2bytes
    GROUP_ID_1 INTEGER,          -- 小班ID 3bytes
    COMPLETED_TIMES_1 INTEGER,   -- 打卡天数 2bytes
    DURATION_DAYS_1 INTEGER,     -- 入班天数 2bytes
    GROUP_ID_2 INTEGER,
    COMPLETED_TIMES_2 INTEGER,
    DURATION_DAYS_2 INTEGER,
    GROUP_ID_3 INTEGER,
    COMPLETED_TIMES_3 INTEGER,
    DURATION_DAYS_3 INTEGER,
    GROUP_ID_4 INTEGER,
    COMPLETED_TIMES_4 INTEGER,
    DURATION_DAYS_4 INTEGER,
    GROUP_ID_5 INTEGER,
    COMPLETED_TIMES_5 INTEGER,
    DURATION_DAYS_5 INTEGER,
    GROUP_ID_6 INTEGER,
    COMPLETED_TIMES_6 INTEGER,
    DURATION_DAYS_6 INTEGER,
    UNIQUE(USER_ID, TODAY_DATE)  -- 以用户ID和记录日期组合为主键
);'''
# 对应关系：1bytes/用户每天 = 30000000 = 32MB
# 基本信息：15bytes/用户每天
# 小班信息：
cursor.execute("""DROP TABLE IF EXISTS MEMBERS_GROUPS;""")
cursor.execute("""CREATE TABLE IF NOT EXISTS MEMBERS_GROUPS (
    USER_ID INTEGER,                         -- 用户ID
    GROUP_ID INTEGER,                        -- 小班ID
    STREAK_TIMES INTEGER,                    -- 连胜天数
    COMPLETED_TIMES_START INTEGER,           -- 连胜开始时的打卡天数
    ACHIEVED_DATE INTEGER,                   -- 达到这个连胜的日期
    DURATION_DAYS INTEGER                   -- 入班天数
);""")
# 更新逻辑：如果今天已打卡(completed_time不为0)，则current_completed_times先-1，如果today_date - achieved_date = current_completed_times - streak_times - completed_times_start，则更新连胜信息
# 否则新加入一行，COMPLETED_TIMES_START = current_completed_times

# 查询原表中的数据
date_limit = 103# 1.05 还没有增加二次获取completed_times校准，会有错误数据
cnt = cursor.execute(f"SELECT COUNT(*) FROM MEMBERS WHERE TODAY_DATE > {date_limit}").fetchone()[0]
print(f"There are {cnt} rows in the original table.")
cursor.execute(f"""
    SELECT 
        USER_ID, COMPLETED_TIME, TODAY_DATE, GROUP_ID_1, COMPLETED_TIMES_1, DURATION_DAYS_1,
        GROUP_ID_2, COMPLETED_TIMES_2, DURATION_DAYS_2,
        GROUP_ID_3, COMPLETED_TIMES_3, DURATION_DAYS_3,
        GROUP_ID_4, COMPLETED_TIMES_4, DURATION_DAYS_4,
        GROUP_ID_5, COMPLETED_TIMES_5, DURATION_DAYS_5,
        GROUP_ID_6, COMPLETED_TIMES_6, DURATION_DAYS_6
    FROM MEMBERS WHERE TODAY_DATE > {date_limit} ORDER BY TODAY_DATE ASC 
""") 
def date_delta(date1: int, date2: int): # 计算两个MMDDYYYY格式日期的差值，返回天数
    # 由于本次处理的数据只在1.03-1.19之间，所以可以直接减
    return (date1 - date2) // 10000

user_streak_info = {} # (user_id, group_id): (streak_times, completed_times_start, achieved_date, duration_days)
prev_user_streak_info = {} # 用于记录上一次的连胜信息
user_streak_buffer = []
# 如果有多个，则保留achieved_date最大的那个
processed_cnt = 0
# 提取并插入到新表中
for row in cursor.fetchall():
    processed_cnt += 1
    if processed_cnt % 10000 == 0:
        print(f"Processed {processed_cnt} rows...")
    user_id = row[0]
    completed_time = row[1]
    today_date_mmdd = row[2]
    today_date_mmddyyyy = today_date_mmdd * 10000 + 2025 # 从MMDD格式转换为MMDDYYYY
    for i in range(1, 7):
        group_id = row[i*3]
        completed_times = row[i*3+1]
        duration_days = row[i*3+2]
        if group_id == None:
            break
        if completed_time == 0:
            completed_times += 1
        if (user_id, group_id) not in user_streak_info:
            if completed_time == 0:
                continue
            if completed_times == duration_days:
                user_streak_info[(user_id, group_id)] = (completed_times, 1, today_date_mmddyyyy, duration_days)
            else:
                user_streak_info[(user_id, group_id)] = (1, completed_times, today_date_mmddyyyy, duration_days)
            continue
        streak_times, completed_times_start, achieved_date, duration_days_old = user_streak_info[(user_id, group_id)]
        delta = date_delta(today_date_mmddyyyy, achieved_date) - 1 - (completed_times - streak_times - completed_times_start)
        if delta < 0:
            print(user_id, group_id, today_date_mmddyyyy, achieved_date, completed_times, streak_times, completed_times_start, delta)
            # 检查本次延长后是否和上次连接
            print(prev_user_streak_info.get((user_id, group_id)))
            if (user_id, group_id) in prev_user_streak_info:
                prev_streak_times, prev_completed_times_start, prev_achieved_date, prev_duration_days = prev_user_streak_info[(user_id, group_id)]
                prev_delta = date_delta(achieved_date, prev_achieved_date) - (completed_times - streak_times - completed_times_start)
                if prev_delta == 0:
                    streak_times = prev_streak_times
                    completed_times_start = prev_completed_times_start
                    achieved_date = prev_achieved_date
                    duration_days = prev_duration_days
                    prev_user_streak_info.pop((user_id, group_id))
                    print('connect_success')
            # if delta < -1:
                # input()
            delta = 0
            streak_times += -delta # 经过手动确认，可能是单词机（或者后门）

        if delta == 0:
            streak_times += date_delta(today_date_mmddyyyy, achieved_date)
            user_streak_info[(user_id, group_id)] = (streak_times, completed_times_start, today_date_mmddyyyy, duration_days)
        else: # 增加新纪录
            if completed_time == 0:
                continue
            prev_item = prev_user_streak_info.get((user_id, group_id))
            if prev_item is not None:
                user_streak_buffer.append((user_id, group_id, prev_item[0], prev_item[1], prev_item[2], prev_item[3]))
            prev_user_streak_info[(user_id, group_id)] = (streak_times, completed_times_start, achieved_date, duration_days_old)
            if completed_times == duration_days:
                user_streak_info[(user_id, group_id)] = (completed_times, 1, today_date_mmddyyyy, duration_days)
            else:
                user_streak_info[(user_id, group_id)] = (1, completed_times, today_date_mmddyyyy, duration_days)
        
# 将user_streak_info和prev_user_streak_info并入user_streak_buffer
for (user_id, group_id), (streak_times, completed_times_start, achieved_date, duration_days) in user_streak_info.items():
    if streak_times > 0:
        user_streak_buffer.append((user_id, group_id, streak_times, completed_times_start, achieved_date, duration_days))
for (user_id, group_id), (streak_times, completed_times_start, achieved_date, duration_days) in prev_user_streak_info.items():
    if streak_times > 0:
        user_streak_buffer.append((user_id, group_id, streak_times, completed_times_start, achieved_date, duration_days))

# 统计streak_times为0-10的数量
cnt = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
for (user_id, group_id, streak_times, completed_times_start, achieved_date, duration_days) in user_streak_buffer:
    if streak_times < 10:
        cnt[streak_times] += 1
print(f"Streak times count: {cnt}")
thresh = int(input("Enter the threshold of streak times: "))
# 过滤掉streak_times小于thresh的记录
user_streak_buffer = [x for x in user_streak_buffer if x[2] >= thresh]

# 插入到新表中
cursor.executemany("""
    INSERT INTO MEMBERS_GROUPS (USER_ID, GROUP_ID, STREAK_TIMES, COMPLETED_TIMES_START, ACHIEVED_DATE, DURATION_DAYS)
    VALUES (?,?,?,?,?,?)
""", user_streak_buffer)

# 删除原表中的字段
cursor.execute("""
    ALTER TABLE MEMBERS
    DROP COLUMN GROUP_ID_1,
    DROP COLUMN COMPLETED_TIMES_1,
    DROP COLUMN DURATION_DAYS_1,
    DROP COLUMN GROUP_ID_2,
    DROP COLUMN COMPLETED_TIMES_2,
    DROP COLUMN DURATION_DAYS_2,
    DROP COLUMN GROUP_ID_3,
    DROP COLUMN COMPLETED_TIMES_3,
    DROP COLUMN DURATION_DAYS_3,
    DROP COLUMN GROUP_ID_4,
    DROP COLUMN COMPLETED_TIMES_4,
    DROP COLUMN DURATION_DAYS_4,
    DROP COLUMN GROUP_ID_5,
    DROP COLUMN COMPLETED_TIMES_5,
    DROP COLUMN DURATION_DAYS_5,
    DROP COLUMN GROUP_ID_6,
    DROP COLUMN COMPLETED_TIMES_6,
    DROP COLUMN DURATION_DAYS_6
""")

# 提交更改并关闭连接
conn.commit()
conn.close()
