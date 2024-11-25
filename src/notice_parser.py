import random
import datetime
import zipfile
import sqlite3
import logging
import statistics
import openpyxl
import json
import os

DEBUG = True

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
member_info_top_rate_path = '../BCZ-Notice-Examiner/assets/member_info_top_rate.bin'
member_info_top_rate_screen_path = '../BCZ-Notice-Examiner/assets/member_info_top_rate_screen.bin'
member_info_top_name_path = "../BCZ-Notice-Examiner/assets/member_info_top_name.bin"
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
def slice_invalid_char(text: str):
    # 去除并存储无效字符的位置
    invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）','-','—','_']
    invalid_storage = {}
    position = 0
    new_text = ""
    for char in text:
        if char in invalid_chars:
            set_invalid_storage(invalid_storage, position, char)
        elif char in replace_dict:
            set_invalid_storage(invalid_storage, position, char)
            position += 1
            new_text += replace_dict[char]
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

def parse_text(text: str) -> list:
    '''将文本解析长度为2的所有字串列表'''
    invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）']
    for char in invalid_chars:
        text = text.replace(char, '')
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
        # if date < least_valid_date:
        #     continue
        if share_key not in notice_dict:
            notice_dict[share_key] = []
            notice_date[share_key] = [latest_date]
        notice_dict[share_key].append(notice_content)
        notice_date[share_key].append(latest_date)
        if notice_content.startswith('(空)') and date > most_recent_clear_date:
            most_recent_clear_date = date # 这里使用开始而不是最新日期
    # 遍历每个分类，找到公告被清空（以'(空)'开头）的那天
    print(f"most_recent_clear_date: {most_recent_clear_date}")
    warn_words = []
    accept_words = []
    accept_notice_list = []
    bad_notice_list = []
    for share_key, notice_list in notice_dict.items():
        length = len(notice_list)
        for i in range(0, length):
            if notice_list[i].startswith('(空)'):
                # 前面的公告加入到warn_words中
                for j in range(i): # 补药放一堆(空)进去啦
                    accept_words.extend(parse_text(notice_list[j]))
                    accept_notice_list.append(notice_list[j])
                    
                for j in range(i+1, length):
                    if notice_list[j].startswith('(空)'):
                        continue
                    warn_words.extend(parse_text(notice_list[j]))
                    bad_notice_list.append(notice_list[j])
                    break # 暂时只要(空)后面的第一个公告
                break
        else:
            # 公告都没有被清空，且是最近的公告，全部加入到accept_words中
            for notice, date in zip(notice_list, notice_date[share_key]):
                if date >= most_recent_clear_date:
                    accept_words.extend(parse_text(notice))
                    accept_notice_list.append(notice)
                else:
                    continue # 没清空，但不确定，故也不要
                    warn_words.extend(parse_text(notice))
                    bad_notice_list.append(notice)
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
        f.write(encoder(flatten(json.dumps(list(warn_words), ensure_ascii=False))))
    with zipfile.ZipFile(f"{warn_word_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(warn_word_path, arcname=warn_word_path)
        
    accept_words = list(accept_words)
    today_date = f"数据更新日期：{datetime.datetime.now().strftime('%Y-%m-%d')}"
    accept_words.insert(0, today_date)
    with open(accept_word_path, 'wb') as f:
        f.write(encoder(flatten(json.dumps(accept_words, ensure_ascii=False))))
    with zipfile.ZipFile(f"{accept_word_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(accept_word_path, arcname=accept_word_path)
    with open(accept_notice_path, 'w', encoding='utf-8') as f:
        f.write(accept_fuzz)
    with open(bad_notice_path, 'w', encoding='utf-8') as f:
        f.write(bad_fuzz)

class member_storage_class:
    def __init__(self):
        self.db_path = default_notice_db_path
        self.logger = logging.getLogger(__name__)
        self.hash_dict = {}
        self.hash_index = 0

        self.word_count_period = 25 # 25词分一档
        self.time_count_period = 1800 # 30分钟分一档
        self.reserve_digits = 1000000 # 保留uid的最后6位

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # 获取所有书本信息
        # HASH_ID, BOOK_NAME, BOOK_ID, BOOK_URL
        cur.execute("SELECT HASH_ID, BOOK_NAME FROM BOOK_NAME")
        self.book_dict = {}
        for book in cur.fetchall():
            self.book_dict[book[0]] = book[1]
        # 获取所有班级信息
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
        # 获取所有成员信息
        command = "SELECT USER_ID, NICKNAME, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_ID, STUDY_CHEAT FROM MEMBERS ORDER BY TODAY_DATE DESC"
        if DEBUG: # 苔泰！
            command = "SELECT USER_ID, NICKNAME, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_ID, STUDY_CHEAT FROM MEMBERS WHERE USER_ID == 1141201181 OR USER_ID == 1584809188 OR USER_ID == 766773235 ORDER BY TODAY_DATE DESC"
        cur.execute(command)
        # 按照USER_ID分类
        self.member_name = {}
        member_name_date = {}
        self.members = {}
        for member in cur.fetchall():
            user_id = member[0]
            if user_id not in self.members:
                self.members[user_id] = []
            self.members[user_id].append(member)

            name = member[1]
            if name is not None and user_id not in self.member_name:
                self.member_name[user_id] = member[1]
            # 下面这个是没有排序的版本
            # today_name = member[1]
            # today_date = member[3]
            # if today_date is None:
            #     continue
            # if user_id not in self.member_name or today_name != self.member_name[user_id] and member_name_date[user_id] < member[3]:
            #     self.member_name[user_id] = today_name
            #     member_name_date[user_id] = today_date

        # 读取黑名单评分
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
        seven_days_start = (today_start - datetime.timedelta(days=7)).timestamp()
        for user_id, member_list in self.members.items():
            book_name_set = set()
            word_count_dict = {}
            word_count_sum = 0
            word_count_cnt = 0
            completed_time_dict = {}
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
                book_name_set.add(member[7])
                if member[2] != '0':
                    daka_timestamp = int(member[2])
                    # 判断是否在本周
                    if daka_timestamp >= seven_days_start:
                        completed_time_cnt_this_week += 1
                    daka_time = ((daka_timestamp + 14400) % 86400) # UTC+8要+28800s # 鼓励早打卡，而不是凌晨打卡，因此多减4小时14400s，共+14400s
                    completed_time_list.append(daka_time)
                    completed_time_sum += daka_time
                    completed_time_cnt += 1
                    completed_time_div = int(daka_time/self.time_count_period)
                    if completed_time_div not in completed_time_dict:
                        completed_time_dict[completed_time_div] = 1
                    else:
                        completed_time_dict[completed_time_div] += 1
                
                # 如果学习作弊，即为-1
                if member[4] > 0:
                    word_count = -self.word_count_period if member[9] == 1 else member[4]
                    word_count_div = int(word_count/self.word_count_period)
                    if daka_timestamp >= seven_days_start: # 用于排行的只计算7天，统计的计算所有历史
                        word_count_sum += word_count
                        word_count_cnt += 1
                    if word_count_div not in word_count_dict:
                        word_count_dict[word_count_div] = 1
                    else:
                        word_count_dict[word_count_div] += 1

                # 处理以前有漏卡的连胜
                today_date = int(member[3])
                if streak_date - today_date == 1:
                    streak_days += 1
                else:
                    streak_days = 1
                streak_date = today_date

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
            if completed_time_cnt == 0:
                completed_time_average = 0
            else:
                completed_time_average = completed_time_sum / completed_time_cnt
            # 根据completed_time_dict计算标准差
            if completed_time_cnt > 1:
                completed_time_list.sort()
                completed_time_stdev = statistics.stdev(completed_time_list)
            max_expectancy = round(max_expectancy, 2)
            total_rating = 100
            blacklist_info = []
            if user_id in self.blacklist:
                blacklist_info_with_rating = self.blacklist[user_id]
                for info in blacklist_info_with_rating:
                    total_rating += info[0]
                    blacklist_info.append(info[1:])
            if completed_time_cnt_this_week > 0: # 为节省空间，只有本周至少打卡1次的成员才算有效
                member_infos.append([user_id, group_infos, list(book_name_set), word_count_dict, completed_time_dict, word_average, round(completed_time_average, 2), max_streak, max_expectancy, round(completed_time_average + completed_time_stdev, 2), blacklist_info, total_rating])
            # 最大数据大小（字节）： 10  + 6 * (10 + 10) +       50        +       100     +          200        +      5      +           5           +     5     +       5        +             5      = 505
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
    
    def screen(self, members, num, index_1, index_2): 
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
        for member in members[num:500]: # 保留前500名
            uid, screen_uid = self.add_screen(member[index_1])
            score = member[index_2]
            rank.append(uid)
            rank.append(score)
            rank_screen.append(uid)
            rank_screen.append(score)
        return rank, rank_screen
        
    def update_member_infos(self, logger=None):
        '''计算真正有意义的排行榜。
        按照词数加权均值、加权打卡时间均值、连卡天数、连卡期望分别出前1000名'''
        if logger is None:
            logger = self.logger
        self.logger.info("开始更新成员信息")
        member_infos = self.get_member_infos()
        # 如果排名相同，按照其他三个指标排序
        self.clear_screen() # 得到前排的去重后的uid，得到昵称
        # 连卡天数
        self.logger.info("开始计算streak排名")
        member_infos.sort(key=lambda x: (x[7], x[8], x[5], -x[9]), reverse=True)
        for i, member in enumerate(member_infos):
            member.append(i+1)
        streak_rank, streak_rank_screen = self.screen(member_infos, 101, 0, 7)
        # 连卡期望
        self.logger.info("开始计算expectancy排名")
        member_infos.sort(key=lambda x: (x[8], x[7], x[5], -x[9]), reverse=True)
        for i, member in enumerate(member_infos):
            member.append(i+1)
        expectancy_rank, expectancy_rank_screen = self.screen(member_infos, 101, 0, 8)
        # 词数
        self.logger.info("开始计算word排名")
        member_infos.sort(key=lambda x: (x[5], x[7], x[8], -x[9]), reverse=True)
        for i, member in enumerate(member_infos):
            member.append(i+1)
        word_rank, word_rank_screen = self.screen(member_infos, 101, 0, 5)
        # 打卡时间
        self.logger.info("开始计算time排名")
        member_infos.sort(key=lambda x: (-x[9], x[7], x[8], x[5]), reverse=True)
        for i, member in enumerate(member_infos):
            member.append(i+1)
        time_rank, time_rank_screen = self.screen(member_infos, 101, 0, 9)
        # 被拉黑次数（黑名单评分）
        self.logger.info("开始计算blacklist排名")
        member_infos.sort(key=lambda x: (-x[11], -x[7], -x[8]), reverse=True)
        for i, member in enumerate(member_infos):
            member.append(i+1)
        blacklist_rank, blacklist_rank_screen = self.screen(member_infos, 0, 0, 11)


        self.logger.info("开始写入排名数据")
        with open(member_info_top_rate_path, 'wb') as f:
            f.write(encoder(self.flatten(json.dumps([streak_rank, expectancy_rank, word_rank, time_rank, blacklist_rank], ensure_ascii=False))))
        with zipfile.ZipFile(f"{member_info_top_rate_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(member_info_top_rate_path, arcname=member_info_top_rate_path)

        with open(member_info_top_rate_screen_path, 'wb') as f:
            f.write(encoder(self.flatten(json.dumps([streak_rank_screen, expectancy_rank_screen, word_rank_screen, time_rank_screen, blacklist_rank_screen], ensure_ascii=False))))
        with zipfile.ZipFile(f"{member_info_top_rate_screen_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(member_info_top_rate_screen_path, arcname=member_info_top_rate_screen_path)

        self.logger.info("开始写入排名name信息")
        # 用self.screen_set查表得到昵称
        with open(member_info_top_name_path, 'wb') as f:
            f.write(encoder(self.flatten('\n'.join([f"{screen_uid}\n{self.member_name.get(uid, '未知昵称')}" for uid, screen_uid in self.id_dict.items()]))))
        with zipfile.ZipFile(f"{member_info_top_name_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(member_info_top_name_path, arcname=member_info_top_name_path)
        
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
        for sect, member_list in classified_member_infos.items():
            flatten_str = self.flatten(json.dumps(member_list, ensure_ascii=False))
            with open(f"{member_info_path}{sect}.bin", 'wb') as f:
                f.write(encoder(flatten_str))
            with zipfile.ZipFile(f"{member_info_path}{sect}.bin.zip", 'w', zipfile.ZIP_DEFLATED) as f:
                f.write(f"{member_info_path}{sect}.bin", arcname=f"{member_info_path}{sect}.bin")

        self.logger.info("开始压缩member_name数据")
        classified_member_names = {}
        for user_id, nickname in self.member_name.items():
            sect = str(user_id)[:sect_num]
            if sect not in classified_member_names:
                classified_member_names[sect] = []
            classified_member_names[sect].append([user_id, nickname])
        self.logger.info(f"开始写入member_name数据，共{len(classified_member_names)}个文件")
        for sect, member_list in classified_member_names.items():
            flatten_str = "\n".join([f"{user_id}\n{nickname}" for user_id, nickname in member_list])
            with open(f"{member_name_path}{sect}.bin", 'wb') as f:
                f.write(encoder(flatten_str)) # nickname中有空格，不flatten
            with zipfile.ZipFile(f"{member_name_path}{sect}.bin.zip", 'w', zipfile.ZIP_DEFLATED) as f:
                f.write(f"{member_name_path}{sect}.bin", arcname=f"{member_name_path}{sect}.bin")

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