# notice.py
'''【独立工具】用于检查通知违禁词（需要配合BCZ-Notice-Examiner(已更名为ystkc.github.io)库才能正常工作，将该库解压到这个库的同级平行文件夹即可，结构如下）
 root
 - BCZ-Automata
 - BCZ-Notice-Examiner
'''
from src.notice_parser import NoticeParser
import os
os.chdir(os.path.dirname(__file__))
notice_parser = NoticeParser()
while True:
    text = input("请输入要检查的通知（#结束）：")
    result = text
    while text != "#":
        text = input("请输入要检查的通知（#结束）：")
        result += text + '\n'
    print("\n\nfiltered：")
    print(notice_parser.filter_string(result))
    print("\n\n精确词检查：")
    print(notice_parser.check_notice_auto(result))
    print("\n\n模糊词检查：")
    print(notice_parser.check_notice_auto(result, include_compulsory=True))
    print("\n\n不清洗检查：")
    print(notice_parser.check_notice_auto(result, include_compulsory=True, clean_text=False))