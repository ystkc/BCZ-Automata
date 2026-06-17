# notice_parser.py
'''通知、信息、违禁词和订阅类'''
import datetime
import zipfile
import sqlite3
import json
import os
import re

DEBUG = False
NO_ENCODE = False
ACCEPT_WORDS_LIMIT = 100000
default_notice_db_path = f'../BCZ-Notice-Examiner/bcz_notice.db?mode=ro'


def encoder(text):
    if NO_ENCODE:
        return bytearray(text.encode())
    # 转化成bytearray类型
    input = bytearray(text.encode())
    
    for i in range(len(input)):
        # 将byte的后5位取反
        input[i] = input[i] ^ 0b00011111
        # ...
    return input

def decoder(text):
    if NO_ENCODE:
        return bytearray(text).decode()
    input = bytearray(text)
    # 转化成bytearray类型
    for i in range(len(input)):
        # 将byte的后5位取反
        input[i] = input[i] ^ 0b00011111
    
    return input.decode()

class NoticeParser:
    '''位于BCZ-Automata/src/notice_parser.py'''
    bad_word_path = '../BCZ-Notice-Examiner/assets/bad_words.json'
    enhanced_bad_word_path = '../BCZ-Notice-Examiner/assets/enhanced_bad_words.json'
    warn_word_path = '../BCZ-Notice-Examiner/assets/warn_words.bin'
    accept_word_path = '../BCZ-Notice-Examiner/assets/accept_words.bin'
    accept_notice_path = '../BCZ-Notice-Examiner/accept_notice.txt'
    bad_notice_path = '../BCZ-Notice-Examiner/bad_notice.txt'
    replace_dict_path = '../BCZ-Notice-Examiner/assets/replace_dict.json'
    replace_dict = {}
    
    # Chinese Characters: 4E00–9FA5
    # Dingbats: 0x2700-0x27BF
    # Ornamental Dingbats:  1F650–1F67F
    # Emoticons:  1F600–1F64F
    # Miscellaneous Symbols:  2600–26FF
    # Miscellaneous Symbols and Pictographs:  1F300–1F5FF
    # Supplemental Symbols and Pictographs:  1F900–1F9FF
    # Symbols and Pictographs Extended-A:  1FA70–1FAFF
    # Transport and Map Symbols:  1F680–1F6FF
    # Enclosed Alphanumeric Supplement:  1F100–1F1FF
    # Enclosed Ideographic Supplement:  1F200–1F2FF

    pattern = r'''[^\w\d
    \u4e00-\u9fa5
    \u2700-\u27BF
    \U0001F650-\U0001F67F
    \U0001F600-\U0001F64F
    \u2600-\u26FF
    \U0001F300-\U0001F5FF
    \U0001F900-\U0001F9FF
    \U0001FA70-\U0001FAFF
    \U0001F680-\U0001F6FF
    \U0001F100-\U0001F1FF
    \U0001F200-\U0001F2FF
    ]'''
    
    def __init__(self):
        self.bad_words = []
        if os.path.exists(self.bad_word_path):
            with open(self.bad_word_path, 'rb') as f:
                bin_data = f.read()
            self.bad_words = json.loads((bin_data))
        if os.path.exists(self.enhanced_bad_word_path):
            with open(self.enhanced_bad_word_path, 'rb') as f:
                bin_data = f.read()
            self.bad_words.extend(json.loads((bin_data)))

        try:
            self.replace_dict = json.load(open(self.replace_dict_path))
        except:
            print('replace_dict.json not found, using default replace_dict')
            self.replace_dict = {
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
                '〇': '0'
            }
    
        self.replace_keys = set(self.replace_dict.keys())
        self.warn_words = []
        self.invalid_storage = {} # {[]}
        self.notice_dict = {}
        self.most_recent_clear_date = 0 # timestamp

    def set_invalid_storage(self, position, char, length=1):
        for i in range(position, position+length):
            if i not in self.invalid_storage:
                self.invalid_storage[i] = [char]
            else:
                self.invalid_storage[i].append(char)


    def slice_invalid_char(self, text: str):
        # 去除并存储无效字符的位置
        # invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）','-','—','_']
        invalid_chars = ['_','丨','✔','\n',' ']
        self.invalid_storage = {}
        position = 0
        new_text = ""
        for char in text:
            if char in self.replace_dict:
                self.set_invalid_storage(position, char)
                position += 1
                new_text += self.replace_dict[char]
            elif re.match(self.pattern, char) is not None or char in invalid_chars:
                self.set_invalid_storage(position, char)
            elif char >= 'A' and char <= 'Z':
                self.set_invalid_storage(position, char)
                position += 1
                new_text += char.lower()
            else:
                position += 1
                new_text += char
        return new_text


    def restore_invalid_char_unaccept(self, text: str):
        # 插入无效字符
        bad = False # 优先级从高到低
        accept = False
        warn = False
        new_text = ""
        for position in range(len(text)):
            original_content_replaced = False
            auto_replaced = True if text[position] == '■' else False
            if position in self.invalid_storage:
                min_char = "9"
                min_char_cnt = 0
                for char in self.invalid_storage[position]:
                    if char.isdigit():
                        if char < min_char:
                            min_char = min(min_char, char)
                            min_char_cnt = 1
                        elif char == min_char:
                            min_char_cnt += 1
                    else:
                        if char in self.replace_keys or char >= 'A' and char <= 'Z':
                            if auto_replaced:
                                continue
                            else:
                                original_content_replaced = True
                        new_text += char
                if min_char == "1":
                    # continue
                    new_text += '\033[31m'
                    bad = True
                elif min_char == "2" and min_char_cnt > 1: # 必须要两次接受才是真的接受（代表双向）
                    # continue
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
            if not original_content_replaced:
                new_text += text[position]
        return new_text

    def filter_string(self, text: str):
        filtered_string = re.sub(self.pattern, '', text)

        # 传统方式
        # invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）','~','*','@','～','【','】','《','》','[',']','%','％','=','\\','\t','|','<','>','#','『','』','^','…']
        invalid_chars = ['_','丨','✔','\n',' ']

        for char in invalid_chars:
            filtered_string = filtered_string.replace(char, '')
        return filtered_string.lower()

    def parse_text(self, text: str) -> list:
        '''将文本解析长度为2的所有字串列表'''

        text = self.filter_string(text)

        for char in self.replace_dict:
            text = text.replace(char, self.replace_dict[char])
        result = []
        for i in range(len(text)-1):
            # result.append(text[i]) # 由于长度为1的子串意义不大，还占用空间
            t_str = text[i] + text[i+1]
            result.append(t_str)

        # if len(text) > 0:
        #     result.append(text[-1])
        return result

    def check_notice_auto(self, content: str, include_compulsory=False, clean_text=True) -> [str, int]:
        '''检查违规词，并替换为■'''
        if clean_text:
            content = self.slice_invalid_char(content)
            print("检测文本：" + content)
        else:
            self.invalid_storage = {}
        cnt = 0
        for check_word in self.bad_words:
            if not include_compulsory and (check_word[0] == '!' or check_word[0] == '?'):
                continue
            while True:
                posA, posB, result = self.cbw(check_word, content)
                
                if posA != -1:
                    if posB - posA > 4:
                        content = content[:posA] + '■■' + content[posA+2:posB-2] + '■■' + content[posB:]
                    else:
                        content = content[:posA] + '■'*(posB-posA) + content[posB:]
                    cnt += 1
                else:
                    break
        return self.restore_invalid_char_unaccept(content), cnt

    
    def check_notice(self, content: str, include_compulsory=False, clean_text=True):
        '''检查通知内容是否包含违规词汇（默认不包含强制违禁词）'''
        if clean_text:
            content = self.filter_string(content)
        for check_word in self.bad_words:
            if not include_compulsory and (check_word[0] == '!' or check_word[0] == '?'):
                continue
            posA, posB, result = self.cbw(check_word, content)
            if posA != -1:
                return posA, posB, result
        return -1, -1, ""


    def verify_bad_word(self, accept_notice: str) -> str:
        '''检查违禁词是否被包含在被接受的通知中'''
        log = ""
        for check_word in self.bad_words:
            posA, posB, result = self.cbw(check_word, accept_notice)
            if result != "":
                log += f'{check_word} 已存在于被接受的通知中 result:{result}'

        
    def cbw(self, check_word, accept_notice):
        if check_word[0] == '!' or check_word[0] == '?':
            check_word = check_word[1:]
        if check_word in accept_notice:
            idx = accept_notice.index(check_word)
            result = idx
            return idx, idx + len(check_word), accept_notice[result:result+len(check_word)+20]
        elif check_word[0] == '/': # 正则表达式
            try:
                s_result = re.search(check_word[1:-1], accept_notice)
            except:
                return -1, -1, "Invalid regular expression"
            if s_result:
                s = s_result.start()
                e = s_result.end()
                return s, e, accept_notice[s:e+20]
        elif '|' in check_word:
            sub_words = check_word.split('|')
            temp_accept_notice = accept_notice
            valid = True
            result = []
            result_pos = []
            accrue = 0 # 偏移量
            i = 0
            while i < len(sub_words):
                try:
                    sub_word = sub_words[i]
                    index = temp_accept_notice.index(sub_word)
                    # 提取到index_new位置
                    if i == 0 or '\\\\' not in temp_accept_notice[:index]: # 跨公告了，不算
                        result.append(temp_accept_notice[index:index+len(check_word)+20])
                        result_pos.append(index + accrue)
                        temp_accept_notice = temp_accept_notice[index+len(sub_word):]
                        accrue += index + len(sub_word)
                        i += 1
                    else:
                        # 重新查找上一个sub_word的位置
                        i -= 1
                        result.pop()
                        result_pos.pop()
                        continue
                except ValueError:
                    valid = False
                    break
            if valid:
                return result_pos[0], result_pos[-1] + len(sub_words[-1]), '|'.join(result)
        return -1, -1, ""

    def slice_accepted_text(self, text: str, accept_words: set) -> str:
        '''将坏文本中被接受两次的词汇去除'''
        text_set = set(self.parse_text(text))
        # 获取同时存在于text_set和accept_words中的词汇
        text_accept_set = text_set & accept_words
        valid_text = self.slice_invalid_char(text)
        for word in text_accept_set:
            # print(f'accept word: {word}')
            try:
                temp_valid_input_str = valid_text
                pos = 0
                while True:
                    # print(f'pos: {pos}')
                    pos += temp_valid_input_str.index(word)
                    temp_valid_input_str = valid_text[pos+len(word):]
                    self.set_invalid_storage(pos, f"2", length=len(word))   # 32m
                    pos += len(word)
            except ValueError:
                pass

        for pattern in self.bad_words:
            try:
                temp_valid_input_str = valid_text
                pos = 0
                while True:
                    pos += temp_valid_input_str.index(pattern)
                    temp_valid_input_str = valid_text[pos+len(pattern):]
                    self.set_invalid_storage(pos, "1", length=len(pattern)) # 31m
                    pos += len(pattern)
            except ValueError:
                pass
        return self.restore_invalid_char_unaccept(valid_text)
        
    def load_notice_from_db(self, conn: sqlite3.Connection=None):
        '''从数据库中读取所有通知'''
        close_conn = False
        if conn is None:
            conn = sqlite3.connect(default_notice_db_path, detect_types=0, uri=True)
            close_conn = True
        # 从数据库中读取近7天的公告
        week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).timestamp()
        cur = conn.cursor()
        cur.execute("SELECT GROUP_ID, CONTENT, DATE, LATEST_DATE, CHECKED FROM notice WHERE DATE >= ? OR LATEST_DATE >= ? ORDER BY DATE DESC", (week_ago, week_ago))
        notices = cur.fetchall()
        self.notice_dict = {}
        self.most_recent_clear_date = 0
        # 最多只接受两周内的公告
        # least_valid_date = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime('%Y-%m-%d 00:00:00')
        for notice in notices:
            group_id = notice[0]
            notice_content = notice[1]
            date = notice[2]
            latest_date = notice[3]
            checked = notice[4]
            if latest_date is None:
                latest_date = date
            if group_id not in self.notice_dict:
                self.notice_dict[group_id] = []
            self.notice_dict[group_id].append((notice_content, latest_date, checked))
            if notice_content.startswith('(空)') and date > self.most_recent_clear_date:
                self.most_recent_clear_date = date # 这里使用开始而不是最新日期
        # 遍历每个分类，找到公告被清空（以'(空)'开头）的那天
        print(f"most_recent_clear_date: {datetime.datetime.fromtimestamp(self.most_recent_clear_date).strftime('%Y-%m-%d %H-%M-%S')}")
        cur.close()
        if close_conn:
            conn.close()
        

    def update_notice(self, conn: sqlite3.Connection=None, only_raw_notice=False):
        '''导出数据库中（或已读取的）公告的接受、警告部分'''
        if len(self.notice_dict) == 0 or self.most_recent_clear_date == 0:
            self.load_notice_from_db(conn)
        warn_words = []
        accept_words = []
        accept_notice_list = []
        bad_notice_list = []
        for group_id, notice_list in self.notice_dict.items():
            # index_time = 0
            # for (notice, date, checked) in notice_list:
            #     if notice.startswith('(空)'): # 找到同一天的(空)的位置
            #         index_time = date
            #         break
            # if index_time != 0:
                for (notice, date, checked) in notice_list:
                    if checked is not None and checked < 200000000: # 同一天早些时候的公告
                        warn_words.extend(self.parse_text(notice))
                        bad_notice_list.append(notice)
                    if date >= self.most_recent_clear_date: # 同一天晚些时候的公告
                        if len(accept_words) < ACCEPT_WORDS_LIMIT:
                            accept_words.extend(self.parse_text(notice))
                        accept_notice_list.append(notice)
            # else:
                # 公告都没有被清空，且是当天的公告，全部加入到accept_words中
                # for (notice, date, checked) in notice_list:
                #     if date >= self.most_recent_clear_date:
                #         if len(accept_words) < ACCEPT_WORDS_LIMIT:
                #             accept_words.extend(self.parse_text(notice))
                #         accept_notice_list.append(notice)
        
        print(f"accept_notice_list: {len(accept_notice_list)}")
        print(f"bad_notice_list: {len(bad_notice_list)}")
        # 去重
        warn_words = set(warn_words)
        accept_words = set(accept_words)
        # 从warn_words中去除accept_words
        warn_words = warn_words - accept_words # accept_words是确定合规的
        # 写入json文件
        print(f'warn_words: {len(warn_words)}')
        print(f'accept_words: {len(accept_words)}')
        accept_fuzz = '\n\\\\\n'.join(accept_notice_list)
        print(f'accept_fuzz: {len(accept_fuzz)}')
        bad_fuzz = self.slice_accepted_text('\n'.join(bad_notice_list), accept_words)
        print(f'bad_fuzz: {len(bad_fuzz)}')
        self.verify_bad_word(accept_fuzz)

        with open(NoticeParser.accept_notice_path, 'w', encoding='utf-8') as f:
            f.write(accept_fuzz)
        with open(NoticeParser.bad_notice_path, 'w', encoding='utf-8') as f:
            f.write(bad_fuzz)
        

        if only_raw_notice:
            return

        def flatten(str):
            return str.replace(' ','')

        with open(NoticeParser.warn_word_path, 'wb') as f:
            f.write(encoder(flatten("\n".join(list(warn_words)))))
        with zipfile.ZipFile(f"{NoticeParser.warn_word_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(NoticeParser.warn_word_path, arcname=NoticeParser.warn_word_path)
            
        accept_words = list(accept_words)
        today_date = f"数据更新日期：{datetime.datetime.now().strftime('%Y-%m-%d')}"
        accept_words.insert(0, today_date)
        with open(NoticeParser.accept_word_path, 'wb') as f:
            f.write(encoder(flatten("\n".join(accept_words))))
        with zipfile.ZipFile(f"{NoticeParser.accept_word_path}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(NoticeParser.accept_word_path, arcname=NoticeParser.accept_word_path)
        

if __name__ == '__main__':
    '''测试用例：检查违禁词'''
    notice_parser = NoticeParser()
    while True:
        text = input("请输入要检查的通知：")
        print(notice_parser.check_notice(text))
        print("模糊词检查：")
        print(notice_parser.check_notice(text, include_compulsory=True))