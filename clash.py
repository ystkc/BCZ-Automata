import random
import pyperclip
import os
from pypinyin import pinyin, Style
from collections import defaultdict
from src.http2_client import http2_client
http2_client_obj = http2_client()
# from src.get_headers import getHeaders_by_access_token
from src.daka_utils import send_content
from src.thrift_utils import user_dict


os.chdir(os.path.dirname(os.path.abspath(__file__)))
user_dict_obj = user_dict()

PINYIN_TO_CHARS = defaultdict(list)

def build_homophones():
    with open("characters.txt", 'r', encoding='utf-8') as f:
        lines = f.read().strip().split()
    for line in lines:
        chars = line.split()
        if len(chars) == 0:
            continue
        if len(chars) == 1 and len(chars[-1]) >= 2: # 'X画'
            continue
        for char in chars:
            py = pinyin(char, style=Style.TONE, heteronym=False)[0][0]
            PINYIN_TO_CHARS[py].append(char)
    # 为每个字符加上其拼音
    # for py in PINYIN_TO_CHARS.keys():
    #     PINYIN_TO_CHARS[py].append(py)
    # print(PINYIN_TO_CHARS)

def get_homophones(char: str):
    py = pinyin(char, style=Style.TONE, heteronym=False)[0][0]
    return PINYIN_TO_CHARS[py]

MAXLEN = 999
INITLEN = input("请输入原始长度，用软件测量的，如果不确定就留空：")
if INITLEN == '':
    INITLEN = None
else:
    INITLEN = int(INITLEN)
def replace_with_homophones(text: str, ratio: float):
    if not 0 <= ratio <= 1:
        raise ValueError("ratio must be between 0 and 1")

    chars = list(text)
    
    
    # 保护 /maskstart 和 /maskend 之间的区域
    protected_indices = set()
    start_idx = None
    i = 0
    while i < len(chars):
        if chars[i] == '/' and i + 9 < len(chars) and ''.join(chars[i:i+10]) == '/maskstart':
            start_idx = i  # 删掉 /maskstart
            chars = chars[:i] + chars[i+10:]
        elif chars[i] == '/' and i + 7 < len(chars) and ''.join(chars[i:i+8]) == '/maskend':
            chars = chars[:i] + chars[i+8:]
            if start_idx is not None:
                for k in range(start_idx, i):
                    protected_indices.add(k)
                start_idx = None
        else:
            i += 1
    
    # 找出不能替换的区域（@到空格之间的内容）
    i = 0
    while i < len(chars):
        if chars[i] == '@':
            # 找到下一个空格
            j = i + 1
            while j < len(chars) and chars[j] != ' ':
                j += 1
            # 将@到空格（不包括空格）的所有索引加入保护
            for k in range(i, j):
                protected_indices.add(k)
            i = j  # 跳到空格位置
        i += 1
    
    
    # 在可替换区域内筛选出汉字索引，并排除保护区域
    hanzi_indices = []
    for i, char in enumerate(chars):
        if '\u4e00' <= char <= '\u9fff' and i not in protected_indices:
            hanzi_indices.append(i)

    currentlen = len(chars) if INITLEN is None else INITLEN
    n_replace = int(len(hanzi_indices) * ratio)
    to_replace = set(random.sample(hanzi_indices, n_replace)) if hanzi_indices else set()
    highlightchars = chars.copy()
    for i in to_replace:
        homophones = get_homophones(chars[i])
        if homophones:
            while True:
                target = random.choice(homophones)
                if len(target) - 1 + currentlen < MAXLEN:
                    break
            currentlen += len(target) - 1
            chars[i] = target
            highlightchars[i] = f"\033[31m{target}\033[0m"

    return "".join(chars), "".join(highlightchars)


if __name__ == "__main__":
    print("构建替换字表中...")
    build_homophones()
    text = t = input("输入文本（#结束）：")
    while True:
        t = input("输入文本（#结束）：")
        if t == '#':
            break
        text += t + '\n'

    ratio = float(input("替换比例（0~1）："))
    print(replace_with_homophones(text, ratio)[1])
    sharekey = input("尝试目标班sharekey:")
    unique_id = input("尝试unique_id:")
    # headers = getHeaders_by_access_token('group.baicizhan.com', access_token)
    attempts = int(input("循环尝试次数："))
    user_cookie = user_dict_obj.get_cookie(user_dict_obj.get_index_by_unique_id(unique_id))
    msg = None
    for i in range(attempts):
        content, highlightcontent = replace_with_homophones(text, ratio)
        print(highlightcontent)
        if input(f'上一次{msg}\n第{i}次执行确认？1确认') != '1':
            i -= 1
            continue
        msg = send_content(sharekey, content, user_cookie, http2_client_obj)
        if msg is None:
            input(f"发送成功，结果已复制{msg}")
            pyperclip.copy(content)
            break
        else:
            print(f"第{i}次发送失败{msg}")