import random
import datetime
import zipfile
import sqlite3
import logging
import statistics
import openpyxl
from openpyxl.chart import BarChart, Reference, LineChart, ScatterChart, Series
import json
import os
import re

DEBUG = False

def encoder(text):
    # 转化成bytearray类型
    input = bytearray(text.encode())
    
    for i in range(len(input)):
        # 将byte的后5位取反
        input[i] = input[i] ^ 0b00011111
        # ...
    return input

def decoder(text):
    input = bytearray(text)
    # 转化成bytearray类型
    for i in range(len(input)):
        # 将byte的后5位取反
        input[i] = input[i] ^ 0b00011111
    
    return input.decode()

bad_word_path = '../BCZ-Notice-Examiner/assets/bad_words.bin'
bad_words = []
if os.path.exists(bad_word_path):
    with open(bad_word_path, 'rb') as f:
        bin_data = f.read()
        bad_words = json.loads(decoder(bin_data))
warn_word_path = '../BCZ-Notice-Examiner/assets/warn_words.bin'
accept_word_path = '../BCZ-Notice-Examiner/assets/accept_words.bin'
accept_notice_path = '../BCZ-Notice-Examiner/accept_notice.txt'
bad_notice_path = '../BCZ-Notice-Examiner/bad_notice.txt'
year = datetime.datetime.now().year
member_info_path = '../BCZ-Notice-Examiner/assets/member/' # 要按照unique_id来处理
member_name_path = '../BCZ-Notice-Examiner/assets/member_name/'
member_info_top_rate_path = '../BCZ-Notice-Examiner/assets/js/member_info_top_rate.js'
member_info_top_rate_screen_path = '../BCZ-Notice-Examiner/assets/js/member_info_top_rate_screen.js'
member_info_top_name_path = "../BCZ-Notice-Examiner/assets/js/member_info_top_name.js"
groups_path = '../BCZ-Notice-Examiner/assets/groups.bin'
books_path = '../BCZ-Notice-Examiner/assets/books.bin'
default_notice_db_path = f'../BCZ-Notice-Examiner/bcz_notice.db'

black_list_path = '../BCZ-Notice-Examiner/blacklist.xlsx'
black_list_rating_path = '../BCZ-Notice-Examiner/blacklist_rating.json'
black_list_string_assets = '../BCZ-Notice-Examiner/assets/black_list_string.bin'

def set_invalid_storage(invalid_storage: dict, position, char, length=1):
    for i in range(position, position+length):
        if i not in invalid_storage:
            invalid_storage[i] = [char]
        else:
            invalid_storage[i].append(char)


replace_dict = {
    '一': '1',
    '二': '2',
    '三': '3',
    '四': '4',
    '五': '5',
    '六': '6',
    '七': '7',
    '八': '8',
    '九': '9',
    '零': '0',
    '壹': '1',
    '贰': '2',
    '叁': '3',
    '肆': '4',
    '伍': '5',
    '陆': '6',
    '柒': '7',
    '捌': '8',
    '玖': '9',
    '〇': '0',
}
pattern = r'[^\w\d\u4e00-\u9fa5\U0001F601-\U0001F64F\U00002702-\U000027B0\U0001F680-\U0001F6C0\U0001F170-\U0001F251\U0001F600-\U0001F636\U0001F681-\U0001F6C5\U0001F30D-\U0001F567]'
def slice_invalid_char(text: str):
    # 去除并存储无效字符的位置
    global pattern
    # invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）','-','—','_']
    invalid_storage = {}
    position = 0
    new_text = ""
    for char in text:
        
        if char in replace_dict:
            set_invalid_storage(invalid_storage, position, char)
            position += 1
            new_text += replace_dict[char]
        elif re.match(pattern, char) is not None:
            set_invalid_storage(invalid_storage, position, char)
        else:
            position += 1
            new_text += char
    return new_text, invalid_storage


def restore_invalid_char_unaccept(text: str, invalid_storage: dict):
    # 插入无效字符
    bad = False # 优先级从高到低
    accept = False
    warn = False
    new_text = ""
    for position in range(len(text)):
        if position in invalid_storage:
            min_char = "9"
            min_char_cnt = 0
            for char in invalid_storage[position]:
                if char.isdigit():
                    if char < min_char:
                        min_char = min(min_char, char)
                        min_char_cnt = 1
                    elif char == min_char:
                        min_char_cnt += 1
                else:
                    if char == "\n":
                        new_text += char
            if min_char == "1":
                continue
                new_text += '\033[31m'
                bad = True
            elif min_char == "2" and min_char_cnt > 1: # 必须要两次接受才是真的接受（代表双向）
                continue
                new_text += '\033[32m'
                accept = True
            elif min_char == "3":
                # new_text += '\033[33m'
                warn = True
            elif bad or accept or warn:
                # new_text += '\033[0m'
                bad = False
                accept = False
                warn = False
        if text[position] not in replace_dict:
            new_text += text[position]
    return new_text

def filter_string(text: str):
    # \w\d\u4e00-\u9fa5 数字字母和汉字
    global pattern
    

    filtered_string = re.sub(pattern, '', text)

    # 传统方式
    # invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）','~','*','@','～','【','】','《','》','[',']','%','％','=','\\','\t','|','<','>','#','『','』','^','…']
    invalid_chars = ['_','丨','✔']

    for char in invalid_chars:
        filtered_string = filtered_string.replace(char, '')
    return filtered_string

