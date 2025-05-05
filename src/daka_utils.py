
import logging
import queue
from src.thrift_utils import report_event, social_send_share_success, user_study, user_dict, http2_client
from src.config import Config
from src.get_headers import getHeaders
# from src.avatar import find_unique_id
from src.notice_parser import NoticeParser
import zipfile
import os
import re
import csv
import random
import time
import json
import datetime
import sqlite3
import threading
import hashlib
import traceback
from fuzzywuzzy import process
from collections import Counter
DEBUG = False
DEBUG_SIZE = 1
LOAD_MEMBER_TABLE = True # 如果要一天获取多次，请设置为True
MEMBERS_GROUPS_LIMIT = 2147483647 # 数据库循环队列的大小（旧的会被删除）
DICT_DB_PATH = 'lookup.db'

# 功能开关
BCZ_NCSVC = False # 已于12.5结束
YZDD = False # 2024.12.2已经结束

def clear_learnt_list(unique_id):
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''DROP TABLE IF EXISTS {learnt_words_db}''')
    conn.commit()

def get_learnt_list(unique_id):
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {learnt_words_db} (
        TOPIC_ID INTEGER,
        DATE TEXT)
    ''')
    conn.commit()
    result = cursor.execute(f'''SELECT TOPIC_ID FROM {learnt_words_db}''')
    learnt_list = [i[0] for i in result.fetchall()]
    return learnt_list

def add_learnt_list(unique_id, topic_id: list):
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {learnt_words_db} (
        TOPIC_ID INTEGER,
        DATE TEXT)
    ''')
    conn.commit()
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    for i in topic_id:
        cursor.execute(f'''INSERT INTO {learnt_words_db} (TOPIC_ID, DATE) VALUES (?,?)''', (i, today_date))
    conn.commit()

def get_history_learnt_list(unique_id, delta=1):
    '''获取delta天前的学习列表'''
    conn = sqlite3.connect('learnt_words.db')
    learnt_words_db = f'learnt_words_{unique_id}'
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {learnt_words_db} (
        TOPIC_ID INTEGER,
        DATE TEXT)
    ''')
    conn.commit()
    history_date = (datetime.datetime.now() - datetime.timedelta(days=delta)).strftime('%Y-%m-%d')
    print(f"get{delta}={history_date}")
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    result = cursor.execute(f'''SELECT TOPIC_ID FROM {learnt_words_db} WHERE DATE == ?''', (history_date, ))
    learnt_list = [i[0] for i in result.fetchall()]
    return learnt_list

from src.bcz import getRandomWordIDInBook

