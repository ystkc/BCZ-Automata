# notice.py
'''【独立工具】用于检查通知违禁词'''
from src.notice_parser import NoticeParser
notice_parser = NoticeParser()
while True:
    text = input("请输入要检查的通知（#结束）：")
    result = text
    while text != "#":
        text = input("请输入要检查的通知（#结束）：")
        result += text
    print(notice_parser.check_notice(result))
    print("模糊词检查：")
    print(notice_parser.check_notice(result, include_compulsory=True))