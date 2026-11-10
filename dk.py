# dk.py
'''【独立工具】快速打卡'''
from src.bcz import getCurrentBook, updateDoneData, getRandomWordIDInBook, daka
from src.thrift_utils import print_thrift_object, user_study, user_dict, http2_client
import os

os.chdir(os.path.dirname(__file__))
user_dict_obj = user_dict()
http2_client_obj = http2_client()
user_study_ = user_study(http2_client_obj=http2_client_obj)
try:
    os.chdir(os.path.dirname(__file__))
    token = input("请输入token：")
    book_id = getCurrentBook(token)
    print_thrift_object(updateDoneData(token, book_id, getRandomWordIDInBook('lookup.db', book_id, count=5, word_learnt=[])))
    date = input("请输入打卡日期（格式：20240829）：")
    print("上传不断电中")
    # 尝试根据token获取cookie，如果失败则用默认cookie填写
    user = user_dict_obj.get_user_dict_by_access_token(access_token=token)
    if user is None:
        # 默认cookie
        user = user_dict_obj.get_user_dict()
        user['cookie']['access_token'] = token
    print(user_study_.user_study_submit_win_streak_records(user_cookie=user['cookie'], user_config=user['config'], client_date=date))
    print_thrift_object(daka(token, date, 5))
except Exception as e:
    print(e)
input("按任意键退出...")