def parse_text(text: str) -> list:
    '''将文本解析长度为2的所有字串列表'''

    text = filter_string(text)

    for char in replace_dict:
        text = text.replace(char, replace_dict[char])
    result = []
    for i in range(len(text)-1):
        result.append(text[i])
        result.append(text[i] + text[i+1])
    if len(text) > 0:
        result.append(text[-1])
    return result

def splice_accepted_text(text: str, accept_words: set, bad_words: set) -> str:
    '''将文本中被接受两次的词汇去除'''
    text_set = set(parse_text(text))
    # 获取同时存在于text_set和accept_words中的词汇
    text_accept_set = text_set & accept_words
    valid_text, invalid_storage = slice_invalid_char(text)
    for word in text_accept_set:
        # print(f'accept word: {word}')
        try:
            temp_valid_input_str = valid_text
            pos = 0
            while True:
                # print(f'pos: {pos}')
                pos += temp_valid_input_str.index(word)
                temp_valid_input_str = valid_text[pos+len(word):]
                set_invalid_storage(invalid_storage, pos, f"2", length=len(word))   # 32m
                pos += len(word)
        except ValueError:
            pass

    for pattern in bad_words:
        try:
            temp_valid_input_str = valid_text
            pos = 0
            while True:
                pos += temp_valid_input_str.index(pattern)
                temp_valid_input_str = valid_text[pos+len(pattern):]
                set_invalid_storage(invalid_storage, pos, "1", length=len(pattern)) # 31m
                pos += len(pattern)
        except ValueError:
            pass
    return restore_invalid_char_unaccept(valid_text, invalid_storage)
    