class daka_list_class:
    def is_default_avatar(avatar_url: str):
        return avatar_url.endswith('default_avatar_new2.png') or avatar_url.endswith('default_avatar.png')

    def __init__(self, logger, http2_client_obj: http2_client, config: Config):
        self.last_remove_timestamp = 0 # 0空闲/已关闭，1运行中，-1关闭中，timestamp准备关闭倒计时
        self.http2_client_obj = http2_client_obj
        self.logger = logger
        self.daka_list = {}
        self.daka_pk_status = {} # 0未启动，-1匹配中，1对战中
        self.daka_pk_status_expire_time = {}
        self.current_matching_king_id = set()
        self.current_rivals = set()
        self.pk_results = []
        self.is_king = {}
        self.logs = []
        self.warnings = []
        self.class_list_2048 = []
        for group_id in config.class_list_2048:
            self.class_list_2048.append({'groupId': group_id, 'score': None})
        self.anticheat_power = config.anticheat_power
        self.do_not_charge_pk_energy = config.do_not_charge_pk_energy
        self.lock = threading.Lock()
        self.patch_list = [] # 公告块，切分合并成1000长度(每次检测最多1000个)，检测后切除通过的部分，得到坏词
        self.status = [] # 标记每个patch_list中的检查状态：0未检查，1已从后检查，2已双向检查
        self.class_list = {}
        self.time_start = int(time.time())
        # 加载用户字典
        self.user_dict_obj = user_dict()
        logger.info(f'加载了{self.get_user_cnt()}个用户')

        # 初始化数据储存信息
        self.notice_and_rank_path = config.database_path
        self.puzzle_path = config.puzzle_path
        self.dict_patch_db_path = config.dict_patch_db_path
        self.log_dir = config.log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
        self.pk_blacklist = config.pk_blacklist
        self.pk_whitelist = config.pk_whitelist

        # 初始化单词大赛数据库
        if BCZ_NCSVC:
            puzzle_conn = sqlite3.connect(self.puzzle_path)
            cursor = puzzle_conn.cursor()
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS BCZ_NCSVC (
                INDEX_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID INTEGER UNIQUE,
                QUESTION TEXT,
                CHN_MEAN TEXT,
                ANSWER TEXT,
                OPTIONS1 TEXT,
                OPTIONS2 TEXT,
                OPTIONS3 TEXT,
                TOPIC_ID INTEGER)
            ''')
            puzzle_conn.commit()
            puzzle_conn.close()
        # 单词数据库
        
        wl_patch_conn = sqlite3.connect(self.dict_patch_db_path)
        cursor = wl_patch_conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS dict_bcz (
            TOPIC_ID INTEGER,
            WORD TEXT,
            ANSWER TEXT,
            RANK TEXT)
        ''')
        wl_patch_conn.commit()
        wl_patch_conn.close()
        # 公告数据库
        conn = sqlite3.connect(self.notice_and_rank_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS notice (
            GROUP_ID INTEGER,
            RANK_TYPE_RANK INTEGER, -- rank_type * 1000 + rank
            CONTENT VARCHAR(1000),
            DATE INTEGER,
            LATEST_DATE INTEGER,
            SCORE INTEGER,
            CHECKED INTEGER)  -- 9位数，第1位(0未检查，1已从后检查，2已双向检查)，2-5位(000-1000)上次检查到的位置, 6-8位(000-1000)上次检查到的位置''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS MEMBERS (                   -- 成员表（以用户 + 小班 + 日期 为主键）
            USER_ID INTEGER,             -- 用户ID   *
            COMPLETED_TIME INTEGER,                -- 打卡时间
            TODAY_DATE INTEGER,             -- 记录日期 * MMDD
            WORD_COUNT INTEGER,                 -- 今日词数
            STUDY_CHEAT INTEGER,                -- 是否作弊
            BOOK_NAME INTEGER,                     -- 学习词书
            UNIQUE(USER_ID, TODAY_DATE))''')
        cursor.execute("""CREATE TABLE IF NOT EXISTS MEMBERS_GROUPS (
            USER_ID INTEGER,                         -- 用户ID
            GROUP_ID INTEGER,                        -- 小班ID
            STREAK_TIMES INTEGER,                    -- 连胜天数（最长完成 = 开始天数 + 连胜天数）
            COMPLETED_TIMES_START INTEGER,           -- 连胜开始时的打卡天数
            START_DATE INTEGER,                      -- 开始日期
            ACHIEVED_DATE INTEGER,                   -- 达到这个连胜的日期
            DURATION_DAYS INTEGER,                   -- 最新的入班天数（也就是最长的）
            UNIQUE(USER_ID, GROUP_ID, START_DATE))""")
        cursor.execute('''CREATE TABLE IF NOT EXISTS BOOK_NAME (
            HASH_ID INTEGER PRIMARY KEY,
            BOOK_NAME TEXT,
            BOOK_ID INTEGER,
            BOOK_URL TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS USER_NAME ( -- 最新的用户信息
            NICKNAME TEXT,
            USER_ID INTEGER PRIMARY KEY,
            USER_AVATAR TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS GROUP_NAME ( -- 最新的小班信息
            GROUP_ID INTEGER PRIMARY KEY,
            SHARE_KEY VARCHAR(16),
            MONITOR_ID INTEGER,
            GROUP_NAME VARCHAR(10),
            GROUP_INTRODUCTION VARCHAR(50),
            GROUP_AVATAR TEXT)''') # 定期备份数据库，要获得旧的小班、用户信息，看历史版本即可
        cursor.execute('''CREATE TABLE IF NOT EXISTS OTHER_INFO ( -- 其他数据
            TODAY_DATE INTEGER PRIMARY KEY,
            UV_INDEX INTEGER,
            MAX_GROUP_ID INTEGER,
            GROUP_COUNT_1 INTEGER,
            GROUP_COUNT_2 INTEGER,
            GROUP_COUNT_3 INTEGER,
            GROUP_COUNT_4 INTEGER,
            GROUP_COUNT_5 INTEGER,
            GROUP_COUNT_6 INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS GROUP_RANK ( -- 小班排名
            DATE INTEGER, 
            GROUP_ID INTEGER,
            RANK_TYPE_RANK INTEGER,
            DAKA_COUNT INTEGER,
            TOTAL_DAKA_COUNT INTEGER,
            FINISHING_RATE REAL,
            UNIQUE(DATE, GROUP_ID))''')
        conn.commit()
        conn.close()
        # 检查lookup.db
        # wl_conn = sqlite3.connect(DICT_DB_PATH)
        if not os.path.exists('lookup.db'):
            if not os.path.exists('lookup.rar'): 
                raise Exception('lookup.rar不存在，请重新安装程序')
            with zipfile.ZipFile('lookup.rar', 'r') as z:
                z.extractall()
                logger.info('解压lookup.rar成功')
        
        # 加载king状态
        try:
            with open('king_status.json', 'r', encoding='utf-8') as f:
                self.is_king = json.load(f)
            # 将所有key转为int
            self.is_king = {int(k):v for k,v in self.is_king.items()}
        except:
            self.is_king = {}
        self.latest_check_notice_timestamp = 0
        self.notice_parser = NoticeParser()

        # 创建线程来执行耗时的初始化任务
        self.__not_prepared = True
    
    def set_is_king(self, unique_id, rank, star, energy):
        self.is_king[unique_id] = [rank, star, energy]

    def query_is_king(self, unique_id):
        return self.is_king.get(unique_id, [''])[0] == 'king'
    
    def set_pk_status(self, unique_id, status, expire_time=-1):
        self.daka_pk_status[unique_id] = status
        self.daka_pk_status_expire_time[unique_id] = expire_time
        if status == -1:
            self.current_matching_king_id.add(unique_id)
        elif status == 1 or status == 0 or status == 2: # 0未启动，-1匹配中，1对战中，2体力不足
            try:
                self.current_matching_king_id.remove(unique_id)
            except:
                pass
    
    def query_pk_status(self, unique_id):
        expire_time = self.daka_pk_status_expire_time.get(unique_id, -1)
        if expire_time != -1 and expire_time < time.time():
            self.set_pk_status(unique_id, 0)
        return self.daka_pk_status.get(unique_id, 0)
    
    def query_current_matching_king_id(self):
        return self.current_matching_king_id
    
    def add_rival(self, unique_id):
        self.current_rivals.add(unique_id)
    
    def remove_rival(self, unique_id):
        try:
            if unique_id != -1:
                self.current_rivals.remove(unique_id)
        except:
            pass
    
    def record_pk_result(self, my_name, rival_id, rival_name, my_score, rival_score):
        self.pk_results.append((my_name, rival_id, rival_name, my_score, rival_score))
        if len(self.pk_results) > 300:
            self.save_pk_result()

    def save_pk_result(self):
        if self.pk_results == []:
            return
        # pk_%Y-%m-%d %H-%M-%S.csv
        file_name = f'pk_{datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.csv'
        with open(os.path.join(self.log_dir, file_name), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['我的名字', '对手ID', '对手名字', '我的分数', '对手分数'])
            for row in self.pk_results:
                writer.writerow(row)
        self.pk_results = []

    def delete_accounts(self, unique_id):
        '''删除账号'''
        self.user_dict_obj.delete_user(unique_id)

    def delete_old_logs(self) -> str:
        '''删除35天前的日志文件，并返回最新的日志文件名'''
        today = datetime.date.today()
        max_logname = ""
        for file_name in os.listdir(self.log_dir):
            try:
                file_date_str = file_name.split('_')[1].split(' ')[0]
                if file_name.startswith('log') and file_name > max_logname:
                    max_logname = file_name
                file_date = datetime.datetime.strptime(file_date_str, '%Y-%m-%d').date()
                if (today - file_date).days > 35:
                    os.remove(os.path.join(self.log_dir, file_name))
                    print(f'删除{file_name}')
            except:
                print(f'文件名{file_name}格式错误')
                pass
        print(f'最近日志文件名{max_logname}')
        return max_logname
    
    def init_notice_storage(self, logger):
        '''加载用户信息、小班信息、作弊信息、公告信息、坏词信息、词库信息'''
        if not self.__not_prepared: # 如果False，说明已经初始化过了。如果undefined，则抛出错误
            return

        # 读取今天的cheat_tracker
        self.load_cheat_tracker(datetime.datetime.now().strftime('%Y-%m-%d'))# 防止数据跨天

        logger.info('开始读取数据库')
        self.load_dict_db(logger)
        conn = sqlite3.connect(self.notice_and_rank_path, uri=True)
        cursor = conn.cursor()
        # 取消阻塞
        cursor.execute('''PRAGMA synchronous = OFF''')
        cursor.execute('''PRAGMA journal_mode = MEMORY''')
        cursor.execute('''PRAGMA locking_mode = EXCLUSIVE''')
        cursor.execute('''PRAGMA temp_store = MEMORY''')
        cursor.execute('''PRAGMA cache_size = -100000''')
        # 读取需要检查的notice
        self.check_list = []
        # 加载坏词
        try:
            with open('tmp_bad_words.json', 'r', encoding='utf-8') as f:
                self.bad_words = json.load(f)
        except:
            self.bad_words = []
        # 加载check_list
        cursor.execute('''SELECT GROUP_ID, CHECKED, DATE, CONTENT FROM notice WHERE CHECKED IS NOT NULL AND CHECKED < 200000000''')
        for row in cursor.fetchall():
            self.check_list.append({'group_id': row[0], 'date': row[2], 'content': row[3], 'checked': row[1]//100000000, 'cursorA': row[1]%100000000//10000, 'cursorB': row[1]%10000, 'modified': False, 'valid': True})
        logger.info(f'check_list剩余{len(self.check_list)}条')
        # 加载普通notice
        self.notice_list = {}
        cursor.execute('''SELECT GROUP_ID, CONTENT, DATE, LATEST_DATE FROM notice''')
        cnt = 0
        for row in cursor.fetchall(): # 按group_id分类
            group_id = row[0]
            if group_id not in self.notice_list:
                self.notice_list[group_id] = {}
            self.notice_list[group_id][row[1]] = (row[2], row[3])
            cnt += 1
        logger.info(f'notice_list共加载{cnt}条({len(self.notice_list)}班)')
        # 加载小班信息
        self.group_infos = {} # GROUP_ID:(GROUP_ID, GROUP_NAME, GROUP_INTRODUCTION)
        cursor.execute('''SELECT GROUP_ID, SHARE_KEY, MONITOR_ID, GROUP_NAME, GROUP_INTRODUCTION, GROUP_AVATAR FROM GROUP_NAME''')
        for row in cursor.fetchall():
            self.group_infos[row[0]] = (row[0], row[1], row[2], row[3], row[4], row[5])
        # 将2048列表中的班级ID转换为shareKey
        valid_class_list_2048 = []
        for group in self.class_list_2048:
            group_id = group['groupId']
            if group_id not in self.group_infos:
                self.add_warning(f'2048列表中班级{group_id}不存在')
            group = self.group_infos[group_id]
            valid_class_list_2048.append({'groupId': group[0],'shareKey': group[1], 'name': group[3], 'introduction': group[4].replace('\n','\\n'), 'avatar': group[5], 'score': None})
        self.class_list_2048_sharekey = valid_class_list_2048
        logger.info(f'group_infos共加载{len(self.group_infos)}班')
        # 加载用户信息
        self.user_infos = {} # USER_ID:(USER_ID, NICKNAME, USER_AVATAR)
        self.user_infos_from_avatar = {} # USER_AVATAR:USER_ID
        cursor.execute('''SELECT USER_ID, NICKNAME, USER_AVATAR FROM USER_NAME''')
        for row in cursor.fetchall():
            self.user_infos[row[0]] = (row[0], row[1], row[2])
            avatar = row[2]
            if not avatar:
                continue
            if daka_list_class.is_default_avatar(avatar):# 要同时用名字和头像判断用户
                self.user_infos_from_avatar[(avatar, row[1])] = row[0]
            else:
                self.user_infos_from_avatar[avatar] = row[0]
            
        logger.info(f'user_infos共加载{len(self.user_infos)}个用户')
        # 加载成员信息
        if LOAD_MEMBER_TABLE:
            self.load_member_list(cursor, int(datetime.datetime.now().strftime('%m%d')))
        else:
            self.member_list = {} # USER_ID: (USER_ID, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, STUDY_CHEAT, BOOK_NAME)
            self.member_groups = {}
            self.prev_user_streak_info = {}
        # 加载书本信息
        self.book_name_dict = {} # BOOK_NAME:BOOK_ID
        cursor.execute('''SELECT HASH_ID, BOOK_NAME, BOOK_ID, BOOK_URL FROM BOOK_NAME''')
        for row in cursor.fetchall():
            self.book_name_dict[row[1]] = row[0]
        # 加载其他数据
        today_date = datetime.datetime.now()
        today_date_int = int(today_date.strftime('%Y%m%d'))
        self.group_counter_date = today_date_int
        cursor.execute('''SELECT UV_INDEX, MAX_GROUP_ID, GROUP_COUNT_1, GROUP_COUNT_2, GROUP_COUNT_3, GROUP_COUNT_4, GROUP_COUNT_5, GROUP_COUNT_6 FROM OTHER_INFO WHERE TODAY_DATE == ?''', (today_date_int,))
        row = cursor.fetchone()
        if row is None:
            self.uv_index = 0
            self.max_group_id = 0
            self.group_counter = [0, 0, 0, 0, 0, 0]
            self.logger.info('没有找到其他数据')
        else:
            self.uv_index = row[0]
            self.max_group_id = row[1]
            self.group_counter = [row[2], row[3], row[4], row[5], row[6], row[7]]
            self.logger.info(f'其他数据：uv_index={self.uv_index}, max_group_id={self.max_group_id}')
            self.logger.info(f'组统计：{self.group_counter}')
        conn.close()
        # 读取log
        max_timestamp = int(today_date.timestamp()) - 86400
        print(today_date.timestamp(), max_timestamp)
        t = 0
        today_date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        max_filename = ""
        for file_name in os.listdir(self.log_dir):
            if file_name.startswith(f'log_{today_date_str}') and file_name.endswith('.txt'):
                t = int(file_name.split('.')[1])
                print(t, max_timestamp)
                if t > max_timestamp:
                    max_timestamp = t
                    max_filename = file_name
        self.logger.info(f'上次更新用户和通知状态于{int(today_date.timestamp()) - max_timestamp}秒前({max_filename})')
        self.latest_check_notice_timestamp = self.latest_check_user_timestamp = max_timestamp
        # 初始化数据库内存缓冲区
        self.notice_buffer = [] # 每天最多7000条，暂无需设置大小
        self.notice_cleared_buffer = []
        self.notice_cleared_delete_buffer = []
        self.notice_time_buffer = []
        self.notice_time_delete_buffer = []
        self.group_info_buffer = [] # 每天最多7000条，暂无需设置大小
        self.user_info_buffer = [] # 每天最多700000条，暂无需设置大小
        self.member_buffer = [] # 每天最多700000条，暂无需设置大小
        self.book_name_buffer = []
        self.group_rank_buffer = []
        self.rank_and_daka_count_temp = {}
        
        logger.info('\033[32m数据库初始化完毕\033[0m')
        self.__not_prepared = False

    def export_2048_group_info(self):
        '''导出2048列表小班信息'''
        ...
    
    def load_member_list(self, cursor: sqlite3.Cursor, date_int: int):
        self.member_groups_cnt = {} # user_id: group_id: cnt
        self.member_list = {}
        cursor.execute('''SELECT USER_ID, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, STUDY_CHEAT, BOOK_NAME FROM MEMBERS WHERE TODAY_DATE == ?''', (date_int, ))
        for row in cursor.fetchall():
            self.member_list[row[0]] = (row[0], row[1], row[2], row[3], row[4], row[5])
        self.logger.info(f'member_list共加载{len(self.member_list)}条数据')
        self.member_buffer = [] # 每天最多700000条，暂无需设置大小
        # 加载MEMBERS_GROUPS表
        self.member_groups = {}
        self.prev_user_streak_info = {}
        cursor.execute('''SELECT USER_ID, GROUP_ID, STREAK_TIMES, COMPLETED_TIMES_START, START_DATE, ACHIEVED_DATE, DURATION_DAYS FROM MEMBERS_GROUPS''')
        for row in cursor.fetchall():
            idx = (row[0], row[1])
            tp = self.member_groups.get(idx)
            if tp is None:
                self.member_groups[idx] = (row[2], row[3], row[4], row[5], row[6])
            elif row[4] > tp[4]: # 最新的连胜日期
                self.prev_user_streak_info[idx] = tp # 由于有单词机，可能出现连胜中断后补上，这里储存上一次连胜以备连接
                self.member_groups[idx] = (row[2], row[3], row[4], row[5], row[6])
            else: # 不是最新的，如果比prev_user_streak_info新，则替换prev_user_streak_info
                prev_tp = self.prev_user_streak_info.get(idx)
                if prev_tp is not None and row[4] > prev_tp[4]:
                    self.prev_user_streak_info[idx] = (row[2], row[3], row[4], row[5], row[6])

        self.logger.info(f'成员的groups共加载{len(self.member_groups)}条数据')
        self.logger.info(f'备用prev{len(self.prev_user_streak_info)}条数据')
        self.member_groups_buffer = []
        self.member_groups_delete_buffer = [] # 由于有单词机，可能出现连胜中断后补上，所以要合并后删掉之前的

    def wait(self):
        while self.__not_prepared:
            time.sleep(1)
        date_int = int(datetime.datetime.now().strftime('%m%d'))
    
    def find_unique_id(self, avatar: str, nickname):
        '''查找唯一id'''
        try:
            unique_id = avatar.split('/')[4]
            if unique_id.isdigit():
                result = int(unique_id)
                return result
        except:
            pass
        self.wait()
        if daka_list_class.is_default_avatar(avatar): # 不能根据default头像判断唯一id
            result = self.user_infos_from_avatar.get((avatar, nickname))
        else:
            result = self.user_infos_from_avatar.get(avatar)
        if result == 0:
            raise Exception(f'用户{nickname}的头像链接{avatar}爆0')
            result = None
        return result

    def optimize_db(self, conn: sqlite3.Connection):
        '''优化数据库'''
        conn.execute("PRAGMA synchronous = OFF")  # 减少磁盘同步
        # conn.execute("PRAGMA journal_mode = WAL")  # 事务一般比较大，不用WAL


    def close(self, no_check_daka=False):
        self.wait()
        close_start_time = int(time.time())
        self.last_remove_timestamp = -1
        now = datetime.datetime.now()
        # 写入缓冲区到数据库
        # 写入puzzle_buffer
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', '开始关闭', True)
        if BCZ_NCSVC and len(self.puzzle_buffer) > 0:
            puzzle_conn = sqlite3.connect(self.puzzle_path)
            self.optimize_db(puzzle_conn)
            cursor = puzzle_conn.cursor()
            cursor.executemany('''INSERT OR REPLACE INTO BCZ_NCSVC (ID, QUESTION, CHN_MEAN, ANSWER, OPTIONS1, OPTIONS2, OPTIONS3, TOPIC_ID) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', self.puzzle_buffer)
            puzzle_conn.commit()
            puzzle_conn.close()
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'写入{len(self.puzzle_buffer)}条puzzle', True)
            self.puzzle_buffer = []
        else: # 2
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', '没有puzzle', True)
        
        if len(self.patch_buffer) > 0:
            patch_conn = sqlite3.connect(self.dict_patch_db_path)
            self.optimize_db(patch_conn)
            cursor = patch_conn.cursor()
            cursor.executemany('''INSERT OR REPLACE INTO dict_bcz (ANSWER, WORD, TOPIC_ID, RANK) VALUES (?, ?, ?, ?)''', self.patch_buffer)
            patch_conn.commit()
            patch_conn.close()
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'写入{len(self.patch_buffer)}条patch', True)
            self.patch_buffer = []
        else: # 3
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', '没有patch', True)
        
        conn = sqlite3.connect(self.notice_and_rank_path)
        self.optimize_db(conn)
        cursor = conn.cursor()
        self.save_other_info(cursor)
        # 删除35天前的日志
        latest_log = self.delete_old_logs() # 这家伙也是log很多（故意的）
        with open(os.path.join(self.log_dir, latest_log), 'r', encoding='utf-8') as f:
            try:
                buka_users = f.read().split('_*')[1]
            except:
                buka_users = ''
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'35天前的日志删除完毕，上一个补卡用户：\033[1;36m{buka_users}\033[0m', True)
        # 写入king状态
        with open('king_status.json', 'w', encoding='utf-8') as f:
            json.dump(self.is_king, f, ensure_ascii=False)
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', 'king_status.json保存完毕', True)
        # 检查未打卡用户
        if close_start_time - self.latest_check_user_timestamp > 3600 and not no_check_daka:
            not_daka_users = self.check_not_daka_users(include_not_daka=False) # 有网络请求，要放在close前面，防止log太多
            self.latest_check_user_timestamp = close_start_time
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'打卡检测完毕，本轮{self.get_user_cnt()}个账号，有{len(not_daka_users)}人未打卡_*{[user["config"].get("name", user["config"]) for user in not_daka_users]}_*，共耗时{close_start_time - self.time_start}秒', True)
            for user in not_daka_users:
                self.add_warning(f'未打卡用户：{user["config"].get("name")}({user["config"].get("unique_id")})')
        else:# 5
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'最近{close_start_time - self.latest_check_user_timestamp}秒前检测过 未打卡用户，不重复检查', True)

        
        # 保存用户配置
        self.user_dict_obj.save()
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', '用户配置保存完毕', True)
        # 保存pk结果
        self.save_pk_result()
        # 写入作弊检测self.cheat_tracker结果到csv
        if len(self.cheat_tracker) > 0:
            with open(f'{self.log_dir}cheat-tracker_{self.cheat_tracker_date_str} .csv', 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['bcz_id', 'word_cnt', 'time','study_cheat'])
                for user_id, (word_count, time_, status) in self.cheat_tracker.items():
                    writer.writerow([user_id, word_count, time_, status])
        # 将公告检测结果存入notice_and_rank_path
        cnt = 0
        rest = 0
        for i, check_item in enumerate(self.check_list):
            if not check_item['valid']:
                continue
            if check_item['modified']:
                if check_item['group_id'] is None:
                    cursor.execute(f'''UPDATE notice SET CHECKED = ? WHERE GROUP_ID IS ? AND DATE == ?''', (check_item['checked']*100000000 + check_item['cursorA'] * 10000 + check_item['cursorB'], check_item['group_id'], check_item['date']))
                else:
                    cursor.execute(f'''UPDATE notice SET CHECKED = ? WHERE GROUP_ID == ? AND DATE == ?''', (check_item['checked']*100000000 + check_item['cursorA'] * 10000 + check_item['cursorB'], check_item['group_id'], check_item['date']))
                check_item['modified'] = False
                cnt += 1
            if check_item['checked'] < 2:
                rest += 1
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'notice保存完毕，本轮{cnt}条，剩余{rest}条', True)
        bad_words_display = "新增坏词：\n"
        if cnt > 0:
            bad_words = self.get_bad_words(has_mid=False)
            # 获取一下今天有没有新的坏词
            date_str = now.strftime('(%Y-%m-%d)')
            has_new_bad_word = False
            for bad_word in bad_words:
                if bad_word.startswith(date_str):
                    bad_words_display += f'{bad_word}\n'
                    has_new_bad_word = True
            # 将坏词存入json
            if has_new_bad_word:
                with open('tmp_bad_words.json', 'w', encoding='utf-8') as f:
                    json.dump(bad_words, f, ensure_ascii=False, indent=4)
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', bad_words_display, True)
        # 写入notice_buffer
        # 删除35天前的MEMBERS和notice数据
        date_int = int(now.strftime('%m%d'))
        thresh_date = datetime.datetime.combine((now - datetime.timedelta(days=35)), datetime.time.min)
        thresh_date_int = int(thresh_date.strftime('%m%d'))
        thresh_date_int_timestamp = int(thresh_date.timestamp())
        if date_int < thresh_date_int: # 跨年
            cursor.execute('''SELECT COUNT(*) FROM MEMBERS WHERE TODAY_DATE < ? AND TODAY_DATE > ? ''', (thresh_date_int, date_int))
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始删除去年{thresh_date_int}前的MEMBERS数据{cursor.fetchone()[0]}条', True)
            cursor.execute('''DELETE FROM MEMBERS WHERE TODAY_DATE < ? AND TODAY_DATE > ? ''', (thresh_date_int, date_int))
        else:
            cursor.execute('''SELECT COUNT(*) FROM MEMBERS WHERE TODAY_DATE < ?''', (thresh_date_int,))
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始删除{thresh_date_int}前的MEMBERS数据{cursor.fetchone()[0]}条', True)
            cursor.execute('''DELETE FROM MEMBERS WHERE TODAY_DATE < ?''', (thresh_date_int,))
        # 删除notice中DATE<thresh_date_int且(LATEST_DATE 是None或<thresh_date_int)的记录
        cursor.execute('''SELECT COUNT(*) FROM notice WHERE DATE < ? AND (LATEST_DATE IS NULL OR LATEST_DATE < ?)''', (thresh_date_int_timestamp, thresh_date_int_timestamp))
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始删除{thresh_date.strftime("%Y-%m-%d")}前的notice数据{cursor.fetchone()[0]}条', True)
        cursor.execute('''DELETE FROM notice WHERE DATE < ? AND (LATEST_DATE IS NULL OR LATEST_DATE < ?)''', (thresh_date_int_timestamp, thresh_date_int_timestamp))
        # 删除MEMBERS_GROUPS中ACHIEVED_DATE在7天前且STREAK_TIMES<7的记录
        thresh_date_int = int((now - datetime.timedelta(days=7)).strftime('%Y%m%d'))
        cursor.execute('''SELECT COUNT(*) FROM MEMBERS_GROUPS WHERE ACHIEVED_DATE < ? AND STREAK_TIMES < ?''', (thresh_date_int, 7))
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始删除{thresh_date_int}前且STREAK_TIMES<7的MEMBERS_GROUPS数据{cursor.fetchone()[0]}条', True)
        cursor.execute('''DELETE FROM MEMBERS_GROUPS WHERE ACHIEVED_DATE < ? AND STREAK_TIMES < ?''', (thresh_date_int, 7))
        # 写入notice
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入notice缓冲区{len(self.notice_buffer)}条', True)
        cursor.executemany('''INSERT OR REPLACE INTO notice (GROUP_ID, RANK_TYPE_RANK, CONTENT, DATE, LATEST_DATE, SCORE) VALUES (?, ?, ?, ?, ?, ?)''', self.notice_buffer)
        self.notice_buffer = []

        # 仅更新时间的公告
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始更新notice时间缓冲区{len(self.notice_time_buffer)}条', True)
        # cursor.executemany('''UPDATE notice SET LATEST_DATE = ?, RANK_TYPE_RANK = ? WHERE GROUP_ID = ? AND DATE = ?''', self.notice_time_buffer)
        cursor.executemany('''DELETE FROM notice WHERE GROUP_ID = ? AND DATE = ?''', self.notice_time_delete_buffer)
        self.logger.info('...')
        cursor.executemany('''INSERT OR REPLACE INTO notice (GROUP_ID, RANK_TYPE_RANK, CONTENT, DATE, LATEST_DATE, SCORE) VALUES (?, ?, ?, ?, ?, ?)''', self.notice_time_buffer)
        self.notice_time_buffer = []
        self.notice_time_delete_buffer = []

        # 被清空的公告
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入notice被清空缓冲区{len(self.notice_cleared_buffer)}条', True)
        # cursor.executemany('''UPDATE notice SET CHECKED=? WHERE GROUP_ID = ? AND DATE = ?''', self.notice_cleared_buffer)
        # cursor.executemany('''UPDATE notice SET CHECKED=? WHERE GROUP_ID = ? AND LATEST_DATE = ?''', self.notice_cleared_buffer)
        cursor.executemany('''DELETE FROM notice WHERE GROUP_ID = ? AND DATE = ?''', self.notice_cleared_delete_buffer)
        self.logger.info('...')
        cursor.executemany('''INSERT OR REPLACE INTO notice (GROUP_ID, RANK_TYPE_RANK, CONTENT, DATE, LATEST_DATE, SCORE, CHECKED) VALUES (?, ?, ?, ?, ?, ?, ?)''', self.notice_cleared_buffer)
        self.notice_cleared_buffer = [] # 已经在store_notice中处理
        self.notice_cleared_delete_buffer = []

        # 写入group_name
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入group_name缓冲区{len(self.group_info_buffer)}条', True)
        cursor.executemany('''INSERT OR REPLACE INTO GROUP_NAME (GROUP_ID, SHARE_KEY, MONITOR_ID, GROUP_NAME, GROUP_INTRODUCTION, GROUP_AVATAR) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(GROUP_ID) DO UPDATE SET SHARE_KEY = excluded.SHARE_KEY, MONITOR_ID = excluded.MONITOR_ID, GROUP_NAME = excluded.GROUP_NAME, GROUP_INTRODUCTION = excluded.GROUP_INTRODUCTION, GROUP_AVATAR = excluded.GROUP_AVATAR''', self.group_info_buffer)
        self.group_info_buffer = []

        # 写入user_name
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入user_name缓冲区{len(self.user_info_buffer)}条', True)
        cursor.executemany('''INSERT OR REPLACE INTO USER_NAME (USER_ID, NICKNAME, USER_AVATAR) VALUES (?, ?, ?) ON CONFLICT(USER_ID) DO UPDATE SET NICKNAME = excluded.NICKNAME, USER_AVATAR = excluded.USER_AVATAR''', self.user_info_buffer)
        self.user_info_buffer = [] # 每天最多700000条，暂无需设置大小

        # 写入member
        # 如果是星期日，则全部写入；否则只保留已打卡的成员
        copied_buffer = []
        if datetime.datetime.now().weekday() != 6:
            for value in self.member_buffer:
                if value[1] != 0:
                    copied_buffer.append(value)
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入member缓冲区，原有{len(self.member_buffer)}条，保留已打卡的成员{len(copied_buffer)}条', True)
            cursor.executemany('''INSERT OR REPLACE INTO MEMBERS (USER_ID, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, STUDY_CHEAT, BOOK_NAME) VALUES (?, ?, ?, ?, ?, ?)''', copied_buffer)
        else:
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入member缓冲区，原有{len(self.member_buffer)}条，周末全部写入', True)
            cursor.executemany('''INSERT OR REPLACE INTO MEMBERS (USER_ID, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, STUDY_CHEAT, BOOK_NAME) VALUES (?, ?, ?, ?, ?, ?)''', self.member_buffer)
        self.member_buffer = []

        # 写入book_name
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入book_name缓冲区{len(self.book_name_buffer)}条', True)
        cursor.executemany('''INSERT OR REPLACE INTO BOOK_NAME (HASH_ID, BOOK_NAME, BOOK_ID, BOOK_URL) VALUES (?, ?, ?, ?)''', self.book_name_buffer)
        self.book_name_buffer = []
        # 写入MEMBERS_GROUPS
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入MEMBERS_GROUPS缓冲区{len(self.member_groups_buffer)}条', True)
        cursor.executemany('''INSERT OR REPLACE INTO MEMBERS_GROUPS (USER_ID, GROUP_ID, STREAK_TIMES, COMPLETED_TIMES_START, START_DATE, ACHIEVED_DATE, DURATION_DAYS) VALUES (?, ?, ?, ?, ?, ?, ?)''', self.member_groups_buffer)
        self.member_groups_buffer = []
        # 写入MEMBERS_GROUPS合并后需要被删除的部分
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入MEMBERS_GROUPS合并后需要被删除的部分{len(self.member_groups_delete_buffer)}条', True)
        cursor.executemany('''DELETE FROM MEMBERS_GROUPS WHERE USER_ID = ? AND GROUP_ID = ? AND START_DATE = ?''', self.member_groups_delete_buffer)
        self.member_groups_delete_buffer = []
        # 写入GROUP_RANK
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'开始写入GROUP_RANK缓冲区{len(self.group_rank_buffer)}条', True)
        cursor.executemany('''INSERT OR REPLACE INTO GROUP_RANK (DATE, GROUP_ID, RANK_TYPE_RANK, DAKA_COUNT, TOTAL_DAKA_COUNT, FINISHING_RATE) VALUES (?, ?, ?, ?, ?, ?)''', self.group_rank_buffer)
        self.group_rank_buffer = []
        self.rank_and_daka_count_temp = {}# 用于储存排行榜上的班级的卡数和排名
        conn.commit()
        if close_start_time - self.latest_check_notice_timestamp > 3600:
            self.notice_parser.update_notice(conn, only_raw_notice=False)
            self.latest_check_notice_timestamp = close_start_time
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'notice_parser已更新', True)
        else: # 19
            self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'notice_parser 时间过短，不更新', True)
        conn.close()
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'数据库已保存', True)

        # 写入日志
        self.add_log(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '', '', f'共有{len(self.logs)}(-25)条日志，{len(self.warnings)}条警告如下：', False)
        if len(self.logs) > 25 or len(self.warnings) > 0:
            with open(f'{self.log_dir}log_{now.strftime("%Y-%m-%d %H-%M-%S")}.{max(self.latest_check_user_timestamp, self.latest_check_notice_timestamp)}.{len(self.logs)}.txt', 'w', encoding='utf-8') as f:
                for msg in self.logs:
                    f.write(msg)
                for msg in self.warnings:
                    f.write(msg)
            self.logs = []
            for warning in self.warnings:
                self.logger.warning(warning)
            self.warnings = []
        self.logger.info(f'全部保存操作已完成')
        self.last_remove_timestamp = 0
    
    def closing_count_down(self):
        '''为防止频繁关闭，增加关闭倒计时'''
        close_timestamp = self.last_remove_timestamp
        close_count_down_time = 120
        if DEBUG:
            close_count_down_time = 12
        while True:
            try:
                self.http2_client_obj.check_closing_state()
            except AssertionError: # 快速关闭
                return
            if close_timestamp != self.last_remove_timestamp or not self.is_empty():
                return
            if close_count_down_time <= 0:
                break
            self.logger.info(f'关闭倒计时: {close_count_down_time}s')
            time.sleep(6)
            close_count_down_time -= 6
        self.logger.info(f'关闭倒计时结束，准备关闭')
        self.close()


    def puzzle_solver(self, puzzle_dict): # 适用于BCZ_NCSVC
        if not BCZ_NCSVC:
            self.add_warning('BCZ_NCSVC未导入，无法使用puzzle_solver')
            return None
        id = int(puzzle_dict['id'])
        chn_mean = puzzle_dict['chnMean']
        if chn_mean is None:
            puzzle_dict['chnMean'] = ''
        option_list = puzzle_dict['options'].copy()
        answer = puzzle_dict['rightAnswer']
        question = puzzle_dict['question']
        topic_id = puzzle_dict['topicId']
        # 查找答案
        result = self.puzzles.get(id) # 得到的是答案的文本
        stored = False
        if result is not None:
            stored = True
            puzzle_dict['chnMean'] += 'Stored'
            # print(id ,result, option_list)
            if answer is None: # 还未作答
                for i, option in enumerate(option_list):
                    # print(i, option, result[0], answer)
                    for item in result:
                        if option == item:
                            answer = i + 1
                            break
                    if answer is not None:
                        break
                if answer is None:
                    # print(i, option, result[0], answer, puzzle_dict['chnMean'])
                    puzzle_dict['chnMean'] += '.Expired'
                    stored = False
                    self.add_warning(f'id={id} 题目过期...更新中')
        
        # print(stored, answer, puzzle_dict['chnMean'])
        if not stored and answer is not None:
            answer_text = option_list[answer - 1]
            self.puzzle_buffer.append((id, question, chn_mean, answer_text, option_list[0], option_list[1], option_list[2], topic_id))
            puzzle_dict['chnMean'] += 'Learnt'
        if answer is None:
            answer = random.randint(0, 4)
            if answer == 0:
                answer = 1 # 干扰概率
        return answer

    def load_dict_db(self, logger):
        # 读取puzzle_path数据库
        if BCZ_NCSVC:
            puzzle_conn = sqlite3.connect(self.puzzle_path)
            cursor = puzzle_conn.cursor()
            cursor.execute('''SELECT QUESTION, ANSWER FROM BCZ_NCSVC''')
            self.puzzles = {}
            for row in cursor.fetchall():
                if self.puzzles.get(row[0]) is None:
                    self.puzzles[row[0]] = [row[1],]
                else:
                    self.puzzles[row[0]].append(row[1])
            puzzle_conn.close()
            logger.info(f'加载puzzle_path数据库{len(self.puzzles)}条')
            self.puzzle_buffer = []
        # 遍历DICT_DB_PATH中的所有表
        dict_db_conn = sqlite3.connect(DICT_DB_PATH)
        cursor = dict_db_conn.cursor()
        cursor.execute('''SELECT name FROM sqlite_master WHERE type='table' ''')
        tables = cursor.fetchall()
        self.variants = {}
        for table in tables:
            if table[0].startswith('variant'):
                results = cursor.execute(f'''SELECT variant, origin FROM {table[0]}''')
                for result in results:
                    self.variants[result[0]] = result[1]
        self.words = {}
        logger.info(f'加载词族{len(self.variants)}条')
        cursor.execute('''SELECT topic_id, word, mean_cn FROM dict_bcz''')
        for result in cursor.fetchall():
            self.words[result[0]] = result[2]
            self.words[result[1]] = result[2]
        logger.info(f'加载单词词释义{len(self.words)}条')
        dict_db_conn.close()
        # 加载dict_patch_db_path数据库
        dict_patch_db_conn = sqlite3.connect(self.dict_patch_db_path)
        cursor = dict_patch_db_conn.cursor()
        cursor.execute('''SELECT TOPIC_ID, WORD, ANSWER, RANK FROM dict_bcz''')
        self.words_patch = {}
        self.word_occur_ranks = {}
        for result in cursor.fetchall():
            if self.words_patch.get(result[0]) is None:
                self.words_patch[result[0]] = [result[2],]
            else:
                self.words_patch[result[0]].append(result[2])
            if self.words_patch.get(result[1]) is None:
                self.words_patch[result[1]] = [result[2],]
            else:
                self.words_patch[result[1]].append(result[2])
            self.word_occur_ranks[result[1]] = result[3]
        self.patch_buffer = [] # 包括释义不完整和排名信息不完整的单词
        logger.info(f'加载patch数据库{len(self.word_occur_ranks)}条')

    def word_lookup(self, word, topic_id=None):
        # 先尝试查找原型
        result = self.words_patch.get(word)
        if result is not None:
            # 可能有多个，用，连接
            return '@' + '，'.join([i for i in result])
        result = self.words.get(word)
        if result is not None: # 这个不会有多个，直接返回
            return f'@@{result}'
        
        # 尝试查找topic_id
        if topic_id is not None:
            result = self.words_patch.get(topic_id)
            if result is not None:
                return '#' + '，'.join([i for i in result])
            result = self.words.get(topic_id)
            if result is not None:
                return f'##{result}'
        
        # 再尝试查找词根
        variant = self.variants.get(word)
        if variant == word:
            return None
        result = self.words.get(variant)
        if result is not None:
            return '*' + result
        return None

    replace_dict = {
        '（':'',
        '）':'',
        '  ': ' ',
        '…': '',
        '/': '',
        ', ': '，', # 统一成中文逗号
        '…': '',
        '.': '',
        '；':'，'
    }
    def standardize(chn_mean):
        if chn_mean is None:
            return None
        # 将大写字母转换为小写字母
        # chn_mean = chn_mean.lower()
        for key, value in daka_list_class.replace_dict.items():
            chn_mean = chn_mean.replace(key, value)
        return chn_mean

    def word_lookup_puzzle_solver(self, puzzle_dict):
        word = daka_list_class.standardize(puzzle_dict['title'])
        topic_id = puzzle_dict['topicId']
        msg = word
        chn_mean = daka_list_class.standardize(self.word_lookup(word, topic_id))
        if chn_mean is None:
            chn_mean = ''
            self.add_warning(f'word_lookup_puzzle_solver: word not found: {word}')
            msg += '<font color="red">未找到</font>'
        options = puzzle_dict['options']
        options_text = [daka_list_class.standardize(option['text']) for option in options] # 统一成中文逗号
        result = None
        for text in options_text:
            if text == chn_mean:
                result = (text, 100)
                msg += '&ltEXACT&gt'
                break
            elif text in chn_mean and (result is None or len(text) > len(result[0])):
                result = (text, 95)
                msg += '&ltIN&gt'
        if result is None:
            result = process.extractOne(chn_mean, options_text)
            msg += '&ltFUZZ&gt'
        msg += f'{options_text}match={result}<br>释义：{chn_mean}'
        if result is None:
            return random.randint(0, 3)
        index = options[options_text.index(result[0])]['id']
        return index, msg

    def word_lookup_patcher(self, puzzle_dict, answer_id, topic_id, rank, rival_score):
        word = puzzle_dict['title']
        for option in puzzle_dict['options']:
            if option['id'] == answer_id:
                answer = option['text']
                break
        else:
            self.add_warning(f'PATCHER: answer_id={answer_id} not found in options{puzzle_dict}')
            return
        result = self.word_occur_ranks.get(word)
        # 检查是否已经存在
        if result is None:
            self.word_occur_ranks[word] = rank
            self.patch_buffer.append((answer, word, topic_id, rank))
        else:
            recorded_rank = result.split(',')
            if rank not in recorded_rank:
                recorded_rank.append(rank)
                new_str = ','.join(recorded_rank)
                self.word_occur_ranks[word] = new_str
                self.patch_buffer.append((answer, word, topic_id, new_str))

    def count_group(self):
        return Counter([len(groups) for groups in self.member_groups_cnt.values()])

    def get_uv(self):
        '''获取总用户uv，储存到self.uv_index'''
        user_cookie = self.user_dict_obj.get_cookie()
        user_config = self.user_dict_obj.get_config()
        # https://group.baicizhan.com/group/study_words_together_home_page
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        response = self.http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/study_words_together_home_page', headers, None)
        data = response.json()['data']
        self.uv_index = data['uv']
        self.logger.info(f'\033[36;1m获取uv成功，当前uv={self.uv_index}\033[0m')
        
    def save_other_info(self, cursor: sqlite3.Cursor):
        '''保存其他信息，包括uv_index，小班数量比例和最大group_id'''
        if len(self.member_buffer) == 0:
            return
        group_counter = self.count_group()
        total_count = sum(group_counter.values())
        # 记录每种小班数量的比例
        group_ratio = [round(count/total_count*100, 2) for count in group_counter.values()]
        self.logger.info(f'小班数量百分比：{group_ratio}')
        self.get_uv()
        today_date_int = int(datetime.datetime.now().strftime('%Y%m%d'))
        cursor.execute('''INSERT OR REPLACE INTO OTHER_INFO (UV_INDEX, MAX_GROUP_ID, GROUP_COUNT_1, GROUP_COUNT_2, GROUP_COUNT_3, GROUP_COUNT_4, GROUP_COUNT_5, GROUP_COUNT_6, TODAY_DATE) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (self.uv_index, self.max_group_id, group_counter[1], group_counter[2], group_counter[3], group_counter[4], group_counter[5], group_counter[6], today_date_int))
    
    def load_cheat_tracker(self, cheat_tracker_date_str: str):
        self.cheat_tracker = {}
        self.cheat_tracker_date_str = cheat_tracker_date_str
        if os.path.exists(f'{self.log_dir}cheat-tracker_{cheat_tracker_date_str} .csv'):
            with open(f'{self.log_dir}cheat-tracker_{cheat_tracker_date_str} .csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader) # 跳过标题
                for row in reader:
                    self.cheat_tracker[int(row[0])] = (int(row[1]), int(row[2]), int(row[3]))
        self.logger.info(f'cheat_tracker共加载{len(self.cheat_tracker)}个用户')

    def store_group_rank(self, date, group_id, daka_count, finishing_rate):
        '''self.wait() before calling this function''' # 在notice_and_rank函数中已经调用了
        with self.lock:
            item = self.rank_and_daka_count_temp.get(group_id, (None, None))
            rank_type_rank, total_daka_count = item
            self.group_rank_buffer.append((date, group_id, rank_type_rank, daka_count, total_daka_count, finishing_rate))
        
    def store_group_info(self, group_id, share_key, monitor_id, class_name, introduction, group_avatar):
        '''self.wait() before calling this function''' # 在notice_and_rank函数中已经调用了
        if monitor_id == '':
            monitor_id = None
        with self.lock:
            self.max_group_id = max(self.max_group_id, group_id)
            current_data = self.group_infos.get(group_id, (None, None, None, None, None, None))
            if current_data[3] == class_name and current_data[4] == introduction and current_data[5] == group_avatar:
                return
            new_tp = (group_id, share_key, monitor_id, class_name, introduction, group_avatar)
            self.group_infos[group_id] = new_tp
            self.group_info_buffer.append(new_tp)

    def store_notice(self, group_id, rank_type_rank, content, data_time, score, week_daka_days) -> int: # 0被清空，1新增，2已存在
        '''self.wait() before calling this function''' # 在notice_and_rank函数中已经调用了
        with self.lock:
            if group_id not in self.notice_list:
                self.notice_list[group_id] = {}
            if week_daka_days is None: # 防止二次获取时错误数据覆盖有效数据
                week_daka_days = self.rank_and_daka_count_temp.get(group_id, (None, None))[1]
            self.rank_and_daka_count_temp[group_id] = (rank_type_rank, week_daka_days)
            
            if content == '(空)': # 只有第一次看到空公告才需要加入notice_cleared_buffer
                # 从notice_list中找到该班级最近的不为空的公告，加入notice_cleared_buffer
                max_date = 0
                max_date_latest = 0
                max_key = ''
                for key, value in self.notice_list[group_id].items():
                    if value[1] and value[1] > max_date or value[0] > max_date:
                        max_date = value[0]
                        max_date_latest = value[1]
                        max_key = key
                        
                if max_key == '(空)':
                    self.notice_time_buffer.append((group_id, rank_type_rank, content, max_date, data_time, score)) # 记录时间
                    self.notice_time_delete_buffer.append((group_id, max_date))
                    return -1 # 如果最近的就是空，则不加入
                self.notice_list[group_id][content] = (data_time, None)
                self.notice_buffer.append((group_id, rank_type_rank, content, data_time, None, score))
                if max_date > 0: 
                    self.notice_cleared_buffer.append((group_id, rank_type_rank, max_key, max_date, max_date_latest, score, 0))
                    self.notice_cleared_delete_buffer.append((group_id, max_date))
                    return 0
                return -2 # 没有最近的不为空的公告
                
            if content not in self.notice_list[group_id]: # 新增公告
                self.notice_list[group_id][content] = (data_time, None)
                self.notice_buffer.append((group_id, rank_type_rank, content, data_time, None, score))
                return 1
            else: # 已存在，更新时间
                old_date = self.notice_list[group_id][content][0]
                self.notice_time_buffer.append((group_id, rank_type_rank, content, old_date, data_time, score)) # 仅更新时间
                self.notice_time_delete_buffer.append((group_id, old_date))
                self.notice_list[group_id][content] = (old_date, data_time)
                return 2
    
    
    
    def store_member(self, user_id, group_id, completed_time, today_date, today_date_mmdd, today_date_datetime: datetime.datetime, word_count, study_cheat, completed_times, duration_days, book_name, nickname, user_avatar):
        '''self.wait() before calling this function''' # 在notice_and_rank函数中已经调用了
        with self.lock:
            def store_user_info(user_id, nickname, user_avatar):
                # user_avatar = None
                current_data = self.user_infos.get(user_id, (None,None,None))
                if current_data[1] == nickname and current_data[2] == user_avatar:
                    return
                new_tp = (user_id, nickname, user_avatar)
                self.user_infos[user_id] = new_tp
                self.user_infos_from_avatar[user_avatar] = user_id
                self.user_info_buffer.append(new_tp)
            # 先存储用户信息
            store_user_info(user_id, nickname, user_avatar)
            # 先将书本名对应到id
            book_id = self.book_name_dict.get(book_name)
            if book_id is None:
                book_id = len(self.book_name_dict) + 1
                self.book_name_dict[book_name] = book_id
                self.book_name_buffer.append((book_id, book_name, None, None))
            # 先检查是否有重复记录
            tp = self.member_list.get(user_id)
            if tp is None:
                tp_new = (user_id, completed_time, today_date_mmdd, word_count, study_cheat, book_id)
                self.member_list[user_id] = tp_new
                self.member_buffer.append(tp_new)
                self.member_groups_cnt[user_id] = {group_id: 1}
            else:
                if today_date_mmdd != tp[2] or self.member_groups_cnt.get(user_id) is None:
                    self.member_groups_cnt[user_id] = {}
                self.member_groups_cnt[user_id][group_id] = 1
                if completed_time != tp[1] or today_date_mmdd != tp[2] or word_count != tp[3] or study_cheat != tp[4] or book_id != tp[5]:
                    tp_new = (user_id, completed_time, today_date_mmdd, word_count, study_cheat, book_id)
                    self.member_list[user_id] = tp_new
                    self.member_buffer.append(tp_new)

            idx = (user_id, group_id)
            tp = self.member_groups.get(idx)
            if tp is None:
                if completed_time == 0: # 默认当天打卡，为了防止不打卡用户产生碎片数据，只有打了卡才能开始第一天连胜
                    return
                if completed_times == duration_days:
                    calc_start_date = int((today_date_datetime - datetime.timedelta(days=completed_times - 1)).strftime('%Y%m%d')) # 之前的都算连胜
                    self.member_groups[idx] = (completed_times, 1, calc_start_date, today_date, duration_days)
                    self.member_groups_buffer.append((user_id, group_id, completed_times, 1, calc_start_date, today_date, duration_days))
                else:
                    self.member_groups[idx] = (1, completed_times, today_date, today_date, duration_days)  # 从今天开始算第一天连胜
                    self.member_groups_buffer.append((user_id, group_id, 1, completed_times, today_date, today_date, duration_days))
                return
            streak_times, completed_times_start, start_date, achieved_date, duration_days_old = tp
            delta = (today_date_datetime - datetime.datetime.strptime(str(achieved_date), '%Y%m%d')).days - 1 - (completed_times - streak_times - completed_times_start)
            if delta < 0: # 打卡次数多过天数，可能是单词机（或者后门）
                # 检查本次延长后是否和上次连接。极端情况下，会有多次记录需要合并，每次合并一段，多几次就好了
                prev_tp = self.prev_user_streak_info.get(idx)
                if prev_tp is not None:
                    prev_streak_times, prev_completed_times_start, prev_start_date, prev_achieved_date, prev_duration_days = prev_tp
                    prev_delta = (today_date_datetime - datetime.datetime.strptime(str(prev_achieved_date), '%Y%m%d')).days - 1 - (completed_times - streak_times - completed_times_start)
                    if prev_delta <= 0:
                        streak_times = prev_streak_times + (-prev_delta) # 补上上次的连胜部分，后面还要再加上本次的连胜部分
                        completed_times_start = prev_completed_times_start
                        self.member_groups_delete_buffer.append((user_id, group_id, start_date)) # 是删掉这一次的中断记录，合并如上一次的完整记录
                        start_date = prev_start_date
                        achieved_date = prev_achieved_date
                        duration_days = prev_duration_days
                        self.prev_user_streak_info.pop((user_id, group_id))
                # 延长连胜
                delta = 0
                streak_times += -delta # 补上比天数多的连胜部分，后面还要再加上天数连胜

            if delta == 0:
                streak_times += (today_date_datetime - datetime.datetime.strptime(str(achieved_date), '%Y%m%d')).days # 连续天数增加
                self.member_groups[idx] = (streak_times, completed_times_start, start_date, today_date, duration_days)
                self.member_groups_buffer.append((user_id, group_id, streak_times, completed_times_start, start_date, today_date, duration_days))
            else: # 增加新纪录
                if completed_time == 0: # 默认当天打卡，为了防止不打卡用户产生碎片数据，只有打了卡才能开始第一天连胜
                    return
                if completed_times == duration_days:
                    calc_start_date = int((today_date_datetime - datetime.timedelta(days=completed_times-1)).strftime('%Y%m%d')) # 有可能记录有缺失，所以不一定是今天退出重进的，要严格用倒推法
                    if calc_start_date != start_date: # 如果相等，则说明当天退出重进，只保留新的记录，不更新prev_user_streak_info（数据库同START_DATE会被REPLACE掉，无需处理）
                        self.prev_user_streak_info[(user_id, group_id)] = (streak_times, completed_times_start, start_date, achieved_date, duration_days_old)
                    self.member_groups[(user_id, group_id)] = (completed_times, 1, calc_start_date, today_date, duration_days)
                    self.member_groups_buffer.append((user_id, group_id, completed_times, 1, calc_start_date, today_date, duration_days))
                else:
                    if today_date != start_date:
                        self.prev_user_streak_info[(user_id, group_id)] = (streak_times, completed_times_start, start_date, achieved_date, duration_days_old)
                    self.member_groups[(user_id, group_id)] = (1, completed_times, today_date, today_date, duration_days)
                    self.member_groups_buffer.append((user_id, group_id, 1, completed_times, today_date, today_date, duration_days))

                    
    # 打卡状态检查链接：https://group.baicizhan.com/group/study_words_together_home_page
    def check_if_daka(self, user_cookie):
        headers = getHeaders('$group', user_cookie, int(time.time()), index = 1)
        url = 'https://group.baicizhan.com/group/study_words_together_home_page'
        response = self.http2_client_obj.send_http2_request('GET', url, headers=headers, content=None)
        response_json = response.json()
        return response_json['data']['todayDaka']
    
    def check_not_daka_users(self, include_not_daka: bool):
        daka_check = {}
        checked_cnt = 0
        users = self.user_dict_obj.get_user_dict_list()
        total_cnt = len(users)

        not_daka_users = []
        def delayed_check_if_daka(user_dict, total_user_cnt, index):
            time.sleep(random.randint(0, total_user_cnt * 5) / 10)
            daka_check[index] = self.check_if_daka(user_dict['cookie'])
            if not daka_check[index]:
                not_daka_users.append(user_dict)

        for i, user in enumerate(users):
            if not include_not_daka and user['config']['can_daka'] == 0:
                total_cnt -= 1
                continue
            # 多线程检测
            t = threading.Thread(target=delayed_check_if_daka, args=(user, total_cnt, i))
            t.start()
        # 等待所有线程结束
        while len(daka_check) < total_cnt:
            self.logger.info(f'检测中，已完成{len(daka_check)}个用户')
            time.sleep(1)
        self.logger.info(f'检测完毕，共{len(not_daka_users)}个用户未打卡')
        if not include_not_daka:
            self.logger.info(f'不包括 仅托管用户')
        else:
            self.logger.info(f'包括 仅托管用户')
        for user in not_daka_users:
            self.logger.info(f'{user["config"]["name"]}({user["config"]["unique_id"]})未打卡')
        return not_daka_users

    def add_warning(self, content):
        time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        self.warnings.append(f'[Warning][{time_str}] {content}\n')
        self.logger.warn(content)

    def add_log(self, date_str, name, unique_id, msg, display=False):
        result = f'[{date_str}] {name}({unique_id}) {msg}'
        if display:
            self.logger.info(result)
        self.logs.append(result+'\n')

    def track_cheat_user(self, date_str, user_id, user_word_cnt, time, status): # 0未刷词，1刷词
        if date_str != self.cheat_tracker_date_str:
            self.load_cheat_tracker(date_str)
        if user_id in self.cheat_tracker:
            if self.cheat_tracker[user_id][2] == 0 and status == 1: # 爆破成功
                print(f'{user_id}\033[31m刷词爆破成功\033[0m')
                self.cheat_tracker[user_id] = (user_word_cnt, time, 3)
                return
        with self.lock:
            self.cheat_tracker[user_id] = (user_word_cnt, time, status)
    
    def user_tracked(self, user_id):
        return user_id in self.cheat_tracker
        
    def get_notice_and_rank_conn(self):
        return sqlite3.connect(self.notice_and_rank_path)
    
    def get_user_cnt(self):
        return self.user_dict_obj.get_count()
    
    def has_user(self, unique_id):
        return False if self.user_dict_obj.get_index_by_unique_id(unique_id) is None else True
    
    def get_access_token(self, unique_id):
        return self.user_dict_obj.get_access_token_by_unique_id(unique_id)

    def get_user_dict(self, unique_id=0):
        index = self.user_dict_obj.get_index_by_unique_id(unique_id)
        if index is None:
            return None
        return {'cookie': self.user_dict_obj.get_cookie(index), 'config': self.user_dict_obj.get_config(index)}

    def get_user_dict_list(self):
        return self.user_dict_obj.get_user_dict_list()
    
    def update_user_dict(self, user_dict):
        self.user_dict_obj.update_user_dict(user_dict)
    
    def reload_user_dict(self):
        del self.user_dict_obj
        self.user_dict_obj = user_dict()

    def get_user_name_and_avatar(self, unique_id):
        try:
            self.wait()
            user = self.user_infos.get(int(unique_id))
            return {"nickname": user[1], "avatar": user[2]}
        except:
            return {"nickname": "未收录", "avatar": ""}
        
    def get_group_avatar(self, group_id):
        try:
            self.wait()
            return self.group_infos.get(group_id)[5]
        except:
            return None
    
    def get_group_info(self, group_id):
        '''返回(名称，介绍)'''
        try:
            self.wait()
            group = self.group_infos.get(group_id)
            return {"name": group[3], "introduction": group[4], "avatar": group[5]}
        except:
            return {"name": "", "introduction": "未收录", "avatar": None}
        
    def get_class_list(self, rank, user_cookie): # 此函数无需等待初始化完成
        if rank == 2048:
            self.wait()
            return self.class_list_2048_sharekey
        class_list = []
        current_data_time = datetime.datetime.now().strftime('%Y-%m-%d')
        if rank not in self.class_list or current_data_time != self.class_list[rank]['data_time']:
            with self.lock:
                headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
                if rank == 0:
                    # https://group.baicizhan.com/group/recommended_groups
                    response = self.http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/recommended_groups', headers, None)
                elif rank >= 1 and rank <= 7:
                    response = self.http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/get_group_rank?rank={rank}', headers, None)
                else:
                    return []
                class_list = response.json()['data']['list']
                self.class_list[rank] = {'data_time': current_data_time, 'class_list': class_list}
                return class_list
        class_list = self.class_list[rank]['class_list']
        return class_list

    def add(self, unique_id, daka_type):
        self.lock.acquire()
        if len(self.daka_list) == 0:
            self.logger.info('daka_list time start!')
            self.time_start = int(time.time())
            if self.last_remove_timestamp == -1:
                self.lock.release()
                while True:
                    time.sleep(10)
                    if self.last_remove_timestamp != -1:
                        break
                self.lock.acquire()
            self.last_remove_timestamp = 1 # 开始如果0/timestamp置1，如果-1则等待
        if self.daka_list.get(unique_id) is None:
            self.daka_list[unique_id] = daka_type
            self.lock.release()
            return True
        elif self.daka_list[unique_id] == daka_type:
            self.lock.release()
            return False
        self.lock.release()
        while True:
            time.sleep(10)
            if self.daka_list.get(unique_id) is None:
                with self.lock:
                    if self.daka_list.get(unique_id) is None:
                        self.daka_list[unique_id] = daka_type
                        return True
                    else:
                        continue

    def remove(self,unique_id):
        self.lock.acquire()
        if unique_id in self.daka_list:
            del self.daka_list[unique_id]
        if self.is_empty():
            # 结束如果0/1置timestamp，如果-1，等待
            if self.last_remove_timestamp == -1:
                self.lock.release()
                while True:
                    time.sleep(10)
                    if self.last_remove_timestamp != -1:
                        break
                self.lock.acquire()
            self.logger.info('daka_list is empty!')
            self.last_remove_timestamp = time.time()
            threading.Thread(target=self.closing_count_down).start()
        self.lock.release()

    def query(self, unique_id):
        return self.daka_list.get(unique_id)
    
    def get_not_running_arbiter(self, cnt, except_ids: set, include_subscriber=False):
        '''返回cnt个未在运行的arbiter，如果不足，则返回剩余的'''
        return self.user_dict_obj.get_except_from_arbiter(set(self.daka_list.keys()), cnt, except_ids, self.daka_pk_status, include_subscriber=include_subscriber)
    
    def get_bad_words(self, has_mid=True): # 获取检查结果
        # 拼接状态为1的notice
        result = self.bad_words.copy()
        if has_mid:
            not_checked_str = ''
            with self.lock:
                for item in self.check_list:
                    if item['checked'] == 1 and item['valid']:
                        not_checked_str += f'{item["content"][-15:]}<br>'
            result.append(not_checked_str)
        return result

    def clear_bad_words(self): # 清除检查结果
        self.bad_words = []

    def check_notice(self, content):
        return self.notice_parser.check_notice(content)
    
    def get_check_notice(self):
        self.wait()
        with self.lock:
            for item in self.check_list:
                if item['checked'] < 2 and item['valid']:
                    item['valid'] = False
                    return item.copy()
            return None
        
    def patch_check_notice(self, item, modified=True):
        self.wait()
        date_str = datetime.datetime.now().strftime('(%Y-%m-%d)')
        with self.lock:
            item['valid'] = True
            item['modified'] = modified
            if item['checked'] == 2 and item['cursorB'] > 0:
                self.bad_words.append(date_str + item['content'])
            self.check_list.insert(0, item)
    
    def is_empty(self):
        return len(self.daka_list) == 0

    def is_closing(self):
        return self.last_remove_timestamp != 0

class stargazer_class:
    def __init__(self, logger, http2_client_obj: http2_client, config: Config, daka_list_obj: daka_list_class, messages: queue.Queue, king: bool):
        # king参数：仅将arbiter和subscribed users上段，然后退出
        self.king = king
        self.http2_client_obj = http2_client_obj
        self.messages = messages
        self.logger = logger
        self.stargazer_list = [] if self.king else config.pk_blacklist
        self.stargazer_set = set(self.stargazer_list)
        self.stargazer_cnt = len(self.stargazer_list)
        self.stargazer_db = config.stargazer_db
        self.arbiter_offset_win = config.arbiter_offset_win
        self.arbiter_offset_lose = config.arbiter_offset_lose
        self.arbiter_interval = config.arbiter_interval
        self.arbiter_size = config.arbiter_size
        self.arbiter_index = 10**(self.arbiter_size-1)
        self.stargazers = {}
        self.success_timestamp = set()
        self.daka_list_obj = daka_list_obj
        self.session_id = None
        self.buffer = []  # (TIMESTAMP, STAR, RANK, ACTION)
        self.action_buffer = {} # (TIMESTAMP, USER_ID):ACTION
        self.token_user_dict_list = []

    def init_db(self):
        conn = sqlite3.connect(self.stargazer_db)
        cursor = conn.cursor()
        for unique_id in self.stargazer_list:
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS star_{unique_id} (
                TIMESTAMP INTEGER,
                STAR INTEGER,
                RANK INTEGER,
                ACTION INTEGER) -- -1TRACKING，1MISS，2CAUGHT，3NO_ENERGY，4SKIPPED，9NO_ACCOUNT，-2WIN，-3DRAW，-4LOSS
            ''')
        conn.commit()
        # 读取数据
        # for unique_id in self.stargazer_list:
        #     result = cursor.execute(f'''SELECT STAR FROM star_{unique_id} ORDER BY TIMESTAMP DESC LIMIT 1''').fetchone()
        #     if result:
        #         self.stargazers[unique_id] = {"stars": result[0], "rank": None}# 未上榜不追踪
        #     else:
        #         self.stargazers[unique_id] = {"stars": 0, "rank": None}
        conn.close()

    def get_session_id(self):
        if self.session_id:
            return self.session_id
        time_long = int(time.time() * 1000)
        time_short = int(time.time())
        pk_get_headers = getHeaders("$pk", self.token_user_dict_list[0]['cookie'], time_short, index=1, quote=True)
        # http2://pk.baicizhan.com/api/rankpk/v2/current_session?time=
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/v2/current_session?time={time_long}'
        response = self.http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        if time_long > data['session']['endTime']:
            self.logger.warning(f'当前PK赛季已结束')
        self.session_id = data["session"]["sessionId"]
        return self.session_id

    def refresh_token(self):
        '''获取ARBITER_SIZE个未在运行的arbiter token'''
        new_token_user_dict_list = []
        new_ids = set()
        for i in range(self.arbiter_size):
            try:
                my_unique_id = self.token_user_dict_list[i]['config']['unique_id']
                if not self.daka_list_obj.query_is_king(my_unique_id):
                    threading.Thread(target=self.prepare_arbiter_wrapper, args=(self.token_user_dict_list[i],)).start()
                    self.logger.info(f'为arbiter上段 {my_unique_id}')
                    time.sleep(0.5)
                    continue
                if self.daka_list_obj.query(my_unique_id) is None:
                    if self.daka_list_obj.query_pk_status(my_unique_id) != 2: # 2=能量耗尽
                        new_token_user_dict_list.append(self.token_user_dict_list[i])
                    new_ids.add(my_unique_id)
            except IndexError:
                pass
        if len(new_token_user_dict_list) < self.arbiter_size:
            demand = self.arbiter_size - len(new_token_user_dict_list)
            new_arbiters = self.daka_list_obj.get_not_running_arbiter(demand, new_ids, include_subscriber = self.king)
            if new_arbiters == []:
                if new_token_user_dict_list != []:
                    self.token_user_dict_list = new_token_user_dict_list
                    return # 有但是不足ARBITER_SIZE个，照样发射
                while new_arbiters == []: # 真的一个都没有，至少要一个
                    if self.king:
                        return []
                    self.logger.info(f'没有可用的arbiter，等待1.5秒后重试')
                    time.sleep(1.5)
                    new_arbiters = self.daka_list_obj.get_not_running_arbiter(demand, new_ids)
            new_token_user_dict_list.extend(new_arbiters)
            self.token_user_dict_list = new_token_user_dict_list
            self.refresh_token() # 检查新获取的token是否可用，否则要重新获取


    def refresh_stars(self, refresher_dict) -> list:
        '''刷新星星数，返回+2的用户列表（在stargazer_list中的）'''
        time_long = int(time.time() * 1000)
        time_short = int(time.time())
        user_cookie = refresher_dict['cookie']
        pk_get_headers = getHeaders("$pk", user_cookie, time_short, index=1, quote=True)
        session_id = self.get_session_id()
        # https://pk.baicizhan.com/api/rankpk/session_ranking_list?time=&session_id=&offset=0
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/session_ranking_list?time={time_long}&session_id={session_id}&offset=0'
        response = self.http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        modified_users = []
        current_timestamp = int(time.time())
        for item in data['rank_users']:
            bcz_id = item['bczId']
            # print('\033[32m' + f'[{bcz_id}]' + '\033[0m' + f' {item["rank"]} {item["stars"]} {item["nickname"]}')
            if bcz_id in self.stargazer_set:
                stars = item['stars']
                prev_stars = self.stargazers.get(bcz_id, {}).get('stars', 0)
                if prev_stars == stars:
                    continue
                if bcz_id not in self.stargazers:
                    self.stargazers[bcz_id] = {} # 未上榜不追踪
                self.stargazers[bcz_id]['active'] = current_timestamp # 首次出现在排行榜，视为一次活跃
                self.stargazers[bcz_id]['stars'] = stars
                self.stargazers[bcz_id]['rank'] = item['rank']
                if prev_stars + 2 == stars:
                    modified_users.append(bcz_id) # 此处不save到数据库，交给后面的处理器
                else:
                    self.save_to_db(current_timestamp, bcz_id, -1)
        self.logger.info(f'刷新星星数成功：{self.stargazers}')
        return modified_users
    
    def save_to_db(self, timestamp, target_id, action):
        if action > 0: # 累计ARBITER_SIZE位后一次性写入
            id = (timestamp, target_id)
            if id not in self.action_buffer:
                self.action_buffer[id] = action
            else:
                self.action_buffer[id] = self.action_buffer[id] * 10 + action
            if self.action_buffer[id] < self.arbiter_index:
                return
            action = self.action_buffer[id] # 累计达到ARBITER_SIZE位后，写入数据库
            del self.action_buffer[id]
        self.buffer.append((timestamp, self.stargazers[target_id]['stars'], self.stargazers[target_id]['rank'], action))
        if len(self.buffer) >= 1:
            conn = sqlite3.connect(self.stargazer_db)
            cursor = conn.cursor()
            for item in self.buffer:
                cursor.execute(f'''INSERT INTO star_{target_id} (TIMESTAMP, STAR, RANK, ACTION) VALUES (?,?,?,?)''', item)
            conn.commit()
            self.buffer = []
            conn.close()
    
    def arbiter_wrapper(self, token_user_dict, target_id, start_time):
        '''反挂的包装器'''
        result_str = ''
        user_cookie = token_user_dict['cookie']
        user_config = token_user_dict['config']
        unique_id = token_user_dict['config']['unique_id']
        try:
            if not self.daka_list_obj.add(unique_id, -100):
                return
            # time.sleep(random.randint(10, 100) / 10) # 随机延时
            rival_id = 0
            for msg in pkonline2(user_cookie, user_config, self.http2_client_obj, self.daka_list_obj, max_round=1, max_win_round=6666, allow_self=True):
                result_str += msg
                if len(result_str) > 2048:
                    # 只保留最后2048个字符
                    result_str = result_str[-2048:]
                self.messages.put(('msg', unique_id, result_str))
                if msg.startswith('<font color="'):
                    flag = msg[13:].split('"')[0]
                    if flag == 'lemonchiffon':
                        try:
                            rival_id = int(msg[27:-11]) # 有可能是“未找到”
                        except:
                            rival_id = -1
                        if rival_id == -2:
                            self.logger.info(f'体力不足')
                            self.save_to_db(start_time, target_id, 3)
                        elif rival_id == target_id:
                            self.logger.info(f'匹配到目标rival_id:{rival_id}')
                            self.success_timestamp.add(start_time)
                            self.save_to_db(start_time, target_id, 2)
                        else:
                            self.logger.info(f'rival_id:{rival_id}不是目标rival_id:{target_id}') # MISS
                            self.save_to_db(start_time, target_id, 1)
                        continue
                    if rival_id != target_id:
                        continue # 不是目标rival_id，不记录结果
                    self.refresh_stars(token_user_dict)
                    if flag == 'green':
                        self.save_to_db(int(time.time()), target_id, -2)
                        time.sleep(self.arbiter_offset_lose) # 对方输了
                    elif flag == 'red':
                        self.save_to_db(int(time.time()), target_id, -4)
                        continue # 输了，由主线程start_arbiter
                    elif flag == 'yellow':
                        self.save_to_db(int(time.time()), target_id, -3)
                        time.sleep(self.arbiter_offset_lose) # 等同于对方输了

                    self.start_arbiter(rival_id, int(time.time()))
                    
        except AssertionError: # 快速关闭
            pass
        except Exception as e:
            self.daka_list_obj.add_warning(f'反挂器出错：{traceback.format_exc()}')
            self.messages.put(('error', unique_id, traceback.format_exc()))
        finally:
            result_str = result_str.replace('<br>', '\n')
            self.daka_list_obj.add_log(datetime.datetime.now().strftime('%Y-%m-%d'), user_config['name'], user_config['unique_id'], result_str)
            self.daka_list_obj.remove(unique_id)


    def prepare_arbiter_wrapper(self, token_user_dict):
        '''PK赛事反挂上段的包装器'''
        result_str = ''
        old_result_str = ''
        unique_id = token_user_dict['config']['unique_id']
        user_cookie = token_user_dict['cookie']
        user_config = token_user_dict['config']
        name = user_config['name']
        acc_len = 0
        try:
            if not self.daka_list_obj.add(unique_id, -50):
                return
            time.sleep(random.randint(0, 500) / 10) # 随机延时
            for msg in pkonline2(user_cookie, user_config, self.http2_client_obj, self.daka_list_obj, max_round=9999, max_win_round=9999):
                result_str += msg
                acc_len += len(msg)
                if acc_len > 4096:
                    old_result_str = result_str
                    result_str = ''
                    acc_len = 0
                    self.daka_list_obj.add_log(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), name, unique_id, old_result_str.replace('<br>', '\n'))
                    # 只保留最后8192个字符
                self.messages.put(('msg', unique_id, old_result_str + result_str))
        except AssertionError: # 快速关闭
            pass
        except Exception as e:
            self.daka_list_obj.add_warning(f'PK赛事反挂上段器出错：{traceback.format_exc()}')
            self.messages.put(('error', unique_id, traceback.format_exc()))
        finally:
            result_str = result_str.replace('<br>', '\n')
            self.daka_list_obj.add_log(datetime.datetime.now().strftime('%Y-%m-%d'), user_config['name'], user_config['unique_id'], result_str)
            self.daka_list_obj.remove(unique_id)

    def start_arbiter(self, user_id, current_timestamp):
        '''启动反挂器'''
        for token_user_dict in self.token_user_dict_list:
            if current_timestamp in self.success_timestamp: # 已经成功过，不再发射
                self.save_to_db(current_timestamp, user_id, 4) # SKIPPED
                continue
            self.daka_list_obj.set_pk_status(token_user_dict['config']['unique_id'], -1)
            threading.Thread(target=self.arbiter_wrapper, args=(token_user_dict, user_id, current_timestamp)).start()
            self.logger.info(f'启动arbiter {token_user_dict["config"]["name"]} -> {user_id}')
            time.sleep(self.arbiter_interval)
        try:
            self.success_timestamp.remove(current_timestamp)
        except KeyError:
            pass
        delta = self.arbiter_size - len(self.token_user_dict_list)
        for i in range(delta):
            self.save_to_db(current_timestamp, user_id, 9) # 补充缺失的位
        # 当前token_list已经发射完毕，获取新的token_list
        try:
            self.refresh_token()
        except AssertionError: # 快速关闭
            return
        
        while len(self.daka_list_obj.query_current_matching_king_id()) > 0:
            self.logger.info(f'king正在匹配中，等待...{self.daka_list_obj.query_current_matching_king_id()}')
            time.sleep(random.randint(12, 18) / 10) # 等待king匹配完成
            self.refresh_stars(self.token_user_dict_list[0])
            if (time.time()) - current_timestamp > 60:
                return # 超过60秒，退出

    def run(self):
        active = True
        try:
            self.refresh_token()
        except AssertionError: # 快速关闭
            return
        self.refresh_stars(self.token_user_dict_list[0])
        time.sleep(2)
        while True:
            modified_users = self.refresh_stars(self.token_user_dict_list[0])
            current_timestamp = int(time.time())
            def start_arbiter_with_delay(user_id, current_timestamp):
                time.sleep(self.arbiter_offset_win)
                self.start_arbiter(user_id, current_timestamp)
            for user_id in modified_users:
                threading.Thread(target=start_arbiter_with_delay, args=(user_id, current_timestamp)).start()

            active = False

            tracking_cnt = len(self.stargazer_set.difference(self.daka_list_obj.current_rivals))
            while (tracking_cnt == 0):
                if self.king:
                    return
                self.logger.info('所有人都已经被匹配，等待...')
                time.sleep(1.5) # 所有人都已经被匹配，等待
                try:
                    self.http2_client_obj.check_closing_state()
                except AssertionError: # 快速关闭
                    return
                tracking_cnt = len(self.stargazer_set.difference(self.daka_list_obj.current_rivals))
            for user_id, user in self.stargazers.items():
                if current_timestamp - user.get('active', 0) < 180: # 超过3分钟，自动退出
                    active = True
                    break
            if not active:
                self.logger.info('没有被跟踪者上线，等待30秒后重试...')
                for i in range(random.randint(18, 22)):
                    time.sleep(1.5)
                    try:
                        self.http2_client_obj.check_closing_state()
                    except AssertionError: # 快速关闭
                        return
            else:
                self.logger.info(f'正在跟踪中...匹配{self.stargazer_cnt - tracking_cnt}，跟踪{tracking_cnt}')
                time.sleep(random.randint(12, 18) / 10)
                try:
                    self.http2_client_obj.check_closing_state()
                except AssertionError: # 快速关闭
                    return
            


    def start(self):
        if self.session_id == None: # 初始化
            self.init_db()
            self.logger.info(f'初始化stargazer成功')
            time.sleep(1)
        if len(self.stargazer_list) == 0:
            if self.king:
                self.logger.info(f'自动上段模式，共{len(self.daka_list_obj.user_dict_obj.subscriber_unique_ids)}个订阅，{len(self.daka_list_obj.user_dict_obj.arbiter_unique_ids)}个裁判token')
            else:
                self.logger.info('没有stargazer，退出')
                return
        threading.Thread(target=self.run).start()

    

