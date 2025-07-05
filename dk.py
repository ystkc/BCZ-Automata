# dk.py
'''【独立工具】快速打卡'''
from src.bcz import getCurrentBook, updateDoneData, getRandomWordIDInBook, daka
from src.thrift_utils import print_thrift_object
import os
try:
    os.chdir(os.path.dirname(__file__))
    token = input("请输入token：")
    book_id = getCurrentBook(token)
    print_thrift_object(updateDoneData(token, book_id, getRandomWordIDInBook('lookup.db', book_id, count=5, word_learnt=[])))
    date = input("请输入打卡日期（格式：20240829）：")
    print_thrift_object(daka(token, date, 5))
except Exception as e:
    print(e)
input("按任意键退出...")