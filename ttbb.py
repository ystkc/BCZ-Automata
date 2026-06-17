'''【独立工具】百词斩pk词库导出器（需要先运行自动pk程序收集答案）。可选段位、可筛掉简单词，用于导出为txt在其他软件例如墨墨中使用'''
import sqlite3
import datetime
import os

# 导出的文件分割数量
SPLIT_NUM = 2
# 需要导出的段位
rank_names = [
    # ('wood','wood'),
    # ('iron','iron'),
    # ('copper','copper'),
    # ('silver','silver'),
    # ('gold','gold'),
    # ('venus','venus'),
    ('crystal','crystal'),
    ('legend','legend'),
    ('wood,king','king,wood'),
    ('iron,king','king,iron'),
    ('copper,king','king,copper'),
    ('silver,king','king,silver'),
    ('gold,king','king,gold'),
    ('venus,king','king,venus'),
    ('crystal,king','king,crystal'),
    ('legend,king','king,legend'),
    ('king','king')
]
dir = "./ttbb/"
# 需要筛除的简单词的词书请自行下载，放在dir目录下
file_filters = [
    "大学英语六级考试大纲.txt",
    "四六级常考词组必备.txt",
    "2021恋练有词考研英语词组.txt",
    "英语专业四级大纲词汇.txt",
    "考研英语词汇词以类记.txt", # 可能有简单单词变形需要去除
    "6级词汇词以类记.txt"]
# 偏转词表（共SPLIT_NUM个，如果某个词存在于某个文件的偏转词表中，则该词顺延到下一个文件，若所有文件都不满足条件，则该词不导出并警告）
redir_filters = [
    "redir_1.txt",
    "redir_2.txt",
]
assert len(redir_filters) == SPLIT_NUM

if not os.path.exists(dir):
    os.makedirs(dir)

def load_wordlist(filename, result_set):
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line[0] == '#' or len(line) == 0:
                continue
            result_set.add(line)

# 读取简单词
easy_set = set()
for file_filter in file_filters:
    load_wordlist(dir + file_filter, easy_set)
# 读取偏转词
redir_set = []
for redir_filter in redir_filters:
    redir_set.append(set())
    load_wordlist(dir + redir_filter, redir_set[-1])

def rating(rank_str):
    ranks = rank_str.split(',')
    score = 0
    for rank in ranks:
        if rank == 'wood':
            score += -100
        elif rank == 'iron':
            score += -90
        elif rank == 'copper':
            score += -80
        elif rank =='silver':
            score += -70
        elif rank == 'gold':
            score += -60
        elif rank == 'venus':
            score += -50
        elif rank == 'crystal':
            score += -40
        elif rank == 'legends':
            score += -30
        else: score += 0 # king
    return score

path = "./lookup_patch.db"

conn = sqlite3.connect(path)

c = conn.cursor()

num = 0
datetime_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
fs = [open(f'{dir}ttbb{i}-{datetime_str}.txt', 'w', encoding='utf-8') for i in range(SPLIT_NUM)]
for rank_name in rank_names:
    c.execute("SELECT DISTINCT WORD FROM dict_bcz WHERE RANK = ? OR RANK = ? ORDER BY WORD ASC", (rank_name))
    for f in fs:
        f.write(f'\n\n\n\n#{rank_name[1]}\n\n')
    words = c.fetchall()
    for word in words:
        w = word[0]
        wl = w.lower()
        if w in easy_set or wl in easy_set:
            continue
        origin = num
        while num < SPLIT_NUM and w in redir_set[num] or wl in redir_set[num]:
            num = num + 1 if num < SPLIT_NUM - 1 else 0
            if origin == num:
                Warning(f'{w} is in every redir_set, ignored.')
                continue
        fs[num].write(f'{word[0]}\n')
        num = num + 1 if num < SPLIT_NUM - 1 else 0
conn.close()