class notice_subscriber:
    '''公告订阅器，自动检测公告更新，提供弹窗或网页返回的方式来和班长互动'''
    def __init__(self, logger, http2_client_obj: http2_client, config: Config):
        self.http2_client_obj = http2_client_obj
        self.logger = logger
        self.log_dir = config.log_dir
        self.last_hash = {}
        self.latest_timestamp = 0
        self.get_last_hash()

    def get_last_hash(self):
        '''先获取上次公告哈希值(初始化以及距离上次更新时间超过1h)'''
        # 从log_dir中获取最近的log文件subscriber_%Y-%m-%d %H-%M-%S.timestamp.len().csv
        latest_file_name = ''
        ltt = 0
        for file_name in os.listdir(self.log_dir):
            if file_name.startswith('subscriber_'):
                t = int(file_name.split('.')[1])
                if t > ltt:
                    ltt = t
                    latest_file_name = file_name
        if latest_file_name == '':
            self.logger.info('没有找到订阅记录')
            return
        with open(os.path.join(self.log_dir, latest_file_name), 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                self.last_hash[(int(row[0]), int(row[1]))] = row[2] # (unique_id, group_id) = hash
        self.logger.info(f'加载了{len(self.last_hash)}条订阅记录')

    def get_subscription(self, users):
        # 读取最新公告，检测哪些公告需要更新
        self.latest_timestamp = int(time.time())
        self.new_notice = []
        for user in users:
            if user['config'].get('subscribe_notice', 0) == 0:
                continue
            unique_id = user['config']['unique_id']
            user_name = user['config']['name']
            self.logger.info(f'开始检测{unique_id}的订阅公告')  
            user_cookie = user['cookie']
            headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
            response = self.http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/own_groups?uniqueId=0', headers=headers, content=None) # 我的小班
            for group in response.json()['data']['list']:
                if group['rank'] == 1: # 公告测试用
                    continue
                group_id = group['id']
                group_share_key = group['shareKey']
                group_name = group['name']
                notice = group['notice']
                introduction = group['introduction']
                if notice is None:
                    notice = '(空)'
                notice_hash = hashlib.md5(notice.encode('utf-8')).hexdigest()
                if (unique_id, group_id) not in self.last_hash or self.last_hash[(unique_id, group_id)] != notice_hash:
                    self.logger.info(f'发现{unique_id}的{group_id}有更新(*^o^*)')
                    self.new_notice.append({'user_name': user_name, 
                                             'group_name': group_name, 
                                              'notice': notice, 
                                               'introduction': introduction, 
                                                 'group_id': group_id, 
                                                  'unique_id': unique_id,
                                                   'group_share_key': group_share_key,
                                                    'notice_hash': notice_hash})
            if False:
                self.logger.info("开始检测未读消息")
                # https://notify.baicizhan.com/rest/notify/v2/home
                headers = getHeaders("$notify", user_cookie, int(time.time()), index=1)
                response = self.http2_client_obj.send_http2_request('GET', 'https://notify.baicizhan.com/rest/notify/v2/home', headers=headers, content=None)
                messages = response.json()['data']
                for msg_class in messages:
                    if msg_class["messageType"] != 4: # 1:不断电 2:精选 3:同桌 4:小班 6:调查 7:点赞 9:组队
                        continue
                    if msg_class["unread"] == 0:
                        break
                # https://notify.baicizhan.com/rest/notify/v2/notify_list
                

            time.sleep(0.5)

    def get_top_notice(self, daka_list_obj: daka_list_class):
        if int(time.time()) - self.latest_timestamp > 3600: # 超过1h，重新获取公告哈希值
            users = daka_list_obj.get_user_dict_list()
            random.shuffle(users)
            self.get_subscription(users)
        if len(self.new_notice) == 0:
            return {'user_name': '', 'group_name': '', 'notice': '没有新的订阅～', 'introduction': '', 'group_id': -1, 'unique_id': -1, 'group_share_key': '', 'notice_hash': '', 'remain_count': 0}
        self.new_notice[0]['remain_count'] = len(self.new_notice)
        return self.new_notice[0]
    
    def read_reply_and_ack(self, unique_id, user_dict, group_share_key, group_id, notice_hash, reply_content, correspond = True):
        '''标记已读、回复和确认'''
        if unique_id == -1:
            return 400, "没有订阅，不需要回复"
        result_str = ''
        if correspond:
            # 回复公告并确认
            result_str, status = self.reply_and_ack(unique_id, user_dict, group_share_key, reply_content)
            if status == 0:
                self.logger.error(f'出现错误，不标记已读：{result_str}')
                return 400, '出现了错误，不标记已读'
        # 在内存中标记
        self.last_hash[(int(unique_id), int(group_id))] = notice_hash

        self.new_notice.pop(0) # 弹出已读的公告
        self.logger.info(f'将{unique_id}的{group_id}的公告 标记已读')

        # 如果是最后一条订阅，则写入log文件
        if len(self.new_notice) & 7 == 0:
            self.save_log()
            self.logger.info(f'保存了{len(self.last_hash)}条订阅 已读记录')

        return 200, result_str
    
    def save_log(self):
        '''保存公告哈希值到log文件'''
        with open(os.path.join(self.log_dir, f'subscriber_{datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.{int(time.time())}.csv'), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for key, value in self.last_hash.items():
                writer.writerow(list(key) + [value])
        self.logger.info(f'保存了{len(self.last_hash)}条订阅记录')

    def reply_and_ack(self, unique_id, user_dict, group_share_key, content):
        '''回复公告并确认'''
        try:
            status_1 = 0
            if not unique_id or not group_share_key:
                self.logger.error(f'回复失败，参数不完整{unique_id} {group_share_key} {content}')
                return "参数不完整"
            time_long = int(time.time() * 1000)
            result_str = ''
            group_id = 0 # 后面会获取
            headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
            headers['Content-Type'] = 'application/json; charset=UTF-8'
            # 回复
            if content != '' and content is not None:
                payload = {
                    'shareKey': group_share_key,
                    'nickname': content,
                }
                response_json = self.http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/set_nickname', headers=headers, content = payload).json()
                if response_json['code'] == 1:
                    result_str = '回复成功<br>'
                    status_1 = 1
                else:
                    result_str = f'回复失败{response_json["message"]}<br>'
            else:
                status_1 = 1
            # 获取最新信息
            response_json = self.http2_client_obj.send_http2_request('GET', f'https://group.baicizhan.com/group/information?shareKey={group_share_key}', headers=headers, content=None).json()
            if response_json['code'] == 1:
                group_info = response_json['data']['groupInfo']
                group_id = group_info['id']
                members = response_json['data']['members']
                for member in members:
                    if member['uniqueId'] == unique_id:
                        result_str += f'现在名字{member["nickname"]}<br>'
                        break
            else:
                self.logger.error(f'获取{unique_id}的{group_share_key}的公告失败{response_json["message"]}')
                return f'获取{unique_id}的{group_share_key}的公告失败{response_json["message"]}<br>', 0
            # 收到
            response_json = self.http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/receive_notice?groupId={group_id}', headers=headers, content={}).json()
            if response_json['code'] == 1:
                result_str += '收到成功<br>'
                status_1 &= 1
            else:
                result_str += f'收到失败{response_json["message"]}<br>'
                status_1 = 0
            self.logger.info(result_str)
            return result_str, status_1
        except Exception as e:
            result_str += f'回复失败{e}{traceback.format_exc()}<br>'
            self.logger.error(result_str)
            return result_str, 0


def heartbeat_demon( daka_list: daka_list_class, user_cookie, user_config, http2_client_obj: http2_client):
    unique_id = user_config['unique_id']
    while not daka_list.query(unique_id):
        time.sleep(1)
    demon_daka_type = daka_list.query(unique_id)
    report_cnt = 0
    time.sleep(random.randint(10, 100) / 10) # 随机延时，防止同时启动多个心跳线程
    try:
        while daka_list.query(unique_id) is not None and daka_list.query(unique_id) == demon_daka_type:
            payload=[
                {"index":0}
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=0)
            report_cnt += 1
            if report_cnt > 7200: # 60分钟
                daka_list.add_warning(unique_id, '心跳超时: 60分钟')
                break
            for i in range(10):
                time.sleep(3)
                http2_client_obj.check_closing_state()
    except AssertionError:
        return


    

def print_puzzle(puzzle_dict):
    chn_mean = puzzle_dict['chnMean']
    option_list = puzzle_dict['options']
    question = puzzle_dict['question']
    answer = puzzle_dict['rightAnswer']
    result = f'{question}({chn_mean})('
    for i, option in enumerate(option_list):
        if i == answer - 1:
            result += f'<font  color="green">{option}</font>/'
        else:
            result += f'{option}/'
    result += ')'
    return result


def pkonline(user_cookie, user_config, http2_client_obj: http2_client, daka_list: daka_list_class, max_round=3):
    '''pkonline'''# max_round用来随机轮数，用来调用2次分散打卡时间
    if not BCZ_NCSVC:
        return # 已于12.5结束
    # 领奖
    # https://pkonline1.baicizhan.com/api/contest/2024/prepare/giftMain?code=mB5AG9fCzo
    headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=1)
    url = f'https://{headers["Host"]}/api/contest/2024/prepare/giftMain?code=mB5AG9fCzo'
    response = http2_client_obj.send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    cnt = data['blindBox']
    while cnt > 0:
        # https://pkonline1.baicizhan.com/api/contest/2024/prepare/useBlindBox
        headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=1)
        url = f'https://{headers["Host"]}/api/contest/2024/prepare/useBlindBox'
        response = http2_client_obj.send_http2_request('POST', url, headers, content={})
        data = response.json()['data']
        yield f'领取{data["name"]}成功:{data["url"]}，剩余{cnt-1}个'

        url = f'https://{headers["Host"]}/api/contest/2024/prepare/giftMain?code=mB5AG9fCzo'
        response = http2_client_obj.send_http2_request('GET', url, headers, None)
        data = response.json()['data']
        cnt = data['blindBox']
        time.sleep(random.randint(1, 2))

    # https://pk.baicizhan.com/contest2024/sign/?code=mB5AG9fCzo
    # https://pk.baicizhan.com/contest2024/preparation/index.html?code=mB5AG9fCzo
    # https://pkonline1.baicizhan.com/api/contest/2024/tournament/status?code=mB5AG9fCzo
    time_long = int(time.time() * 1000)
    headers = getHeaders("$pk", user_cookie, int(time.time()), index=1)
    url = f'https://{headers["Host"]}/contest2024/sign/?code=mB5AG9fCzo'
    response = http2_client_obj.send_http2_request('GET', url, headers, None, False)
    if response.status_code != 200:
        yield f'<p style="color:red">单词pk接口请求失败</p>{response.text}'
    url = f'https://{headers["Host"]}/contest2024/preparation/index.html?code=mB5AG9fCzo'
    response = http2_client_obj.send_http2_request('GET', url, headers, None)

    headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
    url = f'https://{headers["Host"]}/api/contest/2024/tournament/status?code=mB5AG9fCzo'
    response = http2_client_obj.send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    if data['status'] == 1:
        yield f'pk正在进行 '
    extra_info = "{\"ABPage\":\"B\"}"
    if data['college'] == False:
        extra_info = "{\"ABPage\":\"A\"}"
    payload = [
        {"index": 29, "extra_info": extra_info}, # pk加载
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
    # https://pkonline1.baicizhan.com/api/contest/2024/prepare/main?code=mB5AG9fCzo
    url = f'https://{headers["Host"]}/api/contest/2024/prepare/main?code=mB5AG9fCzo'
    response = http2_client_obj.send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    if data is None:
        yield f'<p style="color:red">请手动登录并报名pk再运行</p>'
        return
    if data['todayPKFinished'] == True:
        yield f'今日PK已结束'
        return
    yield '开始pk'
    payload = [
        {"index": 30}, # pk主页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
    # https://pkonline1.baicizhan.com/api/contest/2024/prepare/pkMain?code=mB5AG9fCzo
    url = f'https://{headers["Host"]}/api/contest/2024/prepare/pkMain?code=mB5AG9fCzo'
    response = http2_client_obj.send_http2_request('GET', url, headers, None)
    data = response.json()['data']
    daily_round = data['dailyRound']
    current_round = 0
    if max_round == 0:
        return
    yield f' 今已完成{daily_round}/3 '
    time.sleep(1)
    if daily_round < 3:
        payload = [
            {"index": 31} # 进入pk
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
        
        # https://pkonline1.baicizhan.com/api/contest/2024/tournament/failed_puzzle?lastId=
        time_long = int(time.time() * 1000)
        headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
        url = f'https://{headers["Host"]}/api/contest/2024/tournament/failed_puzzle?lastId='
        response = http2_client_obj.send_http2_request('GET', url, headers, None)
        data = response.json()['data']

        payload = [
            {"index": 32} # pk练习页面
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
        time.sleep(1)
        payload = [
            {"index": 33} # 点击开始按钮
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
        # https://pk.baicizhan.com/contest2024/contest/index.html?code=mB5AG9fCzo&mode=practice
        time_long = int(time.time() * 1000)
        headers = getHeaders("$pk", user_cookie, int(time.time()), index=3)
        url = f'https://{headers["Host"]}/contest2024/contest/index.html?code=mB5AG9fCzo&mode=practice'
        response = http2_client_obj.send_http2_request('GET', url, headers, None)

        while True:
            payload = [
                {"index": 34, "extra_info": "{\"CurrentRound\":%d}" % 0} # pk开始（CurrentRound是摆设）
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
            # 匹配
            # https://pkonline1.baicizhan.com/api/contest/practice/match?code=mB5AG9fCzo&contestId=null
            
            time_long = int(time.time() * 1000)
            headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
            url = f'https://{headers["Host"]}/api/contest/practice/match?code=mB5AG9fCzo&contestId=null'
            response = http2_client_obj.send_http2_request('GET', url, headers, None)
            data = response.json()['data']
            challenge_id = data['challengeId']
            current_round = data['currentRound']
            yield f'第{current_round}轮<br>'
            payload = [
                {"index": 35, "extra_info": "{\"MatchTime\":%d}" % (int(time.time() * 1000) - time_long)} # pk匹配成功
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)

            post_headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
            post_headers['Content-Type'] = 'application/json'
            options_headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=2)# 这两个请求头一直使用到结束
            time.sleep(3)

            prev_order = 0
            while True:
                # 开始答题
                # https://pkonline1.baicizhan.com/api/contest/practice/heartbeat
                url = f'https://{options_headers["Host"]}/api/contest/practice/heartbeat'
                response = http2_client_obj.send_http2_request('OPTIONS', url, options_headers, None)
                content = {
                    "challengeId": challenge_id
                }
                response = http2_client_obj.send_http2_request('POST', url, post_headers, content=content)
                data = response.json()['data']
                order = data['order']
                while order == 0 or order == prev_order:
                    response = http2_client_obj.send_http2_request('POST', url, post_headers, content=content)
                    data = response.json()['data']
                    order = data['order']
                    time.sleep(1)
                yield f'第{order}题'
                rival_escaped = data['rivalEscaped']
                ans = daka_list.puzzle_solver(data['puzzle'])
                response_thresh = 4000
                response_delay = random.randint(2000, response_thresh)
                start_timestamp = int(time.time() * 1000)
                session_cnt = int(response_delay / 1000)
                session_delay = response_delay % 1000
                for i in range(session_cnt):
                    time.sleep(1)
                    response = http2_client_obj.send_http2_request('POST', url, post_headers, content = content)
                    rival_escaped = response.json()['data']['rivalEscaped']
                    if rival_escaped:
                        break
                time.sleep(session_delay / 1000)
                ans_content = {
                    "challengeId": challenge_id,
                    "order": order,
                    "answer": ans
                }
                response = http2_client_obj.send_http2_request('POST', url, post_headers, ans_content)
                data = response.json()['data']
                rival_escaped = data['rivalEscaped']
                payload = [
                    {"index": 36, "extra_info": "{\"ContestId\":null,\"ChallengeId\":%d,\"QuesOrder\":%d,\"PuzzleId\":%d,\"ChoiceOrder\":%d,\"CostTime\":%d,\"IsRight\":false}" % (challenge_id, order, data['puzzle']['id'], ans, int(time.time() * 1000 - start_timestamp))} # pk答题成功
                ]
                report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
                if data['rivalAnswer'] is None and not rival_escaped:
                # 等待对手作答
                    while True:
                        response = http2_client_obj.send_http2_request('POST', url, post_headers, content)
                        data = response.json()['data']
                        if data['rivalAnswer'] is not None or data['rivalEscaped']:
                            break
                        time.sleep(1)
                # 检查答案
                daka_list.puzzle_solver(data['puzzle'])
                right_answer = data['puzzle']['rightAnswer']
                my_answer = '√' if data['meAnswer'] == right_answer else '×'
                rival_answer = '已逃跑'
                if not rival_escaped:
                    rival_answer = '√' if data['rivalAnswer'] == right_answer else '×'
                puzzle_str = print_puzzle(data['puzzle'])
                yield f'{puzzle_str} {my_answer}/{rival_answer}<br>'

                time.sleep(3)
                if order == 7:
                    break
                prev_order = order # 防止刷新不及时导致重复答题

            # 结束本轮pk
            payload = [
                # "{\"CurrentRound\":1}"
                {"index": 37, "extra_info": "{\"CurrentRound\":%d}" % current_round} # pk结束
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
            # https://pkonline1.baicizhan.com/api/contest/practice/result?contestId=null&challengeId=&code=mB5AG9fCzo
            time_long = int(time.time() * 1000)
            headers = getHeaders("$pkonline1", user_cookie, int(time.time()), index=3)
            url = f'https://{headers["Host"]}/api/contest/practice/result?contestId=null&challengeId={challenge_id}&code=mB5AG9fCzo'
            response = http2_client_obj.send_http2_request('GET', url, headers, None)
            data = response.json()['data']
            daily_finished = data['dailyFinished']
            if daily_finished:
                yield f'完成3轮 +50铜板<br>'
                break
            else:
                yield f'完成第{current_round}轮<br>'
                current_round += 1
                if current_round > max_round:
                    return
                time.sleep(random.randint(1,4))

def check_and_charge_pk_energy(user_cookie, user_config, http2_client_obj: http2_client, session_id):
    '''检查并充能PK能量'''
    # https://pk.baicizhan.com/api/rankpk/energy?time=&activity_id=0&session_id=
    time_long = int(time.time() * 1000)
    time_short = int(time.time())
    headers = getHeaders("$pk", user_cookie, time_short, index=1)
    url = f'https://{headers["Host"]}/api/rankpk/energy?time={time_long}&activity_id=0&session_id={session_id}'
    response = http2_client_obj.send_http2_request('GET', url, headers, None)
    data = response.json()
    if data.get('data', {}).get('full_seconds', 0) < 0:
        return True
    # https://pk.baicizhan.com/api/rankpk/charge?time=&activity_id=0&session_id=
    headers = getHeaders("$pk", user_cookie, time_short, index=1)
    url = f'https://{headers["Host"]}/api/rankpk/charge?time={time_long}&activity_id=0&session_id={session_id}'
    response = http2_client_obj.send_http2_request('GET', url, headers, content={})
    json = response.json()
    if json.get('code', False) == True and json.get('data', {}).get('full_seconds', 0) < 0:
        return True
    return False

pkonline2_king_lock = threading.Lock() # 防止多账号同时开始匹配
pkonline2_lock = threading.Lock()
pooling_cnt = 0
def pkonline2(user_cookie, user_config, http2_client_obj: http2_client, daka_list:daka_list_class, max_round=3, max_win_round=3, allow_self=False):
    '''单词对战''' # max_round无论输赢，但是体力值不足时，会自动退出
    if user_config.get('can_pk', 1) == 0:
        yield f'{user_config["name"]}不参加pk'
        return
    rival_escaped_notified = False
    name = user_config['name']
    unique_id = user_config['unique_id']
    time_short = int(time.time())
    time_long = int(time.time() * 1000) # 只有report_event的cookie和url需要更新time_long，其余均不需要
    # https://pk.baicizhan.com/api/rankpk/v2/current_session?time=1728962138173
    pk_get_headers = getHeaders("$pk", user_cookie, time_short, index=1, quote=True)
    pk_post_headers = getHeaders("$pk", user_cookie, time_short, index=1, quote=True)
    pk_post_headers['Content-Type'] = 'application/json'

    total_round = 0
    total_win_round = 0
    rival_id = 0
    global pooling_cnt
    while True:
        total_round += 1
        if total_round > max_round or total_win_round >= max_win_round:
            daka_list.set_pk_status(unique_id, 0)
            return
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/v2/current_session?time={time_long}'
        response = http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        current_user_info = data['currentRankUserInfo']
        end_time_str = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(data['session']['endTime'] // 1000))# auditEndTime=
        session_id = data["session"]["sessionId"]
        current_level = current_user_info["currentLevel"]
        current_star = current_user_info["currentStar"]
        current_energy = current_user_info["energy"]
        yield f'单词pk第{total_round}轮 {session_id}赛季{current_level}段{current_star}星{current_energy}体力<br>'
        state = data['session']['state']
        if state == 3:
            yield f'单词pk赛季清扫中，结束<br>'
            daka_list.set_pk_status(unique_id, 0)
            return
        if state != 2:
            yield f'<p style="color:red">单词pk赛季状态{state}，请检查</p>'
            daka_list.set_pk_status(unique_id, 0)
            return
        # https://pk.baicizhan.com/api/rankpk/main?time=1728962138249&activity_id=0&session_id=40
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/main?time={time_long}&activity_id=0&session_id={session_id}'
        response = http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        current_level = data['current_level']
        current_star = data['current_star']
        current_energy = data['energy']
        reward_available = data['reward_avalible']

        for level in data['levels']:
            if level['level'] == current_level:
                current_level_dict = level
                break
        energy_cost = current_level_dict['energy_cost']
        if current_energy < energy_cost:
            if daka_list.do_not_charge_pk_energy:
                yield f'体力{current_energy}不足{energy_cost}，退出<br>'
                yield f'<font color="lemonchiffon">-2</font><br>'
                daka_list.set_pk_status(unique_id, 2, int(time.time()+60*(energy_cost - current_energy))) # 能量耗尽
                return
            yield f'体力{current_energy}不足{energy_cost}，充能中<br>'
            if not check_and_charge_pk_energy(user_cookie, user_config, http2_client_obj, session_id):
                yield f'充能失败，退出<br>'
                yield f'<font color="lemonchiffon">-2</font><br>'
                daka_list.set_pk_status(unique_id, 2, int(time.time()+60*(energy_cost - current_energy))) # 能量耗尽
                return
            yield f'充能成功，继续<br>'
            continue
        rank_name_en = current_level_dict['name_en']
        is_king = rank_name_en == 'king'
        daka_list.set_is_king(unique_id, rank_name_en, current_star, current_energy)
        if not is_king and max_win_round == 6666:
            max_win_round = 9999
        if max_win_round == 9999 and is_king: # 为arbiter上段
            daka_list.set_pk_status(unique_id, 0)
            return


        if reward_available:
            yield f'正在领取'
            payload = [
                {"index": 38}
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            # https://pk.baicizhan.com/api/rankpk/get_reward?time=&session_id=40
            url = f'https://{pk_get_headers["Host"]}/api/rankpk/get_reward?time={time_long}&session_id={session_id}'
            response = http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
            data = response.json()['data']
            pre_session_id = data['sessionId']
            money = data['money']
            yield f'{pre_session_id}赛季+{money}铜板'
        payload = [ # 进入页面
            {"index": 38, "extra_info": '{"trace":"together_tab","session_id":"%d","pk_rank":"%d"}'% (session_id, current_level)}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        
        time.sleep(1)

        payload = [ # 开始匹配
            {"index": 39, "without_login": True, "extra_info": '{"trace":"together_tab","session_id":"%d","pk_rank":"%d"}'% (session_id, current_level)}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)

        challenge_id = 0
        puzzle_count = 0
        side = ''
        rival_name = ''
        rival_avatar = ''
        time_start = time.time()
        # if total_round == 1 and daka_list.query_pk_status(unique_id) != 0:
        #     raise Exception('pk_status_not_0')

        if rank_name_en == 'king':
            if not allow_self:
                pkonline2_king_lock.acquire()
        elif not allow_self:
            pkonline2_lock.acquire()
        daka_list.set_pk_status(unique_id, -1)
        while pooling_cnt > 31:
            time.sleep(10)
        pooling_cnt += 1 # 同时pk的账号数限制为32
        while True:
            # https://pk.baicizhan.com/api/rankpk/challenge/match?challenge_type=word&challenge_level=wood&time=1728962245954&activity_id=0&session_id=40
            url = f'https://{pk_get_headers["Host"]}/api/rankpk/challenge/match?challenge_type=word&challenge_level={rank_name_en}&time={time_long}&activity_id=0&session_id={session_id}'
            response = http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
            data = response.json()['data']
            if not data.get('again', False): # 匹配成功
                challenge_id = data['challenge_id']
                puzzle_count = data['puzzle_count']
                side = data['side']
                rival_name = data['rival']['nickname']
                rival_avatar = data['rival']['avatar']
                break
            time.sleep(1)
        daka_list.set_pk_status(unique_id, 1)
        if rank_name_en == 'king':
            if not allow_self:
                pkonline2_king_lock.release()
        elif not allow_self:
            pkonline2_lock.release()
        yield f'匹配对手:{rival_name}<br>对手bczId:'

        
        
        current_rival_id = daka_list.find_unique_id(rival_avatar, rival_name)
        rival_score = 0
        rival_score_max = 0 # 对手最高分，自己也不能超过
        rival_status = 0 # -1黑名单，1白名单，0正常
        if current_rival_id:
            yield f'<font color="lemonchiffon">{current_rival_id}</font><br>' # 谨慎修改！[27:-11]用于传递信息
            daka_list.add_rival(current_rival_id)
            rival_id = current_rival_id
            
            if rival_id in daka_list.pk_whitelist:
                yield f'白名单用户💖<br>'
                rival_status = 1
                daka_list.add_warning(f'{name}遇到了白名单用户{rival_name}{rival_id}')
            elif rival_id in daka_list.pk_blacklist:
                yield f'黑名单用户🚫<br>'
                rival_status = -1
                daka_list.add_warning(f'{name}遇到了黑名单用户{rival_name}{rival_id}')
            elif rival_id in daka_list.user_dict_obj.arbiter_unique_ids:
                yield f'arbiter用户🤖<br>'
                if rival_id > unique_id: # 避免出现DRAW，逃跑
                    time_long = int(time.time() * 1000)
                    url = f'https://{pk_get_headers["Host"]}/api/rankpk/v2/current_session?time={time_long}'
                    response = http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
                    url = f'https://{pk_get_headers["Host"]}/api/rankpk/main?time={time_long}&activity_id=0&session_id={session_id}'
                    response = http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
                    return
                rival_status = 6666
        else:
            yield f'<font color="lemonchiffon">未找到</font><br>'
            rival_id = -1
        
        payload = [ # 匹配成功
            {"index": 40, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d,\"cost_time\":%d}"% (session_id, current_level, challenge_id, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        time.sleep(0.5)
        payload = [ # 初始化（重复发送3次等待）
            {"index": 41, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d,\"cost_time\":%d}"% (session_id, current_level, challenge_id, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        time.sleep(0.25)
        payload = [ # 初始化（重复发送3次等待）
            {"index": 42, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d,\"cost_time\":%d}"% (session_id, current_level, challenge_id, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        
        order = 0
        chosen_id = 0
        rival_answer = None
        rival_escaped = False
        my_answer = None
        right_answer = None
        current_time = 10000
        my_score = 0
        score_delta = 0
        my_penalty = 0 # 对于自己打错的，不计入分差
        topic_id = 0
        time_start = time.time()
        while order < puzzle_count: # 最后一题作答完毕之后，退出
            try:
                # https://pk.baicizhan.com/api/rankpk/challenge/heartbeat?activity_id=0
                # {"challenge_id":421585,"submit":null,"session_id":40}
                url = f'https://{pk_get_headers["Host"]}/api/rankpk/challenge/heartbeat?activity_id=0'
                content = {
                    "challenge_id": challenge_id,
                    "submit": None,
                    "session_id": session_id
                }
                while True:
                    response = http2_client_obj.send_http2_request('POST', url, pk_post_headers, content=content)
                    time.sleep(0.5)
                    data = response.json()['data']
                    if data['order'] != order:
                        break
                # 报告上一题
                if order > 0: # 第一题时，order还未赋值
                    score_str = f'{my_score}' if order > 1 else ''
                    payload = [
                        {"index": 43, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"topic_id\":%d,\"challenge_id\":%d,\"puzzle_order\":%d,\"score\":\"%s\",\"challenge_type\":\"排位赛\",\"cost_time\":%d}"% (session_id, current_level, topic_id, challenge_id, order, score_str, int(time.time() - time_start))}
                    ]
                    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
                    time_start = time.time()
                order = data['order']
                chosen_id, msg = daka_list.word_lookup_puzzle_solver(data['puzzle'])
                topic_id = data['puzzle']['topicId']
                rival_escaped = data['rivalEscaped']
                rival_answer = data['rival']['answer']

                yield f'第{order}题 {msg}<br>'
                if rival_status == -1:
                    yield '[AC]'
                    ub = 8749 + 50 * min(max(rival_score - my_score + daka_list.anticheat_power * order, -25), 25) # 8749-9999
                    if rival_score_max and ub > rival_score_max + 300:
                        ub = rival_score_max + 300
                    lb = ub
                elif max_win_round == 6666 or rival_status == 1: # 跟踪模式没有遇到被跟踪对象或遇到白名单用户，禁用反挂
                    lb = 6666
                    ub = lb + 500
                else:
                    lb = 6500 + 50 * min(max(rival_score - my_score, -15), 25) # 5750-8250
                    ub = lb + 500
                
                target_time = random.randint(lb, ub) # 分数=答对100+剩余时间/100，每题满分200
                yield f'目标{int(100 + target_time/100)}({lb}-{ub})<br>'
                
                current_time = data['puzzle']['cd']
                
                # {"challenge_id":421585,"nvcVal":"","submit":{"order":1,"answer":3},"session_id":40}
                content_with_ans = {
                    "challenge_id": challenge_id,
                    "nvcVal": "",
                    "submit": {
                        "order": order,
                        "answer": chosen_id
                    },
                    "session_id": session_id
                }
                modem_simulate = (random.randint(1, 5) == 1)

                while True:
                    response = http2_client_obj.send_http2_request('POST', url, pk_post_headers, content)
                    data = response.json()['data']
                    current_time = data['puzzle']['cd']
                    rival_answer = data['rival']['answer']
                    rival_escaped = data['rivalEscaped']
                    
                    if current_time < target_time or (rival_answer is not None and rival_answer == chosen_id):
                        if modem_simulate and target_time < 9000:  # 模拟网络意外延时，反挂除外
                            time.sleep(0.5)
                        break
                    if current_time - 500 <= target_time and current_time < 10000:
                        time.sleep((current_time - target_time) / 1000)
                        break
                    time.sleep(0.4)
                

                response = http2_client_obj.send_http2_request('POST', url, pk_post_headers, content_with_ans)
                time.sleep(0.2)
                response = http2_client_obj.send_http2_request('POST', url, pk_post_headers, content_with_ans)
                time.sleep(0.2)
                data = response.json()['data']
                my_answer = data['me']['answer']
                fail_cnt = 0
                while my_answer is None:
                    response = http2_client_obj.send_http2_request('POST', url, pk_post_headers, content_with_ans)
                    time.sleep(0.2)
                    data = response.json()['data']
                    my_answer = data['me']['answer']
                    me_escaped = data['meEscaped']
                    fail_cnt += 1
                    if me_escaped or fail_cnt > 5:
                        yield f'<font  color="red">掉线</font><br>'
                        daka_list.record_pk_result(name, rival_id, rival_name, my_score, rival_score)
                        daka_list.remove_rival(rival_id)
                        raise Exception(f'{name} 掉线')
                score_delta = data['me']['score'] - my_score
                my_score = data['me']['score']
                right_answer = data['puzzle']['right_answer']
                if my_answer == right_answer:
                    yield f'✓{my_score}(+{score_delta})/'
                else:
                    my_penalty += 175
                    yield f'×{my_score}(+{score_delta})/'
                rival_answer = data['rival']['answer']
                rival_escaped = data['rivalEscaped']
                content = {
                    "challenge_id": challenge_id,
                    "submit": None,
                    "session_id": session_id
                }
                while rival_answer is None and not rival_escaped and current_time > 0:
                    response = http2_client_obj.send_http2_request('POST', url, pk_post_headers, content)
                    time.sleep(0.5)
                    data = response.json()['data']
                    rival_answer = data['rival']['answer']
                    rival_escaped = data['rivalEscaped']
                    current_time = data['puzzle']['cd']
                score_delta = data['rival']['score'] - rival_score
                rival_score = data['rival']['score']
                if rival_escaped:
                    yield f'对手逃跑<br>'
                    if not rival_escaped_notified:
                        yield f'<font color="green">对手逃跑</font><br>'
                        rival_escaped_notified = True
                    score_delta = -1
                elif rival_answer is None:
                    yield f'未作答<br>'
                    score_delta = -1
                else:
                    if rival_answer == right_answer:
                        yield f'✓{rival_score}(+{score_delta})<br>'
                        rival_score_max = max(rival_score_max, (score_delta-100)*100)
                    else:
                        my_penalty -= 150
                        yield f'×{rival_score}(+{score_delta})<br>'
                daka_list.word_lookup_patcher(data['puzzle'], right_answer, topic_id, rank_name_en, score_delta)
                # 等待直到current_time为0
                while True:
                    response = http2_client_obj.send_http2_request('POST', url, pk_post_headers, content)
                    time.sleep(0.5)
                    data = response.json()['data']
                    current_time = data['puzzle']['cd']
                    rival_escaped = data['rivalEscaped']
                    if current_time == 0 or order != data['order']:
                        break
            except:
                yield traceback.format_exc()
                break # 有可能是睡眠导致比赛异常，退出即可
        pooling_cnt -= 1
        # 最后一题作答完毕
        score_str = f'{my_score}' if order > 1 else ''
        payload = [
            {"index": 43, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"topic_id\":%d,\"challenge_id\":%d,\"puzzle_order\":%d,\"score\":\"%s\",\"challenge_type\":\"排位赛\",\"cost_time\":%d}"% (session_id, current_level, topic_id, challenge_id, order, score_str, int(time.time() - time_start))}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        payload = [
            {"index": 44, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\",\"challenge_type\":\"排位赛\",\"challenge_id\":%d}" % (session_id, current_level, challenge_id)}
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        # https://pk.baicizhan.com/api/rankpk/challenge/result?challenge_id=421585&side=left&time=1728962287864&activity_id=0&session_id=40
        url = f'https://{pk_get_headers["Host"]}/api/rankpk/challenge/result?challenge_id={challenge_id}&side={side}&time={time_long}&activity_id=0&session_id={session_id}'
        response = http2_client_obj.send_http2_request('GET', url, pk_get_headers, None)
        data = response.json()['data']
        incr_score = data['incrScore']
        limited = data['limited']
        yield f'学习得分+{incr_score}'
        if limited:
            yield f' 达上限 '
        my_score = data['me']['score']
        rival_score = data['rival']['score']
        yield f' {my_score} - {rival_score} - '
        daka_list.record_pk_result(name, rival_id, rival_name, my_score, rival_score)
        daka_list.remove_rival(rival_id)
        if my_score > rival_score:
            yield f'<font color="green">WIN</font><br>' # 此处有stargazer的信息
            total_win_round += 1
        elif my_score < rival_score:
            yield f'<font color="red">LOSE</font><br>'
        else:
            yield f'<font color="yellow">DRAW</font><br>'
        payload = [
            {"index": 45, "without_login": True, "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"%d\",\"pk_rank\":\"%d\"}" % (session_id, current_level)} # pk结束
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        yield "<br><br>"
        if max_win_round != 6666: # arbiter模式不等待
            delay = random.randint(3,6)
            for i in range(delay):
                yield f'.'
                time.sleep(1)
        if max_win_round == 6666 and rival_status != -1:
            daka_list.set_pk_status(unique_id, 0) # arbiter没有遇到黑名单用户，直接结束
            return

def yzdd(user_cookie, user_config, http2_client_obj: http2_client, daka_list: daka_list_class):
    '''一站到底'''
    if not YZDD:
        return
    # 如果是星期日，跳过
    if datetime.datetime.now().weekday() == 6:
        return "$星期日，跳过"
    # https://pkonline2.baicizhan.com/api/contest/2024/one_fight/get_exam_question?bczId=0&day=
    time_long = int(time.time() * 1000)
    headers = getHeaders("$pkonline2", user_cookie, int(time.time()), index=1)
    url = f'https://{headers["Host"]}/api/contest/2024/one_fight/get_exam_question?bczId=0&day='
    response = http2_client_obj.send_http2_request('GET', url, headers, None)
    data = response.json()['data']

    conn = sqlite3.connect('yzdd.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS yzdd (
        INDEX_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        QID INTEGER,
        IMAGE TEXT,
        TITLE TEXT,
        ANSWER TEXT,
        OPTION_2 TEXT,
        OPTION_3 TEXT,
        OPTION_4 TEXT,
        DETAIL TEXT)
    ''')
    conn.commit()

    qid = data['qid']

    answered = True if (data.get('answer', 1) > 0) else False
    if not answered:
        # qid 查询数据库
        # https://pkonline2.baicizhan.com/api/contest/2024/one_fight/submit_exam
        # Content-Type: application/json; charset=UTF-8
        time.sleep(random.randint(2000, 4000) / 1000)
        headers = getHeaders("$pkonline2", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        url = f'https://{headers["Host"]}/api/contest/2024/one_fight/submit_exam'
        payload = {
            "qid": data['qid'],
            "answer": random.randint(1, 4)
        }
        response = http2_client_obj.send_http2_request('POST', url, headers, payload)
        time.sleep(0.9)

        # 重新请求题目
        # https://pkonline2.baicizhan.com/api/contest/2024/one_fight/get_exam_question?bczId=0&day=
        headers = getHeaders("$pkonline2", user_cookie, int(time.time()), index=1)
        url = f'https://{headers["Host"]}/api/contest/2024/one_fight/get_exam_question?bczId=0&day='
        response = http2_client_obj.send_http2_request('GET', url, headers, None)
        data = response.json()['data']


    
    title = data['title']
    answer_id = data['answer']
    image = data['image']
    detail = data['detail']
    options = []
    options.append(data['options'][answer_id-1]['content'])
    for i, option in enumerate(data['options']):
        if i != answer_id - 1:
            options.append(option['content'])
    cursor.execute('''SELECT * FROM yzdd WHERE QID == ?''', (qid, ))
    result = cursor.fetchone()
    if not result:
        cursor.execute('''INSERT INTO yzdd (QID, TITLE, IMAGE, ANSWER, OPTION_2, OPTION_3, OPTION_4, DETAIL) VALUES (?,?,?,?,?,?,?,?)''', (qid, title, image, options[0], options[1], options[2], options[3],detail))
        conn.commit()
    conn.close()
    return f'$今日题目:{title}:<img src="{image}" width="100px" height="100px"><br>正确答案:{options[0]}<br>选项1:{options[1]}<br>选项2:{options[2]}<br>选项3:{options[3]}<br>'

def deskmate_pk(cookie, config, http2_client_obj: http2_client):
    '''同桌PK'''
    
    data = {}

    name = config['name']
    # https://social.baicizhan.com/api/deskmate/game/start_word_match_game
    time_long = int(time.time() * 1000)
    headers = getHeaders('$social', cookie, time_long, index = 1)
    headers['Content-Type'] = 'application/json'
    response = http2_client_obj.send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/start_word_match_game', headers, {})
    yield (f'{name} 开始每周双人战{response.json()}<br>')
    if response.json()['code'] == 100:
        yield f'出现问题，请检查<br>'
        return
    
    
    
    while True:
        # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
        time_long = int(time.time() * 1000)
        headers = getHeaders('$social', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json'
        response = http2_client_obj.send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
        data = response.json()['data']
        if data.get('needCompletedTopicList', None) is not None:
            break
        time.sleep(1)

    if data['newUserGuide']['status'] == 0:
        yield ('播放新手指南4s')
        # https://social.baicizhan.com/api/deskmate/game/finish_new_user_guide
        time_long = int(time.time() * 1000)
        headers = getHeaders('$social', cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json'
        time.sleep(4)
        response = http2_client_obj.send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/finish_new_user_guide', headers, {})

    finish_all = False
    if time.localtime().tm_wday in [5,6]:
        finish_all = True

    while True:
        try:
            cnt = data['mine']['finishCount']
            deskmate_cnt = data['deskmate']['finishCount']
            # yield (cnt, deskmate_cnt)
            if finish_all and cnt + deskmate_cnt >= 100:
                break
            elif not finish_all and cnt >= 50:
                break
            topic_list = data['needCompletedTopicList'] # 后面50个是自己的词书
            topic_list.reverse()
            deskmate_completed_list = data['deskmate']['completedTopicList']
            my_completed_list = data['mine']['completedTopicList']
            finished_topic_ids = [t['topicId'] for t in deskmate_completed_list]
            finished_topic_ids.extend([t['topicId'] for t in my_completed_list])
            # 找第一个同桌未完成的题目
            found = - random.randint(0, 2)
            topic_id = -1
            
            for topic in topic_list:
                if topic['topicId'] not in finished_topic_ids:
                    found += 1
                    topic_id = topic['topicId']
                    topic_option = topic['topicOption']
                    if found > 0:
                        break
            if topic_id == -1:
                raise f'{name} 没有找到未完成的题目'

            time.sleep(random.randint(3000, 4000) / 1000)

            # https://social.baicizhan.com/api/deskmate/game/word_match
            # {"topicId":45,"topicOption":"疼痛"}
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            headers['Content-Type'] = 'application/json'
            response = http2_client_obj.send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/word_match', headers, {"topicId":topic_id,"topicOption":topic_option})
            response_json = response.json()['data']
            # 刷新
            while True:
                # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
                time_long = int(time.time() * 1000)
                headers = getHeaders('$social', cookie, time_long, index = 1)
                response = http2_client_obj.send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
                data = response.json()['data']
                if data['needCompletedTopicList'] is not None:
                    break
                time.sleep(1)
            
            cnt = data['mine']['finishCount']
            yield (f'完成第{cnt}次{response_json} <br>')
            if response_json['credit'] > 0:
                yield (f'铜板+{response_json["credit"]} <br>')
                time.sleep(0.5)
        except Exception as e:
            yield (f'{name} {e}')
            time.sleep(1)
    yield (f'{name} 每周双人战结束 <br>')

    if data['status'] == 3:# 结束
        if data['wordMatchReward']['status'] == 0:
            # https://social.baicizhan.com/api/deskmate/game/send_word_match_reward
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            headers['Content-Type'] = 'application/json'
            response = http2_client_obj.send_http2_request('POST',f'https://{headers["Host"]}/api/deskmate/game/send_word_match_reward', headers, {})

            # 检验是否领取成功
            # https://social.baicizhan.com/api/deskmate/game/get_word_match_info
            time_long = int(time.time() * 1000)
            headers = getHeaders('$social', cookie, time_long, index = 1)
            response = http2_client_obj.send_http2_request('GET',f'https://{headers["Host"]}/api/deskmate/game/get_word_match_info', headers, None)
            data = response.json()['data']
            if data['wordMatchReward']['status'] == 1:
                yield ('00 每周双人战奖励领取成功 <br>')
            else:
                yield ('01 领取失败 <br>')
        else:
            yield ('02 奖励已领取 <br>')
    else:
        yield ('03 等待同桌完成 <br>')


def get_class_range(user_config, total_user_cnt, max_rank_cnt = 1000):
    user_index = int(user_config['user_index'])
    # 获取今日日期
    # today = datetime.datetime.now().strftime('%Y%m%d')
    # 获取日期最后一位
    # date_last_num = int(today[-1])
    # date_last_num = 0
    # 将这100个班级分成total_user_cnt份
    cnt = max_rank_cnt / total_user_cnt
    num_start = int(cnt * (user_index) + 1)
    num_end = int(cnt * (user_index + 1) )
    if user_index == total_user_cnt - 1:
        num_end = max_rank_cnt
    # 组成班级范围
    # num_start += date_last_num * 100
    # num_end += date_last_num * 100
    # 限制班级范围防止一次性获取过多
    if num_end - num_start > 30:
        num_end = num_start + 30
    return num_start, num_end

def task_center(user_cookie, user_config, http2_client_obj: http2_client, daka_list_obj: daka_list_class, word_cnt=10, react_wait_seconds=1):
    # 获取不断电和学习分排行榜
    client_date = int(datetime.datetime.now().strftime('%Y%m%d'))
    def daily_summary_desc(client_date):
        # https://learn.baicizhan.com/api/study/win-streak/dailySummary?clientDate=20240817
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/dailySummary?clientDate={client_date}', headers, None)
        return response.json()
    
    
    data = daily_summary_desc(client_date)['data']
    score = data['score']
    if score is None:
        yield '还未打卡'
        score = 0
    rank = data['rank']
    win_streak_days = data['winStreakDays']
    if rank is None:
        raise Exception('学习记录异常')
    rank = rank['level']
    level_in_rank = 1
    for person in data['rank']['rankList']:
        if person.get('score', 0) > score:
            level_in_rank += 1
    if win_streak_days == 0:
        daka_list_obj.add_warning(f"用户{user_config['name']}的不断电上传失败，请注意")
    yield f'{win_streak_days}天<br>学习分{score}排{rank}段第{level_in_rank}名'
    time.sleep(react_wait_seconds)

    def get_monthly_task_desc():
        # https://social.baicizhan.com/api/task/v2/getOneUnEndTask
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/task/v2/getOneUnEndTask', headers, None)
        return response.json()
    
    monthly_task_data = get_monthly_task_desc()['data']
    if monthly_task_data is None:
        progress = total = 'null'
    else:
        progress = monthly_task_data.get('progress', 'null')
        total = monthly_task_data.get('actionCnt', 'null')
    
    # yield f' 新任务{progress}/{total}'


    # 前往任务中心领取奖励
    def get_award(user_task_id, task_award_list):
        # https://social.baicizhan.com/api/task/v2/getAward?userTaskId=1631594
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/json'
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/task/v2/getAward?userTaskId={user_task_id}', headers, content = {})
        data = response.json()
        if data.get('code', 0) == 1:
            return get_award_str(task_award_list)
        else:
            return f'失败{data.get("msg", "")}'
        
    def get_award_str(award_list):
        award_str = ''
        for award in award_list:
            award_str += f'{award["type"]}+{award["cnt"]} '
        return award_str

    def get_task_center_reward_desc(user_cookie, user_config):
        # https://social.baicizhan.com/api/task/v2/home
        user_study_ = user_study(http2_client_obj)
        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/task/v2/home', headers, None)
        data = response.json()['data']
        yield "任务中心：<br>"
        for task in data['taskList']:
            task_id = task['userTaskId']
            task_name = task['taskName']
            task_type = task['taskType']
            task_progress = task['progress']
            task_action_cnt = task['actionCnt']
            yield f'#{task_type}.{task_name}{task_progress}/{task_action_cnt} '
            payload = [
                {"index": 28, "extra_info": "{\"task_id\":%d}" % task_id}
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
            
            if task['status'] == 1:
                yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
            elif task['status'] == 0:
                if task_name == '加量学5个单词':
                    time.sleep(1.5)
                    user_study_.user_study_upload_task_action(user_cookie=user_cookie, user_config=user_config, task_upload_req_list=[['learnMore', 5]])
                    time.sleep(3)
                    yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
                elif '单词PK' in task_name and '3' in task_name:
                    for msg in pkonline2(user_cookie, user_config, http2_client_obj, daka_list_obj, max_round=8, max_win_round=3):
                        yield msg
                    time.sleep(1.5)
                    yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
                elif '单词PK' in task_name and '1' in task_name:
                    for msg in pkonline2(user_cookie, user_config, http2_client_obj, daka_list_obj, max_round=8, max_win_round=1):
                        yield msg
                    time.sleep(1.5)
                    yield f"领取{get_award(task['userTaskId'], task['awardList'])}<br>"
                elif task_name == '单词速听复习10个单词':
                    time.sleep(1.5)
                # elif task_name == '完成今日学习计划':

                # elif taskname == '完成1局单词消消练':
                # 因为要花费50铜板，因此不做处理
                else:
                    yield '<br>'
            else:
                yield '<br>'
                # 其他还没记录，先返回描述供开发
            # status == 2：任务已完成，奖励已领取
    
    
    if progress != 'null' and total != 'null':
        # 前往任务中心领取奖励
        time.sleep(react_wait_seconds)
        for msg in get_task_center_reward_desc(user_cookie, user_config):
            yield msg


    payload=[
        {"index": 16, "extra_info": "{\"word_num\":%d,\"experience\":%d}" % (word_cnt, score)} # 数据上传完成标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)

def sleep_actual(sleep_seconds):
    sleep_seconds *= 0.9
    index = random.randint(1, 100)
    if index < 5:
        time.sleep(sleep_seconds * index)
    time.sleep(sleep_seconds + index * 0.001)
    return

def learn_words(user_cookie, user_config, http2_client_obj: http2_client, daka_list_obj: daka_list_class, react_wait_seconds=1, word_count=5):
    unique_id = user_config['unique_id']
    
    yield f'{user_config["book_id"]}书'
    client_date = int(datetime.datetime.now().strftime('%Y%m%d'))
    user_study_ = user_study(http2_client_obj)

    def get_credit_status_desc(client_date):
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        url = f'https://{headers["Host"]}/api/study/xMode/getCreditStatus?date={client_date}'
        response = http2_client_obj.send_http2_request('GET', url, headers, None)
        result = response.json()
        if result['code'] == 1:
            return result['data']['inExperiment'], result['data']['studyCreditObtained'], result['data']['reviewCreditObtained']
        return False, False, False
    
    iE, sCO, rCO = get_credit_status_desc(client_date)
    if not iE:
        yield '没有拼写奖励 '
    elif sCO and rCO:
        yield '所有拼写奖励已领取 '
        
    # if (iE and (not sCO or not rCO)) or not today_daka:
    # 开始新学5个单词
    book_finished = False
    book_id = user_config['book_id']
    learnt_list = get_learnt_list(unique_id)
    learn_list = getRandomWordIDInBook('lookup.db', book_id, word_count, learnt_list)
    if (len(learn_list) < word_count):
        if len(learnt_list) == 0:
            yield '<p style="color:red;background-color:yellow">没有书本数据，请添加或更换书本</p>切换到#410'
            book_id = 410
            learn_list = getRandomWordIDInBook('lookup.db', book_id, word_count, [])
            word_count = len(learn_list)
        else:
            book_finished = True
            yield '<p style="color:red;background-color:yellow">新词不足 重新学习本书或更换书本</p>切换到#410'
            book_id = 410
            learn_list = getRandomWordIDInBook('lookup.db', book_id, word_count, [])
            word_count = len(learn_list)
    else:
        add_learnt_list(unique_id, learn_list)
    yield f'本次{word_count}个词<br>'
    
    learnt_count = 0
    yield f'完成新学轮数：'
    for strategy_id in range(1, 4): # 图选、英选中、中选英
        for i in range(word_count):
            
            
            '''choice_topic_id -1斩,null拼写,其他正常'''
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], strategy_id)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            sleep_actual(1)
            
            # 选择单词
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":%d,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], strategy_id, learn_list[i])},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            learnt_count += 1
            if learnt_count == 5:
                # 上传win_streak_status
                yield str(user_study_.user_study_submit_win_streak_records(user_cookie=user_cookie, user_config=user_config, client_date=client_date))
                # 疑似bug：user_study_submit_win_streak_records的client_date有默认值，但这个默认值可能是程序启动时的时间，导致跨天的打卡失败
            sleep_actual(react_wait_seconds)
            if strategy_id == 1:
                payload = [
                    {"index": 9, "extra_info": "{\"topic_id\":%d,\"book_id\":%d,\"channel\":\"study_mainstream\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], user_config['book_id'])}
                ]
                report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
                # 学习单词
                sleep_actual(1)
            yield '.'
        yield f'{strategy_id}'

    def daka_desc(word_count: int, unique_id: str, client_date: str):
        # 根据用户unique_id计算一个固定的timedelta，范围-1000s到0
        time_long = int(time.time() * 1000) - (int(hashlib.md5(str(unique_id).encode('utf-8')).hexdigest(), 16) % 1000000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/x-www-form-urlencoded'
        http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/study/xMode/daka', headers, f'date={client_date}&count={word_count}')
        
    daka_desc(word_count, unique_id, client_date)
    # 拼写
    payload = [
        {"index": 10}# 开始拼写标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
    for i in range(word_count):
        payload = [
            {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], 4)},
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        sleep_actual(3.6)
        payload = [
            {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":null,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (learn_list[i], 4)},
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        time.sleep(react_wait_seconds)
        yield '.'
        
    def receive_credit_desc(type: int, client_date: str):# 1 新学，2 复习
        type_str = 'study' if type == 1 else 'review'
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/study/xMode/receiveCredit?date={client_date}&type={type_str}', headers, None)
        result = response.json()
        return result['data']
    
    if iE and not sCO:
        yield f'拼写铜板x{receive_credit_desc(1, client_date)}<br>'
    else:
        yield '拼写完成<br>'

    payload=[
        {"index": 11}# 拼写完成标志
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
    payload=[
        {"index": 12}# 复习过渡页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)   
    time.sleep(react_wait_seconds)
    payload=[
        {"index": 13}# 复习过渡页点击
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)

    # 复习列表是今天学过的+昨天的单词，昨天的复习时斩掉
    yield '开始复习 '

    yesterday_list = get_history_learnt_list(unique_id, delta=1)
    the_day_before_list = get_history_learnt_list(unique_id, delta=2)
    review_count = len(yesterday_list)+len(the_day_before_list)
    yield f'共{review_count}个单词<br>'

    review_wrong_cnt = 0
    if review_count > 0:
        payload=[
            {"index": 14}# 复习开始
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
        
        # 复习选择题
        yield '复习选择'
        for word in yesterday_list:
            # 昨天的单词：复习
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            sleep_actual(1)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":%d,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 2, word)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            time.sleep(react_wait_seconds)
            yield '.'
        
        yield ' 前天'
        for word in the_day_before_list:
            # 前天的单词：斩掉
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            sleep_actual(1)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":-1,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 2)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            time.sleep(react_wait_seconds)
            yield '.'

        # 复习拼写
        def save_study_record_desc(topic_id: int, book_id: int, sleep_time_ms: int, wrong=False):
            time_long = int(time.time() * 1000)
            headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
            headers['Content-Type']= 'application/json'
            payload = {}
            if wrong:
                payload = {
                    "bookId": int(book_id),
                    "topicId": int(topic_id),
                    "spellWrongTimes" : 1
                }
            else:
                payload = {
                    "bookId": int(book_id),
                    "topicId": int(topic_id),
                    "costMilliseconds": int(sleep_time_ms)
                }
            response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/study/xMode/saveStudyRecord', headers, content=payload)
            
        yield ' 复习拼写'
        for word in yesterday_list:
            # 昨天的单词：拼写
            payload = [
                {"index": 7, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"plan_type\":\"XModelNewStudy\"}" % (word, 4)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            sleep_time = (random.randint(3000, 6000) / 1000)
            if random.randint(1, 5) == 1:
                # 错题
                review_wrong_cnt += 1
                time.sleep(sleep_time)
                save_study_record_desc(word, user_config['book_id'], sleep_time * 1000, wrong=True)
                yield '`'
                extra_sleep_time = random.randint(3000, 5000) / 1000
                time.sleep(extra_sleep_time)
                save_study_record_desc(word, user_config['book_id'], (extra_sleep_time + sleep_time) * 1000)
            else:
                time.sleep(sleep_time)
                save_study_record_desc(word, user_config['book_id'], sleep_time * 1000)
            payload = [
                {"index": 8, "extra_info": "{\"topic_id\":%d,\"strategy_id\":\"q%d\",\"choice_topic_id\":null,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}" % (word, 4)},
            ]
            report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
            time.sleep(react_wait_seconds)
            yield '.'

        # 复习完成
        daka_desc(word_count + review_count, unique_id, client_date)
        if iE and not rCO:
            yield f' 复习铜板x{receive_credit_desc(2, client_date)} '
        else:
            yield ' 复习完成 '
        payload=[
            {"index": 15}# 复习完成标志
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)
    
    def win_streak_status_desc() -> bool:
        # https://learn.baicizhan.com/api/study/win-streak/status
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/study/win-streak/status', headers, None)
        return response.json()['data']
    

    if win_streak_status_desc():
        yield  '连胜'
    else:
        yield '连胜上传失败'
    
    def report_finish_daily_plan_desc(book_id, new_words_count, total_words_count, book_finished):
        # https://learn.baicizhan.com/api/study/reportFinishDailyPlan
        time_long = int(time.time() * 1000)
        payload = {
            "bookId": int(book_id),
            "totalWordsCount": int(total_words_count),
            "newWordsCount": int(new_words_count),
            "bookFinished": 'true' if (book_finished) else 'false'
        }
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/json'
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/study/reportFinishDailyPlan', headers, content = payload)
        return response.json()
    
    report_finish_daily_plan_desc(user_config['book_id'], word_count, word_count + review_count, book_finished)

    word_done_data = {}
    for i in learn_list:
        word_done_data[i] = {
            "current_score": 3,
            "span_days": 0,
            "used_time": 0,
            "done_times": 4,
            "wrong_times": 0,
            "is_first_do_at_today": 1,
            "tag_id": 0,
            "spell_score": 3,
            "listening_score": 4,
            "chn_score": 3,
            "review_round": 0
        }
    # 数据收集非常水，span_days等等好几个字段都是废弃的
    for i in yesterday_list:
        word_done_data[i] = {
            "current_score": 5,
            "span_days": 0,
            "used_time": 0,
            "done_times": 4,
            "wrong_times": 0,
            "is_first_do_at_today": 0,
            "tag_id": 0,
            "spell_score": 3,
            "listening_score": 7,
            "chn_score": 3,
            "review_round": 0
        }
    for i in the_day_before_list:
        word_done_data[i] = {
            "current_score": 6,
            "span_days": 0,
            "used_time": 0,
            "done_times": 4,
            "wrong_times": 0,
            "is_first_do_at_today": 0,
            "tag_id": 0,
            "spell_score": 3,
            "listening_score": 7,
            "chn_score": 3,
            "review_round": 0
        }
    user_study_.user_study_submit_experience_record(user_cookie=user_cookie, user_config=user_config, word_count=word_count, wrong_count=0, review_count=review_count, review_wrong_count=review_wrong_cnt)
    user_study_.user_study_update_done_data(user_cookie=user_cookie, user_config=user_config, done_data=word_done_data)
    user_study_.user_study_user_daka_v2(user_cookie=user_cookie, user_config=user_config)


    time.sleep(react_wait_seconds)
    yield ' 分享中.'
    # 返回首页去打卡
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=0)
    # 获取打卡背景图
    result = user_study_.get_daka_background_datas(learn_list, user_cookie=user_cookie, user_config=user_config)
    poster_id = result.category_info[0].image_ids[0]
    

    payload=[
        {"index": 17},# 点击去打卡
        {"index": 18, "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\"}" % poster_id},# 访问打卡页面
        {"index": 0}# heartbeat
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=0)
    time.sleep(react_wait_seconds)
    yield '.'
    
    payload=[
        {"index": 19},# 点击分享到微信
        {"index": 20, 'extra_info': "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\", \"share_channel\":\"weixin\"}" % poster_id}# 点击打卡
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=0)
    time.sleep(react_wait_seconds)
    yield '.'
    if social_send_share_success(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, channel=1):
        yield '分享成功'
    result = user_study_.user_study_share_bonus(user_cookie=user_cookie, user_config=user_config)
    yield f'奖励+{result.coinCount}'
    time.sleep(react_wait_seconds)

    # 返回主页
    payload=[
        {"index": 21, "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"%d\",\"share_channel\":\"weixin\"}" % poster_id}# 返回首页
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=0)
    yield ' 学习结束<br>'

    for msg in task_center(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, daka_list_obj=daka_list_obj, word_cnt=word_count + review_count):
        yield msg

def get_leader_info(members):
    for member in members:
        if member['leader'] == True:
            return member['uniqueId'], member['nickname']
    return None, None


def check_study_cheat(date_str, members, user_cookie, http2_client_obj: http2_client, daka_list: daka_list_class) -> bool:
    '''在获取小班信息时，检查是否有刷词嫌疑并进行举报（爆破）'''
    need_recheck = False
    for member in members:
        if member['todayStudyCheat']:
            daka_list.track_cheat_user(date_str, member['uniqueId'], member['todayWordCount'], member['completedTime'], 1) # 1表示刷词，0表示认真学
            continue
        if member['todayWordCount'] > 500: # 如果用户已被跟踪，则已经举报过，证明是认真学的
            if daka_list.user_tracked(member['uniqueId']):
                # 已经举报过，证明不是刷词
                print(f'用户{member["uniqueId"]}\033[1;32m已举报过，不是刷词\033[0m')
                continue
            # https://group.baicizhan.com/group/user_report
            # {"reportModule":203,"reportReason":4,"reportTarget":{"uniqueId":...}}
            payload = {
                "reportModule": 203,
                "reportReason": 4,
                "reportTarget": {
                    "uniqueId": member['uniqueId']
                }
            }
            headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
            headers['Content-Type']= 'application/json'
            time.sleep(random.randint(14, 28)/10)
            response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/group/user_report', headers, content=payload)
            print(f'用户{member["uniqueId"]}\033[1;33m疑似刷词{member["todayWordCount"]}个\033[0m，已举报')
            daka_list.track_cheat_user(date_str, member['uniqueId'], member['todayWordCount'], member['completedTime'], 0)
            need_recheck = True
    return need_recheck

def notice_and_rank(user_cookie, user_config, http2_client_obj: http2_client, total_user_cnt, daka_list: daka_list_class, target_rank):
    '''获取公告和排名'''
    VERBOSE = True
    yield str(target_rank)
    if DEBUG:
        if user_config['user_index'] >= DEBUG_SIZE:
            time.sleep(10)
            return
    # https://group.baicizhan.com/group/get_group_rank?rank=7
    target_class_list = daka_list.get_class_list(target_rank, user_cookie)

    # https://group.baicizhan.com/group/information?shareKey=
    class_rank_start, class_rank_end = get_class_range(user_config, total_user_cnt, len(target_class_list))
    if DEBUG:
        lock.acquire()
        # class_rank_end = class_rank_start
        yield '⚠️ WARNING: DEBUG MODE (only the first class will be obtained)<br>'

    data_list = []
    recheck_data_index = []
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    for i in range(class_rank_start, class_rank_end + 1):
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        try:
            share_key = target_class_list[i - 1]['shareKey']
            response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/information?shareKey={share_key}', headers, None)
            response_json = response.json()

            group_info = response_json['data']['groupInfo']
            group_info['weekDakaDays'] = target_class_list[i - 1].get('weekDakaDays')
            group_info['members'] = response_json['data']['members']

            if not DEBUG and check_study_cheat(date_str, group_info['members'], user_cookie, http2_client_obj, daka_list):
                # （调试模式不检查，防止重复举报）如果有新的刷词记录，则需要一段时间后重新检查
                recheck_data_index.append(i)

            # 下面进行预处理，减少在lock过程中的时间
            group_info['score'] = target_class_list[i - 1].get('score')
            if group_info['notice'] is None or group_info['notice'] == '':
                group_info['notice'] = '(空)'
            # group_info['hash_value'] = hashlib.md5(group_info['notice'].encode('utf-8')).hexdigest()
            group_info['leader_id'], group_info['leader_name'] = get_leader_info(group_info['members'])
            data_list.append(group_info)
            if VERBOSE:
                print(f'{target_rank}.{i}.{group_info["name"]}<br>')
            if DEBUG:
                print(f'WARNING: \033[1;31mDEBUG MODE\033[0m<br>')
        except Exception as e:
            err_str = f'''❌ → 获取到{target_rank}段排名{i}的班级列表失败，请检查网络或排名是否存在\nrange=({class_rank_start}, {class_rank_end}, {len(target_class_list)}\n{traceback.format_exc()}'''
            print(err_str)
            yield err_str
        time.sleep(random.randint(25, 35) / 10)

    time.sleep(2)
    for i in recheck_data_index:
        # 重新检查刷词记录
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        try:
            share_key = target_class_list[i - 1]['shareKey']
            response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/information?shareKey={share_key}', headers, None)
            response_json = response.json()
            group_info = response_json['data']['groupInfo']
            group_info['weekDakaDays'] = target_class_list[i - 1].get('weekDakaDays')
            group_info['members'] = response_json['data']['members']
            if not DEBUG and check_study_cheat(date_str, group_info['members'], user_cookie, http2_client_obj, daka_list):
                # （调试模式不检查，防止重复举报）如果有新的刷词记录，则需要一段时间后重新检查
                recheck_data_index.append(i)
            group_info['score'] = target_class_list[i - 1].get('score')
            # 下面进行预处理，减少在lock过程中的时间
            if group_info['notice'] is None or group_info['notice'] == '':
                group_info['notice'] = '(空)'
            # group_info['hash_value'] = hashlib.md5(group_info['notice'].encode('utf-8')).hexdigest()
            group_info['leader_id'], group_info['leader_name'] = get_leader_info(group_info['members'])
            data_list[i - class_rank_start] = group_info
            if VERBOSE:
                print(f'2> {target_rank}.{i}.{group_info["name"]}<br>')
        except :
            err_str = f'''❌ → (二次获取)获取到{target_rank}段排名{i}的班级列表失败，请检查网络或排名是否存在\nrange=({class_rank_start}, {class_rank_end}, {len(target_class_list)}\n{traceback.format_exc()}'''
            print(err_str)
            yield err_str
        time.sleep(random.randint(25, 35) / 10)

    if VERBOSE:
        print(f'🌟 → 开始储存数据')
    daka_list.wait()
    
    data_time = int(datetime.datetime.now().timestamp())
    today_date_datetime = datetime.datetime.now() # 不用%m%d是为了方便计算start_date，不用%m%d%Y是为了方便strptime
    today_date = int(today_date_datetime.strftime('%Y%m%d')) # MEMBERS_GROUPS表的日期字段
    today_date_mmdd = int(today_date_datetime.strftime('%m%d')) # MEMBERS表的日期字段
    # 暂不再保存班级排名信息
    # if rank_type == 7 or rank_type == 6:
    #     # 对第六段位，只保存前100名
    #     if rank_type == 6:
    #         class_list = class_list[:100]
    #     for i, class_item in enumerate(class_list):
    #         class_share_key = class_item['shareKey']
    #         class_name = class_item['groupName']
    #         class_score = class_item['score']
    #         cursor.execute(f"INSERT OR IGNORE INTO notice (SHARE_KEY, NAME, RANK_TYPE, RANK, HASH_VALUE, CONTENT, DATE, SCORE) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    #                             (class_share_key, class_name, rank_type, i + 1, '', '', time.strftime('%Y-%m-%d %H-%M-%S', time.localtime()), class_score))
    #     if VERBOSE:
    #         print(f'★ → 获取到排名{rank_type}的班级列表\n')  
    #     yield f'★{rank_type}'

    current_rank = target_rank * 1000 + class_rank_start
    for i, group_info in enumerate(data_list):
        class_name = group_info['name']
        group_id = group_info['id']
        content = group_info['notice']
        introduction = group_info['introduction']
        share_key = group_info['shareKey']
        avatar = group_info['avatar']
        score = group_info['score']
        members = group_info['members']
        leader_id, leader_name = group_info['leader_id'], group_info['leader_name']
        daka_count = 0
        for member in members:
            if member['completedTime'] > 0:
                daka_count += 1
            daka_list.store_member(member['uniqueId'], group_id, member['completedTime'], today_date, today_date_mmdd, today_date_datetime, member['todayWordCount'], member['todayStudyCheat'], member['completedTimes'], member['durationDays'], member['bookName'], member['nickname'], member['avatar'])

        # hash_value = group_info['hash_value']
        # 检查GROUP_NAME表中是否有这个班级
        daka_list.store_group_info(group_id, share_key, leader_id, class_name, introduction, avatar)
        if target_rank == 2048: # 关注小班，额外储存一些信息
            daka_list.store_group_rank(today_date, group_id, daka_count, group_info['finishingRate'])
        status = daka_list.store_notice(group_id, current_rank, content, data_time, score, group_info['weekDakaDays'])
        if status == 0:
            if VERBOSE:
                print(f'🤔 → 检查！排名{i + class_rank_start}的班级{class_name}的公告被清空')
            yield '+'
        elif status == -1:
            if VERBOSE:
                print(f'😒 → 偷懒，排名{i + class_rank_start}的班级{class_name}的公告还是空的')
            yield '-'
        elif status == -2:
            if VERBOSE:
                print(f'😓 → 可惜，排名{i + class_rank_start}的班级{class_name}的公告被清空，但没有记录')
        elif status == 1:
            if VERBOSE:
                print(f'❤️ → 获取到排名{i + class_rank_start}的班级{class_name}的通知')
            yield '.'
        elif status == 2:
            if VERBOSE:
                print(f'🙈 → 排名{i + class_rank_start}的班级{class_name}的通知已存在数据库，跳过')
            yield '`'
        
        current_rank += 1

    if DEBUG:
        lock.release()


def watch_daily_sentences(user_cookie, user_config, http2_client_obj:http2_client):
    '''观看每日句子精讲'''
    # https://learn.baicizhan.com/api/activity/sentence/list
    headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
    headers['Content-Type']= 'application/json'
    response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/activity/sentence/list', headers, content={"size":20})
    data = response.json()['data']['data']
    for sentence in data:
        sentence_id = sentence['id']
        daka_num = sentence['dakaNum']
        cn = sentence['sentence']['cn']
        en = sentence['sentence']['en']
        sentence_source = sentence['sentenceSource']
        yield f'句子精讲 #{sentence_id} {daka_num}打卡'
        if user_config['user_index'] == 0:
            yield f'<br>{cn}<br>{en}<br>{sentence_source}'
        # https://learn.baicizhan.com/api/activity/sentence/sentence_daka
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        headers['Content-Type']= 'application/json'
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/activity/sentence/sentence_daka', headers, content = {"sentenceId":sentence_id})
        if response.json()['code'] == 1:
            yield ' 打卡成功 '
        # https://learn.baicizhan.com/api/activity/sentence/detail?sentenceId=882
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/activity/sentence/detail?sentenceId={sentence_id}', headers, None)
        if response.json()['code'] == 1:
            yield '获取详情成功<br>'
        break
    return

# imported from shadlc_BCZ_Group_Manager/src/bcz.py
def getGroupInfo(share_key: str, user_cookie, http2_client_obj:http2_client) -> dict:
    '''获取【班内主页】信息group/information'''
    # https://group.baicizhan.com/group/information
    headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
    main_response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/information?shareKey={share_key}', headers, None)
    if main_response.status_code != 200 or main_response.json().get('code') != 1:
        msg = f'使用主授权令牌获取分享码为{share_key}的小班信息失败! 小班不存在或主授权令牌无效'
        print(f'{msg}\n{main_response.text}')
        return {
            'share_key': share_key,
            'exception': main_response.text,
        }
    return main_response.json()['data']
    
# imported from shadlc_BCZ_Group_Manager/src/bcz.py
def setGroupOnlyInviteCodeJoin(share_key: str, user_cookie: str, http2_client_obj:http2_client) -> str:
    '''设置小班仅允许邀请码加入'''
    try:
        if getGroupInfo(share_key, user_cookie, http2_client_obj)['groupInfo']['onlyPublicKeyJoin']:
            return '已设置仅邀请<br>'
    except: # 无效的小班
        return 'INVALID'

    headers = getHeaders('$group', user_cookie, int(time.time()), index=1)
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    # https://group.baicizhan.com/group/set_only_public_key_join?shareKey=
    response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/group/set_only_public_key_join?shareKey={share_key}', content={}, headers=headers)
    if response.json().get("code",0) != 1:
        return (f"切换小班是否仅允许邀请码加入失败，请检查{response.json()}<br>")
    return (f"<span style='color:green'>切换小班是否仅允许邀请码加入成功</span><br>")

def get_own_bronze_groups_share_key(user_cookie, http2_client_obj:http2_client) -> list:
    '''获取自己的青铜小班分享码'''
    # https://group.baicizhan.com/group/own_groups?uniqueId=0
    headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
    response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/own_groups?uniqueId=0', headers, None)
    if response.status_code != 200 or response.json().get('code') != 1:
        msg = f'获取自己的青铜小班分享码失败! 请检查{response.text}'
        print(f'{msg}\n{response.text}')
        return []
    result = []
    data = response.json()['data']
    for group in data['list']:
        if group['rank'] == 1 and group['leader']:
            result.append(group['shareKey'])
    return result

def notice_checker(daka_list: daka_list_class, user_cookie, user_config, http2_client_obj:http2_client):
    '''检查通知'''
    message_str = ''
    if not user_config.get('check_notice', False):
        return
    own_groups_share_key = get_own_bronze_groups_share_key(user_cookie, http2_client_obj)
    print(f'{user_config["name"]}的青铜小班分享码：{own_groups_share_key}')
    for group_share_key in own_groups_share_key:
        # 设置小班仅允许邀请码加入，防止被检查公告泄露
        tmp_str = setGroupOnlyInviteCodeJoin(group_share_key, user_cookie, http2_client_obj)
        if tmp_str == 'INVALID':
            daka_list.add_warning(f'{user_config["name"]}的小班{group_share_key}不存在，请检查配置')
        # 获取一个待检测的通知
        while True:
            item = daka_list.get_check_notice()
            if item == None:
                yield message_str + '没有待检测的通知<br>'
                return
            check_result = daka_list.check_notice(item['content']) # (posA, posB, result_str)
            if check_result[0] > -1:
                message_str += f'[已知][{item["group_id"]}][{item["date"]}] {check_result}<br>'
                item['content'] = f'[已知][{item["group_id"]}][{item["date"]}] {check_result[2]}'
                item['cursorA'] = check_result[0]
                item['cursorB'] = check_result[1]
                item['checked'] = 2
                daka_list.patch_check_notice(item)
            else:
                break
        

        content = item['content']
        message_str += f'待检测的通知：{item["group_id"]}-{item["date"]}<br>{content[:16]}<br>'
        yield message_str
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        payload = {
            "shareKey": group_share_key,
            "notice": content
        }
        # https://group.baicizhan.com/group/set_notice
        response_json = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/group/set_notice', content=payload, headers=headers).json()
        while response_json['message'] == '公告不能超过1000个字': # 可能是某些偶然bug导致略微超出1000，缩一下就好
            time.sleep(0.8)
            content = content[:-1]
            payload = {
                "shareKey": group_share_key,
                "notice": content
            }
            response_json = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/group/set_notice', content=payload, headers=headers).json()
        if response_json['message'] == None:
            message_str += f'通知发送成功<br>'
            yield message_str
            item['checked'] = 2
            daka_list.patch_check_notice(item)
        elif response_json['message'] == '小班公告每天只能修改一次':
            message_str += f'通知发送失败，{group_share_key}的公告每天只能修改一次<br>'
            yield message_str
            daka_list.patch_check_notice(item, modified=False)
        elif response_json['message'] == '小班公告内容涉嫌违规，请修改':
            acceptable = False
            content_accept_part = ''
            check_part = ''
            if item['checked'] == 0: # 倒找
                message_str += '小班公告内容涉嫌违规，请修改<br>'
                pace = 10
                while not acceptable:
                    # 将content最后的pace个字符加入到check_part
                    # if check_part == content[-pace:]: # 因为有可能重复字符是违规的，这样会概率跳过
                    #     content_accept_part = check_part + content_accept_part
                    #     content = content[:-pace]
                    #     continue
                    content_accept_part = check_part + content_accept_part
                    check_part = content[-pace:]
                    content = content[:-pace]
                    if re.sub(NoticeParser.pattern, '', check_part) == '': # 全是无效字符
                        continue
                    yield message_str + f'{content}<u>{check_part}</u><s>{content_accept_part}</s>'
                    # 发送content
                    payload = {
                        "shareKey": group_share_key,
                        "notice": content
                    }
                    headers = getHeaders('$group', user_cookie, time_long, index = 1)
                    headers['Content-Type'] = 'application/json; charset=UTF-8'
                    response_json = http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/set_notice', content=payload, headers=headers).json()
                    if response_json['message'] == None:
                        message_str += f'{response_json["message"]}<br>{content}<u>{check_part}</u><s>{content_accept_part}</s><br>'
                        yield message_str
                        acceptable = True
                        break
                    elif response_json['message'] != '小班公告内容涉嫌违规，请修改':
                        message_str += f'通知发送失败{response_json["message"]}<br>{content}<u>{check_part}</u><s>{content_accept_part}</s><br>'
                        yield message_str
                        break
                    # 随机延迟
                    time.sleep(random.randint(700, 1200) / 1000)
                if acceptable:
                    item['content'] = content + check_part # 可能还有问题的部分
                    item['cursorB'] = len(content) + pace # 记录当前位置
                    item['checked'] = 1
                    daka_list.patch_check_notice(item)
                else:
                    daka_list.patch_check_notice(item, modified=False)
            else:
                # 从前面往后找
                message_str += '小班公告内容涉嫌违规，请修改_reversed<br>'
                pace = 10
                while not acceptable:
                    # 将content最前的pace个字符加入到check_part
                    content_accept_part += check_part
                    if len(content) < pace*2: # 即将结束，缩小步长
                        pace = 1
                    check_part = content[:pace]
                    content = content[pace:]
                    yield message_str + f'<s>{content_accept_part}</s><u>{check_part}</u>{content}'
                    # 发送content
                    payload = {
                        "shareKey": group_share_key,
                        "notice": content
                    }
                    headers = getHeaders('$group', user_cookie, time_long, index = 1)
                    headers['Content-Type'] = 'application/json; charset=UTF-8'
                    response_json = http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/set_notice', content=payload, headers=headers).json()
                    if response_json['message'] == None:
                        message_str += f'{response_json["message"]}<br><s>{content_accept_part}</s><u>{check_part}</u>{content}<br>'
                        yield message_str
                        acceptable = True
                        break
                    elif response_json['message'] != '小班公告内容涉嫌违规，请修改':
                        message_str += f'通知发送失败{response_json["message"]}<br><s>{content_accept_part}</s><u>{check_part}</u>{content}<br>'
                        yield message_str
                        break
                    # 随机延迟
                    time.sleep(random.randint(700, 1200) / 1000)
                if acceptable:
                    item['content'] = check_part + content # 可能还有问题的部分
                    item['checked'] = 2
                    item['cursorA'] = len(content_accept_part) # 记录当前位置
                    daka_list.patch_check_notice(item)
                else:
                    daka_list.patch_check_notice(item, modified=False)
        else:
            message_str += f'通知发送失败{response_json["message"]}<br><br>'
            daka_list.patch_check_notice(item, modified=False)
            yield message_str
        time.sleep(1)


lock = threading.Lock()
def daka(daka_list: daka_list_class, user_cookie, user_config, http2_client_obj: http2_client, total_user_cnt=18, only_rank_and_notice=-1):
    '''为用户打卡'''
    response_wait_second = 0.3
    react_wait_second = 0.9
    time_start = time.time()
    unique_id = user_config['unique_id']
    
    if not daka_list.add(unique_id, only_rank_and_notice):
        return
    message_str = '#'
    client_date = int(datetime.datetime.now().strftime('%Y%m%d'))

    threading.Thread(target=heartbeat_demon, args=(daka_list, user_cookie, user_config, http2_client_obj)).start()

    # 临时函数放这里
    # for msg in notice_checker(daka_list, user_cookie, user_config,  http2_client_obj):
    #     yield msg
    # only_rank_and_notice = 0
    # for msg in pkonline2(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, daka_list=daka_list, max_round=1):
    #     message_str += msg
    #     yield message_str

    # daka_list.remove(unique_id)
    # return 
    # 临时函数放这里

    if only_rank_and_notice > -1:
        for msg in notice_and_rank(user_cookie, user_config, http2_client_obj, total_user_cnt, daka_list, only_rank_and_notice):
            message_str += msg
            yield message_str
        daka_list.remove(unique_id)
        return 
    
    for msg in watch_daily_sentences(user_cookie, user_config, http2_client_obj):
        message_str += msg
        yield message_str
    time.sleep(react_wait_second)

    for msg in deskmate_pk(cookie=user_cookie, config=user_config, http2_client_obj=http2_client_obj):
        message_str += msg
        yield message_str
    time.sleep(react_wait_second)

    # pk # 1
    if random.randint(0, 1) == 1:
        for msg in pkonline(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, daka_list = daka_list, max_round=3):
            message_str += msg
            yield message_str
        time.sleep(react_wait_second)

    yield yzdd(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, daka_list=daka_list)
    if user_config.get('only_yzdd', "False") == "True":
        return
    
    message_str += '<br>开始背单词<br>'
    yield message_str
    word_count = user_config.get('word_count', 5)
    for msg in learn_words(user_cookie, user_config, http2_client_obj, daka_list, react_wait_second, word_count):
        message_str += msg
        yield message_str
    time.sleep(react_wait_second)

    

    # 前往一起背领取打卡奖励
    def get_task_status_desc():
        
        # https://social.baicizhan.com/api/task/accept_task
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/task/accept_task', headers, {})

        # https://social.baicizhan.com/api/task/finish_task # 发一次空接收、完成请求以完成签到
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/task/finish_task', headers, {})
        
        #  https://group.baicizhan.com/group/study_words_together_home_page
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/group/study_words_together_home_page', headers, None)
        data = response.json()['data']

        # https://social.baicizhan.com/api/task/get_task_list
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/task/get_task_list', headers, None)
        tasklist = response.json()['data']['taskInfoVoList']
        state = 0
        daily_reward_obtained = True
        for task in tasklist:
            if task['showPriority'] == 1 and task['state'] == 1:
                daily_reward_obtained = False
            elif task['state'] == 1:
                    state += 1

        # https://social.baicizhan.com/api/deskmate/home_page
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/deskmate/home_page', headers, None)
        deskmate_data = response.json()['data']
        if deskmate_data is None or deskmate_data['deskmate'] is None:
            deskmate_daka_today = False
        else:
            deskmate_daka_today = deskmate_data['deskmate']['dakaToday']

        
        return data['haveDeskmate'], data['haveGroup'], data['haveOrdinaryGroup'], data['todayDaka'], data['receivedGroupRankRewards'], data['receivedGroupDailyRewards'], state, deskmate_daka_today, daily_reward_obtained
    
    have_deskmate, have_group, have_ordinary_group, today_daka, received_group_rank_rewards, received_group_daily_rewards, task_state, deskmate_daka_today, daily_reward_obtained = get_task_status_desc()
    if not today_daka:
        message_str += '打卡未同步 '
        time.sleep(5)
        have_deskmate, have_group, have_ordinary_group, today_daka, received_group_rank_rewards, received_group_daily_rewards, task_state, deskmate_daka_today, daily_reward_obtained = get_task_status_desc()
        if not today_daka:
            raise '打卡未同步'
        
    if task_state > 0:
        message_str += f'{task_state}任务请手领 '
        yield message_str

    def get_task_reward_desc(client_date):# 签到奖励

        # https://social.baicizhan.com/api/task/get_task_reward {"taskId":1,"receptionTime":20240817}
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        payload = {"taskId": 1, "receptionTime": client_date}
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/task/get_task_reward', headers, payload)
        return response.json()
    
    if not daily_reward_obtained and get_task_reward_desc(client_date)['code'] == 1:
        message_str += '签到+5 '
        yield message_str
        time.sleep(react_wait_second)

    
    def deskmate_daka_reward_desc(type):# 同桌打卡奖励
        # https://social.baicizhan.com/api/deskmate/daka_reward?type=1
        # 0自己；1同桌

        payload=[
            {"index": 22},# 点击领取同桌奖励(自己、同桌分别发送)
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)

        time_long = int(time.time() * 1000)
        headers = getHeaders("$social", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/api/deskmate/daka_reward?type={type}', headers, {})
        return response.json()['data']


    if have_deskmate:
        
        message_str += f'自己份+{deskmate_daka_reward_desc(0)} '
        yield message_str
        time.sleep(react_wait_second)

        if deskmate_daka_today:
            message_str += f'同桌份+{deskmate_daka_reward_desc(1)} '
            yield message_str
            time.sleep(react_wait_second)
        
    def class_reward_desc(type):# 班级奖励
        payload=[
            {"index": 23 + type},# 点击领取班级奖励
        ]
        report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=0)

        time_long = int(time.time() * 1000)
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        if type == 0:
            # https://group.baicizhan.com/group/open_box?surprise=0
            response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/group/open_box?surprise=0', headers, None)
        else:
            # https://group.baicizhan.com/group/receive_group_rank_award
            response = http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/group/receive_group_rank_award', headers, None)
        return response.json()['data']['count']

    if have_group and not received_group_daily_rewards:
        message_str += f'班级日签+{class_reward_desc(0)} '
        yield message_str
        time.sleep(react_wait_second)
        if have_ordinary_group and not received_group_rank_rewards:
            message_str += f'班级段位+{class_reward_desc(1)} '
            yield message_str
            time.sleep(react_wait_second)

    # 商城日奖



    def get_daily_shop_reward_desc(client_date, daka_list: daka_list_class):
        # https://learn.baicizhan.com/api/mall/proxy/homepage/get_home_page_info
        # 获取今日是否已领日奖
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/homepage/get_home_page_info', headers, None)
        try:
            daily_credit_status = response.json()['data']['dailyCreditStatus']
        except:
            daka_list.add_warning(f'{user_config.get("name", "未知")} 获取今日是否已领日奖失败{response.text}')
            daily_credit_status = True

        # https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit
        # 获取当前铜板数
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/creditmall/get_credit', headers, None)
        balance = response.json()['data']
        
        if not daily_credit_status:
            # https://learn.baicizhan.com/api/mall/proxy/homepage/get_daily_reward
            time_long = int(time.time() * 1000)
            headers = getHeaders("$learn", user_cookie, int(time.time()), index=1)
            response = http2_client_obj.send_http2_request('GET', f'https://{headers["Host"]}/api/mall/proxy/homepage/get_daily_reward', headers, None)
            return balance, response.json()['data']['credit']
        else:
            return balance, 0
    

    balance, daily_shop_reward_data = get_daily_shop_reward_desc(client_date, daka_list)
    message_str += f'<br>商城日奖+{daily_shop_reward_data} 现有{balance + daily_shop_reward_data} '
    yield message_str
    time.sleep(react_wait_second)
    user_config['cooper'] = balance + daily_shop_reward_data
    daka_list.update_user_dict({"cookie": user_cookie, "config": user_config})

    payload=[
        {"index": 25},# 点击
        {"index": 26} # 加载商城
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=0)
    payload=[
        {"index": 27},# heartbeat
    ]
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)
    time.sleep(react_wait_second)
    report_event(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, jsons=payload, type=1, host=1)

    # pk # 2
    for msg in pkonline(user_cookie=user_cookie, user_config=user_config, http2_client_obj=http2_client_obj, daka_list=daka_list, max_round=3):
        message_str += msg
        yield message_str

    # 前往个人中心
    user_study_ = user_study(http2_client_obj)
    result = user_study_.user_study_credit_task_center(user_cookie=user_cookie, user_config=user_config)
    message_str += f'今日+{result.daily_inc_credit} '
    yield message_str

    msg = ""
    for msg in notice_checker(daka_list, user_cookie, user_config, http2_client_obj):
        yield message_str + msg
    message_str += msg


    # 删除daka_list中的unique_id
    daka_list.remove(unique_id)

    message_str += f'耗时{time.time() - time_start:.2f}s'
    yield message_str

from src.gen import generate_random, exponential_with_constant, square_gaussian_with_constant
segments = [ # 用于拟合每天各时段打卡时间分布
    {"range": (0.0, 0.2), "function": exponential_with_constant, "params": [435, -65]},
    {"range": (0.2, 0.45), "function": square_gaussian_with_constant, "params": [888, 0.2972, 0.0205, -7624, 5541, -828]},
    {"range": (0.45, 0.65), "function": square_gaussian_with_constant, "params": [738, 0.5279, 0.0195, 746, -1003, 426]},
    {"range": (0.65, 0.85), "function": square_gaussian_with_constant, "params": [465, 0.7770, 0.0322, 22537, -27939, 8726]},
    {"range": (0.85, 1.0), "function": square_gaussian_with_constant, "params": [105, 0.9155, 0.0145, -195883, 353421, -157605]},
]
def daka_headless(daka_list: daka_list_class, user_cookie, user_config, http2_client_obj: http2_client, user_cnt, only_rank_and_notice, random_delay=1800):
    # 获取到今天0点的秒数
    today_seconds = (datetime.datetime.now() - datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0, 0))).total_seconds()
    user_index = user_config['user_index']
    name = user_config.get('name', '未知')
    delay = 0
    if random_delay <= 0 or user_index == 0:
        delay = 0
    elif name[-1] == '*':
        delay = random_delay # 强制最大延迟，可以用于测试或者用于固定账号使用
    else:
        delay = (int(generate_random(today_seconds / 86400, random_delay / 86400, segments) * 86400 - today_seconds) + random.randint(0, 100) / 10)
    
    unique_id = user_config.get('unique_id', '未知')
    try:
        message = f"{unique_id}#开始打卡:{name}，延迟{delay}s"
        print(message)
        yield message
    except:
        daka_list.add_warning(f'{name}链接中断 {traceback.format_exc()}')
        pass
    try:
        if delay < 0:
            daka_list.add_warning(f'{name} {delay} < 0')
        else:
            time.sleep(delay)
        for msg in daka(daka_list, user_cookie, user_config, http2_client_obj, total_user_cnt=user_cnt, only_rank_and_notice=only_rank_and_notice):
            message = msg
            yield message
    except AssertionError as e:
        daka_list.add_warning(f'{name}打卡中止 {e}')
        daka_list.remove(unique_id) # remove会触发自动保存，延迟中止速度
    except Exception as e:
        err_str = traceback.format_exc()
        message += f'<br>${name}打卡失败{e}<br>{err_str}'
        yield message
        daka_list.add_warning(message.replace('<br>', '\n'))
        daka_list.remove(unique_id)
    daka_list.add_log(datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S'), name, unique_id, f"延迟{delay}s后打卡\n{message}".replace('<br>', '\n'))

def generator_wrapper(messages: queue.Queue, unique_id: int, func, *args, **kwargs):
    try:
        for msg in func(*args, **kwargs):
            messages.put(('msg', unique_id, msg))
    except Exception as e:
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")} {unique_id} {e} {traceback.format_exc()}\n')
        messages.put(('err', unique_id, f'{e}'))

def daka_all_headless(user_messages: queue.Queue, daka_list: daka_list_class, http2_client_obj, only_rank_and_notice, user_dict_list=[], random_delay=1800):
    if user_dict_list == []:
        user_dict_list = daka_list.get_user_dict_list()
    user_cnt = len(user_dict_list)
    for user_dict in user_dict_list:
        if only_rank_and_notice == -1 and user_dict['config'].get('can_daka') == 0:
            continue
        threading.Thread(target=generator_wrapper, args=(user_messages, user_dict['config']['unique_id'], daka_headless, daka_list, user_dict['cookie'], user_dict['config'], http2_client_obj, user_cnt, only_rank_and_notice, random_delay)).start()