def update_notice(conn: sqlite3.Connection):
    # 从数据库中读取所有通知
    cur = conn.cursor()
    cur.execute("SELECT SHARE_KEY, NAME, HASH_VALUE, CONTENT, DATE, LATEST_DATE FROM notice ORDER BY DATE DESC")
    notices = cur.fetchall()
    # 按照notices[][0](NAME字段)分类
    notice_dict = {}
    notice_date = {}
    most_recent_clear_date = "1970-01-01 00:00:00"
    # 最多只接受两周内的公告
    # least_valid_date = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime('%Y-%m-%d 00:00:00')
    for notice in notices:
        share_key = notice[0]
        notice_content = notice[3]
        date = notice[4]
        latest_date = notice[5]
        if latest_date is None:
            latest_date = date
        if share_key not in notice_dict:
            notice_dict[share_key] = []
            notice_date[share_key] = []
        notice_dict[share_key].append(notice_content)
        notice_date[share_key].append(latest_date)
        if notice_content.startswith('(空)') and date > most_recent_clear_date:
            most_recent_clear_date = date # 这里使用开始而不是最新日期
    # 遍历每个分类，找到公告被清空（以'(空)'开头）的那天
    print(f"most_recent_clear_date: {most_recent_clear_date}")
    most_recent_clear_date_ymd = most_recent_clear_date.split(' ')[0]
    warn_words = []
    accept_words = []
    accept_notice_list = []
    bad_notice_list = []
    for share_key, notice_list in notice_dict.items():
        notice_date_list = notice_date[share_key]
        index_time = ''
        for notice, date in zip(notice_list, notice_date_list):
            if date.startswith(most_recent_clear_date_ymd) and notice.startswith('(空)'): # 找到同一天的(空)的位置
                index_time = date
                break
        if index_time != '':
            for notice, date in zip(notice_list, notice_date_list):
                if date.startswith(most_recent_clear_date_ymd):
                    if date < index_time: # 同一天早些时候的公告
                        warn_words.extend(parse_text(notice))
                        bad_notice_list.append(notice)
                    elif date > index_time: # 同一天晚些时候的公告
                        accept_words.extend(parse_text(notice))
                        accept_notice_list.append(notice)
        else:
            # 公告都没有被清空，且是当天的公告，全部加入到accept_words中
            for notice, date in zip(notice_list, notice_date_list):
                if date.startswith(most_recent_clear_date_ymd):
                    accept_words.extend(parse_text(notice))
                    accept_notice_list.append(notice)
    # 去重
    warn_words = set(warn_words)
    accept_words = set(accept_words)
    # 从warn_words中去除accept_words
    warn_words = warn_words - accept_words # accept_words是确定合规的
    # 写入json文件
    print(f'warn_words: {len(warn_words)}')
    print(f'accept_words: {len(accept_words)}')
    print(f"accept_notice_list: {len(accept_notice_list)}")
    print(f"bad_notice_list: {len(bad_notice_list)}")
    accept_fuzz = '\n\\\\\n'.join(accept_notice_list)
    print(f'accept_fuzz: {len(accept_fuzz)}')
    bad_fuzz = splice_accepted_text('\n'.join(bad_notice_list), accept_words, bad_words)
    print(f'bad_fuzz: {len(bad_fuzz)}')
    def flatten(str):
        return str.replace(' ','')
    with open(warn_word_path, 'wb') as f:
        f.write(encoder(flatten("\n".join(list(warn_words)))))
    with zipfile.ZipFile(f"{warn_word_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(warn_word_path, arcname=warn_word_path)
        
    accept_words = list(accept_words)
    today_date = f"数据更新日期：{datetime.datetime.now().strftime('%Y-%m-%d')}"
    accept_words.insert(0, today_date)
    with open(accept_word_path, 'wb') as f:
        f.write(encoder(flatten("\n".join(accept_words))))
    with zipfile.ZipFile(f"{accept_word_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(accept_word_path, arcname=accept_word_path)
    with open(accept_notice_path, 'w', encoding='utf-8') as f:
        f.write(accept_fuzz)
    with open(bad_notice_path, 'w', encoding='utf-8') as f:
        f.write(bad_fuzz)

class member_storage_class:
    def __init__(self, logger = None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
        self.gross_daka_time_dict = {} # 统计近30天内，所有各分钟内的打卡人次（按日期%7归类）
        self.gross_daka_time_dict_7 = {} # 统计近7天内，所有单次打卡人次
        self.gross_daka_date = {} # 上面对应%7数的日期
        self.db_path = default_notice_db_path
        self.hash_dict = {}
        self.hash_index = 0

        self.word_count_period = 25 # 25词分一档
        self.time_count_period = 1800 # 30分钟分一档
        self.reserve_digits = 1000000 # 保留uid的最后6位
        self.rank_max_num = 100 # 排行榜最多显示前100名（允许同分）

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # 获取所有书本信息
        # HASH_ID, BOOK_NAME, BOOK_ID, BOOK_URL
        self.logger.info("正在初始化 书本信息")
        cur.execute("SELECT HASH_ID, BOOK_NAME FROM BOOK_NAME")
        self.book_dict = {}
        for book in cur.fetchall():
            self.book_dict[book[0]] = book[1]
        
        # 获取所有班级信息
        self.logger.info("正在初始化 班级信息")
        cur.execute("SELECT DISTINCT GROUP_ID, NAME FROM notice WHERE GROUP_ID IS NOT NULL ORDER BY DATE DESC")
        self.group_dict = {}
        for group in cur.fetchall():
            if group[0] in self.group_dict:
                continue
            if group[1] is None:
                self.group_dict[group[0]] = '无名小班'
            else:                
                self.group_dict[group[0]] = group[1].split('\n')[0].replace(' ', '\t') # 班名中可能有空格
                # 第二行是介绍，不需要
        self.logger.info("正在统计 成员信息条数")
        cur.execute("SELECT COUNT(*) FROM MEMBERS")
        cnt = cur.fetchone()[0]
        self.logger.info(f"成员信息条数：{cnt}")
        # 获取所有成员信息
        command = "SELECT USER_ID, NICKNAME, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_ID, STUDY_CHEAT FROM MEMBERS ORDER BY TODAY_DATE DESC"
        self.logger.info("正在初始化 成员信息")
        if DEBUG: # 苔泰！
            # command = "SELECT USER_ID, NICKNAME, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_ID, STUDY_CHEAT FROM MEMBERS WHERE USER_ID == 1141201181 OR USER_ID == 1584809188 OR USER_ID == 766773235 OR USER_ID == 1798946708 ORDER BY TODAY_DATE DESC"
            command = "SELECT USER_ID, NICKNAME, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_ID, STUDY_CHEAT FROM MEMBERS ORDER BY RANDOM() LIMIT 3000"
        cur.execute(command)
        # 按照USER_ID分类
        self.logger.info("正在分类 成员信息")
        self.member_name = {}
        member_name_date = {}
        self.members = {}
        processed_cnt = 0
        for member in cur:
            user_id = member[0]
            if user_id not in self.members:
                self.members[user_id] = []
            self.members[user_id].append(member)

            name = member[1]
            if name is not None and user_id not in self.member_name:
                self.member_name[user_id] = name.replace('\n','')
            processed_cnt += 1
            if processed_cnt % 100000 == 0:
                self.logger.info(f"已处理 {processed_cnt} 条成员信息")
            # 下面这个是没有排序的版本
            # today_name = member[1]
            # today_date = member[3]
            # if today_date is None:
            #     continue
            # if user_id not in self.member_name or today_name != self.member_name[user_id] and member_name_date[user_id] < member[3]:
            #     self.member_name[user_id] = today_name
            #     member_name_date[user_id] = today_date

        # 读取黑名单评分
        self.logger.info("正在读取 黑名单评分")
        with open(black_list_rating_path, 'r', encoding='utf-8') as f:
            self.rating_dict = json.load(f)
        # 读取黑名单
        self.blacklist = self.read_blacklist()

    def flatten(self, str):
        return str.replace(' ','').replace('[]','')
    
    def get_book_infos(self):
        return self.book_dict
    
    def get_group_infos(self):
        return self.group_dict
        
    def hash_string(self, string):
        # 如果是列表
        if isinstance(string, list):
            hash_list = []
            for str in string:
                hash_list.append(self.hash_string(str))
            return hash_list
        if string is None:
            string = '无'
        string = string.replace('\n', '<br>')
        if string not in self.hash_dict:
            self.hash_index += 1
            self.hash_dict[string] = self.hash_index
            return self.hash_index
        else:
            return self.hash_dict[string]
        
    def get_rating(self, reason_list):
        rating = 0
        for reason in reason_list:
            reason = reason.strip()
            if reason in self.rating_dict:
                rating += self.rating_dict[reason]
            else:
                print(f"未知原因：{reason}")
        return rating

    def read_blacklist(self):
        if not os.path.exists(black_list_path):
            return []
        # openpyxl
        wb = openpyxl.load_workbook(black_list_path)
        ws = wb.active
        # 列名：百词斩昵称	百词斩ID	退班时间	拉黑原因	记录班长	备注	最后编辑时间(不要填)	最后编辑人（不要填）	原创建班长（不要填）
        blacklist = {}
        blacklist_date = {}
        for row in ws.iter_rows(min_row=2):
            uid = row[1].value
            if uid is None:
                continue
            try:
                uid = int(uid)
            except:
                print(f"{uid} 不是数字，对应昵称为 {row[0].value}，跳过")
                continue
            if uid not in blacklist:
                blacklist[uid] = []
                blacklist_date[uid] = []
            if row[2].value is None:
                continue
            date = int(row[2].value.timestamp())
            recorder = self.hash_string(row[4].value)
            
            # 防止重复添加
            id_str = f"{date}{recorder}"
            if id_str in blacklist_date[uid]:
                continue
            blacklist_date[uid].append(id_str)

            reason = []
            rating = 0
            if row[3].value is not None:
                reason = row[3].value.split(',')
                rating = self.get_rating(reason)
                reason = self.hash_string(reason)
            
            remark = self.hash_string(row[5].value)

            if row[6].value is None:
                continue
            last_edit_time = row[6].value.timestamp()
            last_editor = self.hash_string(row[7].value)
            first_editor = self.hash_string(row[8].value)
            blacklist[uid].append([rating, date, reason, recorder, remark, last_edit_time, last_editor, first_editor])
        return blacklist
    
    def ComboExpectancy(self, finishing_rate: float, join_days: int) -> int:
        '''计算最长连卡天数期望'''
        # 我夜观星象，得到超越方程E*(x)^Q = 0.1Q，x为打卡率，求解Q即可
        if finishing_rate == 1:
            return join_days
        lying_flat_index = 0.5
        if finishing_rate < 0.88: # 小于0.88的同学基本会摆烂，因此乘上躺平系数
            finishing_rate *= lying_flat_index
        rate = finishing_rate
        expectancy = join_days
        length = 0
        while length < join_days:
            length += 1
            expectancy *= rate # 11...11（Q个1）在100数位上发生的期望次数
            if expectancy <= length / 4:  # 如果期望大于length则代表有一个完整的length序列，我们要找到符合条件的length最大值
                # 但这个/10，我的天文知识还不能解释。经过测试在join_days = 100..10000, x=0.01..0.99都很符合
                return length
        return join_days

    def get_member_infos(self):
        # 返回：当前昵称、加入的班级列表，学过的书本名称，词数统计、打卡时间统计
        member_infos = []
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        seven_days_start_datetime = today_start - datetime.timedelta(days=7)
        seven_days_start_timestamp = int(seven_days_start_datetime.timestamp())
        seven_days_start_dateint = int(seven_days_start_datetime.strftime("%Y%m%d"))
        thirty_days_start = int((today_start - datetime.timedelta(days=35)).timestamp())
        # 为了让每个分类的天数均衡，范围必须是7的倍数。数据库slice也是必须在35天以上
        processed_cnt = 0
        for user_id, member_list in self.members.items():
            book_name_set = set()
            word_count_dict = {}
            word_count_sum = 0
            word_count_cnt = 0
            completed_time_dict = {}
            daka_dates = {} # 用于给self.gross_daka_time_dict去重（每人每天只计入一次）
            completed_time_list = []
            completed_time_sum = 0
            completed_time_stdev = 0
            completed_time_cnt = 0
            completed_time_cnt_this_week = 0 # 只有本周至少打卡1次的成员才算有效
            streak_date = 0
            streak_days = 0
            group_infos = {}

            daka_timestamp = 0
            for member in member_list:
                # 处理以前有漏卡的连胜
                today_date = int(member[3])
                if streak_date - today_date == 1:
                    streak_days += 1
                else:
                    streak_days = 1
                streak_date = today_date

                # 统计学过的书本
                book_name_set.add(member[7])

                # 统计打卡时间
                if member[2] != '0':
                    daka_timestamp = int(member[2])
                    # 判断是否在本周
                    if daka_timestamp >= seven_days_start_timestamp:
                        completed_time_cnt_this_week += 1
                    daka_time = ((daka_timestamp + 14400) % 86400) # UTC+8要+28800s # 鼓励早打卡，而不是凌晨打卡，因此多减4小时14400s，共+14400s

                    if daka_timestamp >= thirty_days_start:
                        if today_date not in daka_dates:
                            daka_dates[today_date] = 1
                            category = today_date % 7
                            daka_minute = int(daka_time / 60)
                            if category not in self.gross_daka_time_dict:
                                self.gross_daka_time_dict[category] = {}
                            if today_date >= seven_days_start_dateint:
                                if category not in self.gross_daka_date:
                                    self.gross_daka_date[category] = today_date

                                if today_date not in self.gross_daka_time_dict_7:
                                    self.gross_daka_time_dict_7[today_date] = {}
                                if daka_minute not in self.gross_daka_time_dict_7[today_date]:
                                    self.gross_daka_time_dict_7[today_date][daka_minute] = 1
                                else:
                                    self.gross_daka_time_dict_7[today_date][daka_minute] += 1

                            if daka_minute not in self.gross_daka_time_dict[category]:
                                self.gross_daka_time_dict[category][daka_minute] = 1
                            else:
                                self.gross_daka_time_dict[category][daka_minute] += 1

                        # 排名只记录30天内的打卡时间
                        completed_time_sum += daka_time
                        completed_time_cnt += 1
                        completed_time_list.append(daka_time) # 等下要算标准差
                    completed_time_div = int(daka_time/self.time_count_period)
                    if completed_time_div not in completed_time_dict:
                        completed_time_dict[completed_time_div] = 1
                    else:
                        completed_time_dict[completed_time_div] += 1
                
                # 如果学习作弊，即为-1
                if member[4] > 0:
                    word_count = -self.word_count_period if member[9] == 1 else member[4]
                    word_count_div = int(word_count/self.word_count_period)
                    # 排名只记录7天内的单词数量
                    if daka_timestamp >= seven_days_start_timestamp:
                        word_count_sum += word_count
                        word_count_cnt += 1
                    if word_count_div not in word_count_dict:
                        word_count_dict[word_count_div] = 1
                    else:
                        word_count_dict[word_count_div] += 1

                # 统计班级信息：最长的连卡天数（COMPLETED_TIMES==DURATION_DAYS），最长在班时间和对应的打卡天数（COMPLETED_TIME）（分别记录班级ID和名称）
                group_id = member[8]
                completed_times = member[5]
                duration_days = member[6]
                if group_id not in group_infos:
                    group_infos[group_id] = [0, 0, 0]
                current_max_streak_days = group_infos[group_id][0]
                # current_max_completed_times = group_infos[group_id][1]
                current_max_duration_days = group_infos[group_id][2]
                if member[2]=='0':
                    duration_days -= 1 # 未打卡的天数减一
                if streak_days > current_max_streak_days:
                    group_infos[group_id][0] = streak_days
                if completed_times == duration_days and completed_times > current_max_streak_days:
                    group_infos[group_id][0] = completed_times
                if duration_days > current_max_duration_days:
                    group_infos[group_id][1] = completed_times
                    group_infos[group_id][2] = duration_days

            # 找最大的连卡天数、连卡期望
            max_streak = 0
            max_expectancy = 0
            for group_id, group_info in group_infos.items():
                max_streak = max(max_streak, group_info[0])
                group_max_completed_times = group_info[1]
                group_max_duration_days = group_info[2]
                if group_max_duration_days > 0:
                    max_expectancy = max(max_expectancy, self.ComboExpectancy(group_max_completed_times/group_max_duration_days, group_max_duration_days))
                
            # 全部保留2位小数
            if word_count_cnt == 0:
                word_average = 0
            else:
                word_average = round(word_count_sum / word_count_cnt, 2)
            if completed_time_cnt < 3: # 至少要打3次才计算平均值、计入排行榜
                completed_time_average = 86399
            else:
                completed_time_average = completed_time_sum / completed_time_cnt
            # 根据completed_time_dict计算标准差
            if completed_time_cnt > 1:
                completed_time_stdev = statistics.stdev(completed_time_list)
            max_expectancy = round(max_expectancy, 2)
            total_rating = 100
            blacklist_info = []
            if user_id in self.blacklist:
                blacklist_info_with_rating = self.blacklist[user_id]
                for info in blacklist_info_with_rating:
                    total_rating += info[0]
                    blacklist_info.append(info[1:])
            if completed_time_cnt_this_week > 0 or len(blacklist_info) > 0: # 为节省空间，只有本周至少打卡1次的成员才算有效
                member_infos.append([user_id, group_infos, list(book_name_set), word_count_dict, completed_time_dict, word_average, int(completed_time_average / 60) * 60, max_streak, max_expectancy, int((completed_time_average + completed_time_stdev) / 60) * 60, blacklist_info, total_rating])
            else:
                # 移除没有打卡的成员名称
                del self.member_name[user_id]
            # 最大数据大小（字节）： 10  + 6 * (10 + 10) +       50        +       100     +          200        +      5      +           5           +     5     +       5        +             5      = 505
            processed_cnt += 1
            if processed_cnt % 100000 == 0:
                self.logger.info(f"已处理{processed_cnt}人")
        return member_infos
    
    def clear_screen(self):
        self.id_dict = {}
        self.screen_set = set()

    def add_screen(self, uid):
        screen_uid = uid % self.reserve_digits
        if uid in self.id_dict:
            return uid + self.id_dict[uid] - screen_uid, self.id_dict[uid]
        # 没有记录，生成新的screen_uid
        delta = 0
        while (delta + screen_uid) in self.screen_set:
            delta += 0.1
        final_screen_uid = screen_uid + delta
        # 记录映射关系
        self.id_dict[uid] = final_screen_uid
        self.screen_set.add(final_screen_uid)
        return uid + delta, final_screen_uid
    
    def screen(self, members, num, max_num, index_1, index_2): 
        '''屏蔽前num名的id'''
        rank = [0]
        rank_screen = [num]
        for member in members[:num]:
            uid, screen_uid = self.add_screen(member[index_1])
            score = member[index_2]
            rank.append(uid)
            rank.append(score)
            rank_screen.append(screen_uid)
            rank_screen.append(score)
        for member in members[num:max_num]: # 保留前max_num名
            uid, screen_uid = self.add_screen(member[index_1])
            score = member[index_2]
            rank.append(uid)
            rank.append(score)
            rank_screen.append(uid)
            rank_screen.append(score)
        return rank, rank_screen
        
    def update_member_infos(self, logger=None, NO_EXCEL=True):
        '''计算真正有意义的排行榜。
        按照词数加权均值、加权打卡时间均值、连卡天数、连卡期望分别出前1000名'''
        if logger is None:
            logger = self.logger
        self.logger.info(f"开始更新成员信息，共{len(self.members)}人")
        member_infos = self.get_member_infos()
        # 如果排名相同，按照其他三个指标排序
        self.clear_screen() # 得到前排的去重后的uid，得到昵称

        # 创建一个新的工作簿
        if not NO_EXCEL:
            wb = openpyxl.Workbook()
        def get_line_chart(ws, title, xtitle, ytitle, xcol, ycol, maxrow, is_time=False):
            chart = LineChart()
            chart.title = title
            chart.style = 7
            chart.y_axis.title = ytitle
            chart.x_axis.title = xtitle
            data = Reference(ws, min_col=ycol, min_row=2, max_col=ycol, max_row=maxrow+1)
            cats = Reference(ws, min_col=xcol, min_row=2, max_col=xcol, max_row=maxrow+1)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            chart.shape = 4
            chart.height = 15
            chart.width = 30
            if is_time:
                chart.x_axis.number_format = 'hh:mm:ss'
            return chart
        def get_bar_chart(ws, title, xtitle, ytitle, xcol, ycol, maxrow, log_base=True):
            chart = BarChart()
            chart.title = title
            chart.style = 7
            chart.y_axis.title = ytitle
            chart.x_axis.title = xtitle
            # y轴使用对数坐标
            if log_base:
                chart.y_axis.scaling.logBase = 10
            data = Reference(ws, min_col=ycol, min_row=2, max_col=ycol, max_row=maxrow+1)
            cats = Reference(ws, min_col=xcol, min_row=2, max_col=xcol, max_row=maxrow+1)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            chart.shape = 5
            chart.height = 15
            chart.width = 30
            return chart
        def get_scatter_chart(ws, title, xtitle, ytitle, xcol, ycol: int | list, maxrow, titles=None):
            chart = ScatterChart()
            chart.title = title
            chart.style = 7
            chart.y_axis.title = ytitle
            chart.x_axis.title = xtitle
            x_data = Reference(ws, min_col=xcol, min_row=2, max_col=xcol, max_row=maxrow+1)
            if isinstance(ycol, int):
                y_data = Reference(ws, min_col=ycol, min_row=2, max_col=ycol, max_row=maxrow+1)
                series = Series(y_data, x_data, title=title)
                series.graphicalProperties.line.noFill = True # 取消线条
                chart.series.append(series)
                series.marker.symbol = "circle" # 显示数据标记
                series.marker.size = 5
            else:
                for i, y_col in enumerate(ycol):
                    y_data = Reference(ws, min_col=y_col, min_row=2, max_col=y_col, max_row=maxrow+1)
                    series = Series(y_data, x_data, title=titles[i])
                    series.graphicalProperties.line.noFill = True
                    chart.series.append(series)
                    series.marker.symbol = "circle"
                    series.marker.size = 5
            chart.shape = 4
            chart.height = 15
            chart.width = 30
            # 设置x轴显示为时间
            chart.x_axis.number_format = 'hh:mm:ss'
            return chart
        
        def calc_and_save_ranking(member_infos, key_func, main_key_index, screen_num, screen_max_num):
            same_rank_count = {}
            rank_score = {}
            member_infos.sort(key=key_func, reverse=True)
            ranking = 1
            score_prev = member_infos[0][main_key_index]
            count_same_score = 0  # 同分人数
            for i, member in enumerate(member_infos):
                if i > 0 and member[main_key_index] != score_prev:
                    same_rank_count[ranking] = count_same_score
                    rank_score[ranking] = score_prev
                    ranking += 1
                    score_prev = member[main_key_index]
                    count_same_score = 0  # 重置同分人数
                count_same_score += 1  # 增加同分人数
                member.append(ranking)

            # 处理最后一个排名
            same_rank_count[ranking] = count_same_score
            rank_score[ranking] = score_prev

            rank, rank_screen = self.screen(member_infos, screen_num,screen_max_num, 0, main_key_index)

            return rank, rank_screen, same_rank_count, rank_score

        # 连卡天数
        self.logger.info("开始计算streak排名")
        streak_rank, streak_rank_screen, same_rank_count, rank_score = calc_and_save_ranking(member_infos, lambda x: x[7], 7, 100, 100)
        # 写入streak排名统计
        if not NO_EXCEL:
            ws = wb.active
            ws.title = "streak"
            ws.append(["排名", "连卡天数", "同分人数", datetime.datetime.now().strftime("%Y-%m-%d"), f"排名展示{len(streak_rank)}人"])
            for rank in same_rank_count:
                ws.append([rank, rank_score[rank], same_rank_count[rank]])

            ws.add_chart(get_line_chart(ws, "streak排名", "排名", "连卡天数", 1, 2, len(same_rank_count)), "D1")
            ws.add_chart(get_bar_chart(ws, "streak排名", "排名", "同分人数", 1, 3, len(same_rank_count)), "D31")
        
        # 连卡期望
        self.logger.info("开始计算expectancy排名")
        expectancy_rank, expectancy_rank_screen, same_rank_count, rank_score = calc_and_save_ranking(member_infos, lambda x: x[8], 8, 100, 100)
        # 写入expectancy排名统计
        if not NO_EXCEL:
            ws = wb.create_sheet("expectancy")
            ws.append(["排名", "接近满卡天数", "同分人数", datetime.datetime.now().strftime("%Y-%m-%d"), f"排名展示{len(expectancy_rank)}人"])
            for rank in same_rank_count:
                ws.append([rank, rank_score[rank], same_rank_count[rank]])
            ws.add_chart(get_line_chart(ws, "expectancy排名", "排名", "接近满卡天数", 1, 2, len(same_rank_count)), "D1")
            ws.add_chart(get_bar_chart(ws, "expectancy排名", "排名", "同分人数", 1, 3, len(same_rank_count)), "D31")

        # 词数
        self.logger.info("开始计算word排名")
        word_rank, word_rank_screen, same_rank_count, rank_score = calc_and_save_ranking(member_infos, lambda x: x[5], 5, 100, 100)
        # 写入word排名统计
        if not NO_EXCEL:
            ws = wb.create_sheet("word")
            ws.append(["排名", "词数", "同分人数", datetime.datetime.now().strftime("%Y-%m-%d"), f"排名展示{len(word_rank)}人"])
            for rank in same_rank_count:
                ws.append([rank, rank_score[rank], same_rank_count[rank]])
            ws.add_chart(get_line_chart(ws, "word排名", "排名", "词数", 1, 2, len(same_rank_count)), "D1")
            ws.add_chart(get_bar_chart(ws, "word排名", "排名", "同分人数", 1, 3, len(same_rank_count)), "D31")

        # 打卡时间
        self.logger.info("开始计算time排名")
        time_rank, time_rank_screen, same_rank_count, rank_score = calc_and_save_ranking(member_infos, lambda x: -x[6], 6, 100, 100)
        # 写入time排名统计

        def get_weekday(date: int):
            return datetime.datetime.strptime(f"{date}", '%Y%m%d').weekday()+1

        # 到时候要把这个做成全服缓存排名，也就是每30天存一次excel和db的image，然后每天删掉30天前的缓存
        if not NO_EXCEL:
            ws = wb.create_sheet("time")
            # 根据get_weekday(self.gross_daka_date[key])排序
            sorted_keys = sorted(self.gross_daka_date.keys(), key=lambda x: get_weekday(self.gross_daka_date[x]))
            title = ["排名", "打卡时间", "同分人数"]
            title.extend([self.gross_daka_date[i] for i in sorted_keys]*2)
            title.extend([datetime.datetime.now().strftime("%Y-%m-%d"), f"排名展示{len(time_rank)}人"])
            ws.append(title)
            for i, key in enumerate(sorted_keys):
                self.gross_daka_time_dict[key][172800] = i # 排序用
                self.gross_daka_time_dict_7[self.gross_daka_date[key]][172800] = i

            gross_daka_time_list = sorted(self.gross_daka_time_dict.values(), key=lambda x: x[172800])
            gross_daka_time_list_7 = sorted(self.gross_daka_time_dict_7.values(), key=lambda x: x[172800])
            for rank in same_rank_count:
                score_minute = (rank_score[rank]) / 60
                data = [rank, (rank_score[rank] + 14400)/86400, same_rank_count[rank]]
                for value_dict in gross_daka_time_list_7:
                    data.append(value_dict.get(score_minute, 0))
                for value_dict in gross_daka_time_list:
                    data.append(value_dict.get(score_minute, 0))
                ws.append(data)

            sub_series_titles = []
            for i, key in enumerate(sorted_keys):
                sub_series_titles.append(f"{self.gross_daka_date[key]}星期{get_weekday(self.gross_daka_date[key])}")
            t1_start = 4
            t1_end = 4+len(self.gross_daka_time_dict_7)
            t2_start = 4+len(self.gross_daka_time_dict_7)
            t2_end = 4+len(self.gross_daka_time_dict_7)+len(self.gross_daka_time_dict)
            ws.add_chart(get_scatter_chart(ws, "人次(7)", "打卡时间", "人数", 2, [i for i in range(t1_start, t1_end)], len(same_rank_count), titles=sub_series_titles), "D1")
            ws.add_chart(get_scatter_chart(ws, "人次(30)", "打卡时间", "人数", 2, [i for i in range(t2_start, t2_end)], len(same_rank_count), titles=sub_series_titles), "D31")
            ws.add_chart(get_line_chart(ws, "time排名", "打卡时间", "排名", 2, 1, len(same_rank_count), is_time=True), "D61")


        
        # 被拉黑次数（黑名单评分）
        self.logger.info("开始计算blacklist排名")
        blacklist_rank, blacklist_rank_screen, same_rank_count, rank_score = calc_and_save_ranking(member_infos, lambda x: -x[11], 11, 0, 100)
        # 写入blacklist排名统计
        if not NO_EXCEL:
            ws = wb.create_sheet("blacklist")
            ws.append(["排名", "信誉评分", "同分人数", datetime.datetime.now().strftime("%Y-%m-%d"), f"排名展示{len(blacklist_rank)}人"])
            for rank in same_rank_count:
                ws.append([rank, rank_score[rank], same_rank_count[rank]])
            ws.add_chart(get_line_chart(ws, "blacklist排名", "排名", "信誉评分", 1, 2, len(same_rank_count)), "D1")
            ws.add_chart(get_bar_chart(ws, "blacklist排名", "排名", "人数", 1, 3, len(same_rank_count)), "D31")

            # 保存到Excel文件
            logger.info("开始保存Excel文件")
            date_str = datetime.datetime.now().strftime("%Y.%m.%d")
            wb.save(f"排名统计{date_str}.xlsx")



        self.logger.info("开始写入排名数据")
        with open(member_info_top_rate_path, 'w', encoding='utf-8') as f:
            f.write("rank="+self.flatten(json.dumps([streak_rank, expectancy_rank, word_rank, time_rank, blacklist_rank], ensure_ascii=False))+";")
        # with zipfile.ZipFile(f"{member_info_top_rate_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
        #     f.write(member_info_top_rate_path, arcname=member_info_top_rate_path)

        with open(member_info_top_rate_screen_path, 'w', encoding='utf-8') as f:
            f.write("var rank="+self.flatten(json.dumps([streak_rank_screen, expectancy_rank_screen, word_rank_screen, time_rank_screen, blacklist_rank_screen], ensure_ascii=False))+";")
        # with zipfile.ZipFile(f"{member_info_top_rate_screen_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
        #     f.write(member_info_top_rate_screen_path, arcname=member_info_top_rate_screen_path)

        self.logger.info("开始写入排名name信息")
        # 用self.screen_set查表得到昵称
        with open(member_info_top_name_path, 'w', encoding='utf-8') as f:
            f.write("var rankNames=`"+self.flatten('\n'.join([f"{screen_uid}\n{self.member_name.get(uid, '未知昵称')}" for uid, screen_uid in self.id_dict.items()]))+"`;")
        # with zipfile.ZipFile(f"{member_info_top_name_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
        #     f.write(member_info_top_name_path, arcname=member_info_top_name_path)
        
        # 然后写入班级和书本信息
        self.logger.info("开始写入班级和书本信息")
        group_infos = self.get_group_infos()
        group_infos[-1] = f'数据更新日期：{datetime.datetime.now().strftime("%Y-%m-%d")}'
        book_infos = self.get_book_infos()
        with open(groups_path, 'wb') as f:
            f.write(encoder(self.flatten('\n'.join([f"{key}\n{value}" for key, value in group_infos.items()]))))
        with zipfile.ZipFile(f"{groups_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(groups_path, arcname=groups_path)
        with open(books_path, 'wb') as f:
            f.write(encoder(self.flatten('\n'.join([f"{key}\n{value}" for key, value in book_infos.items()]))))
        with zipfile.ZipFile(f"{books_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(books_path, arcname=books_path)
        
        self.logger.info("开始写入blacklist字符串")
        # print(self.flatten('\n'.join(f"{string}\n{hash}" for hash, string in self.hash_dict.items())))
        with open(black_list_string_assets, 'wb') as f:
            f.write(encoder(self.flatten('\n'.join(f"{string}\n{hash}" for hash, string in self.hash_dict.items()))))
        with zipfile.ZipFile(f"{black_list_string_assets}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(black_list_string_assets, arcname=black_list_string_assets)

        # 然后是普通数据，按照前..位进行分割
        self.logger.info("开始压缩member数据")
        sect_num = 3 # 切分成900个文件  
        member_infos.sort(key=lambda x: x[0], reverse=False)
        classified_member_infos = {}
        for member in member_infos:
            sect = str(member[0])[:sect_num]
            if sect not in classified_member_infos:
                classified_member_infos[sect] = []

            # 压缩数据
            # 将group_infos变为列表，可以省大括号、双引号和冒号
            group_infos_list = []
            for group_id, group_info in member[1].items():
                group_infos_list.extend([group_id, group_info[0], group_info[1], group_info[2]])
            member[1] = group_infos_list

            # 将word_count_dict和completed_time_dict变为列表
            word_count_list = []
            for word_count_div, word_count in member[3].items():
                word_count_list.extend([word_count_div, word_count])
            member[3] = word_count_list
            completed_time_list = []
            for completed_time_div, completed_time in member[4].items():
                completed_time_list.extend([completed_time_div, completed_time])
            member[4] = completed_time_list
            
            classified_member_infos[sect].append(member)

        logger.info(f"开始写入member数据，共{len(classified_member_infos)}个文件")
        processed_cnt = 0
        for sect, member_list in classified_member_infos.items():
            flatten_str = self.flatten(json.dumps(member_list, ensure_ascii=False))
            with open(f"{member_info_path}{sect}.bin", 'wb') as f:
                f.write(encoder(flatten_str))
            with zipfile.ZipFile(f"{member_info_path}{sect}.bin.zip", 'w', zipfile.ZIP_DEFLATED) as f:
                f.write(f"{member_info_path}{sect}.bin", arcname=f"{member_info_path}{sect}.bin")
            processed_cnt += 1
            if processed_cnt % 100 == 0:
                logger.info(f"完成第{processed_cnt}个文件")

        self.logger.info("开始压缩member_name数据")
        classified_member_names = {}
        processed_cnt = 0
        for user_id, nickname in self.member_name.items():
            sect = str(user_id)[:sect_num]
            if sect not in classified_member_names:
                classified_member_names[sect] = []
            classified_member_names[sect].append([user_id, nickname])
        self.logger.info(f"开始写入member_name数据，共{len(classified_member_names)}个文件")
        processed_cnt = 0
        for sect, member_list in classified_member_names.items():
            flatten_str = "\n".join([f"{user_id}\n{nickname}" for user_id, nickname in member_list])
            with open(f"{member_name_path}{sect}.bin", 'wb') as f:
                f.write(encoder(flatten_str)) # nickname中有空格，不flatten
            with zipfile.ZipFile(f"{member_name_path}{sect}.bin.zip", 'w', zipfile.ZIP_DEFLATED) as f:
                f.write(f"{member_name_path}{sect}.bin", arcname=f"{member_name_path}{sect}.bin")
            processed_cnt += 1
            if processed_cnt % 100 == 0:
                logger.info(f"完成第{processed_cnt}个文件")

        self.logger.info("更新成员信息完成")

    
class notice_storage_class:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 加载bad_fuzz
        with open(bad_notice_path, "r", encoding="utf-8") as f:
            self.bad_notice_str = f.read()

    def close(self):
        with open(bad_notice_path, "w", encoding="utf-8") as f:
            f.write(self.bad_notice_str)

    
    


if __name__ == '__main__':
    conn = sqlite3.connect(default_notice_db_path)
    update_notice(conn)
    conn.close()