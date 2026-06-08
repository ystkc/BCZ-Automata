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
        if len(chars) == 1 and len(chars[-1]) == 2: # 'X画'
            continue
        for char in chars:
            py = pinyin(char, style=Style.TONE, heteronym=False)[0][0]
            PINYIN_TO_CHARS[py].append(char)

def get_homophones(char: str):
    py = pinyin(char, style=Style.TONE, heteronym=False)[0][0]
    return PINYIN_TO_CHARS[py]

def replace_with_homophones(text: str, ratio: float):
    if not 0 <= ratio <= 1:
        raise ValueError("ratio must be between 0 and 1")

    chars = list(text)
    highlightchars = chars.copy()
    hanzi_indices = [
        i for i, c in enumerate(chars)
        if '\u4e00' <= c <= '\u9fff'
    ]

    n_replace = int(len(hanzi_indices) * ratio)
    to_replace = set(random.sample(hanzi_indices, n_replace))

    for i in to_replace:
        homophones = get_homophones(chars[i])
        if homophones:
            target = random.choice(homophones)
            chars[i] = target
            highlightchars[i] = f"\033[31m{target}\033[0m"

    return "".join(chars), "".join(highlightchars)


if __name__ == "__main__":
    print("构建替换字表中...")
    build_homophones()
    text = t = input("输入文本（#结束）：")
    while t != '#':
        t = input("输入文本（#结束）：")
        text += t

    ratio = float(input("替换比例（0~1）："))
    print(replace_with_homophones(text, ratio)[1])
    sharekey = input("尝试目标班sharekey:")
    unique_id = input("尝试unique_id:")
    # headers = getHeaders_by_access_token('group.baicizhan.com', access_token)
    attempts = int(input("循环尝试次数："))
    user_cookie = user_dict_obj.get_cookie(user_dict_obj.get_index_by_unique_id(unique_id))
    for i in range(attempts):
        content, highlightcontent = replace_with_homophones(text, ratio)
        print(highlightcontent)
        if input(f'第{i}次执行确认？1确认') != '1':
            i -= 1
            continue
        msg = send_content(sharekey, content, user_cookie, http2_client_obj)
        if msg is None:
            input(f"发送成功，结果已复制{msg}")
            pyperclip.copy(content)
        else:
            print(f"第{i}次发送失败{msg}")
