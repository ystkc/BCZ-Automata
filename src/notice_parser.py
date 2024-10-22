import random
import sqlite3
import json

bad_word_path = '../BCZ-Notice-Examiner/warn_words.json'
accept_word_path = '../BCZ-Notice-Examiner/accept_words.json'
accept_notice_path = '../BCZ-Notice-Examiner/accept_notice.txt'
default_notice_db_path = '../BCZ-Notice-Examiner/bcz_notice.db'

def parse_text(text: str) -> list:
    '''将文本解析长度为2的所有字串列表'''
    invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）']
    for char in invalid_chars:
        text = text.replace(char, '')
    result = []
    for i in range(len(text)-1):
        result.append(text[i])
        result.append(text[i] + text[i+1])
    if len(text) > 0:
        result.append(text[-1])
    return result


def update_notice(conn: sqlite3.Connection):
    # 从数据库中读取所有通知
    cur = conn.cursor()
    cur.execute("SELECT * FROM notice ORDER BY DATE DESC")
    notices = cur.fetchall()
    # 按照notices[][0](NAME字段)分类
    notice_dict = {}
    notice_date = {}
    most_recent_clear_date = "1970-01-01 00:00:00"
    for notice in notices:
        share_key = notice[0]
        notice_content = notice[3]
        date = notice[4]
        if share_key not in notice_dict:
            notice_dict[share_key] = []
            notice_date[share_key] = [date]
        notice_dict[share_key].append(notice_content)
        notice_date[share_key].append(date)
        if notice_content.startswith('(空)') and date > most_recent_clear_date:
            most_recent_clear_date = date
    # 遍历每个分类，找到公告被清空（以'(空)'开头）的那天
    bad_words = []
    accept_words = []
    accept_notice_list = []
    for share_key, notice_list in notice_dict.items():
        length = len(notice_list)
        for i in range(0, length):
            if notice_list[i].startswith('(空)'):
                # if i>0:
                    # print(f'{share_key}的公告{i+1}被清空，总长度{length}')
                # if length >= 8:
                #     for notice in notice_list:
                #         print(notice)
                # 前面的公告加入到bad_words中
                for j in range(i+1):
                    accept_words.extend(parse_text(notice_list[j]))
                    accept_notice_list.append(notice_list[j])
                for j in range(i+1, length):
                    bad_words.extend(parse_text(notice_list[j]))
                break
        else:
            # 公告都没有被清空，且是最近的公告，全部加入到accept_words中
            for notice, date in zip(notice_list, notice_date[share_key]):
                if date >= most_recent_clear_date:
                    accept_words.extend(parse_text(notice))
                    accept_notice_list.append(notice)
                else:
                    bad_words.extend(parse_text(notice))
    # 去重
    bad_words = set(bad_words)
    accept_words = set(accept_words)
    # 从bad_words中去除accept_words
    bad_words = bad_words - accept_words # accept_words是确定合规的
    # 写入json文件
    print(f'bad_words: {len(bad_words)}')
    print(f'accept_words: {len(accept_words)}')
    with open(bad_word_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(list(bad_words), ensure_ascii=False))
    with open(accept_word_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(list(accept_words), ensure_ascii=False))
    with open(accept_notice_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(accept_notice_list))

if __name__ == '__main__':
    conn = sqlite3.connect(default_notice_db_path)
    update_notice(conn)
    conn.close()