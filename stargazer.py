# stargazer.py
'''【独立工具】跟踪指定黑名单用户，并尝试匹配之。'''
from src.config import Config
from src.daka_utils import daka_list_class, stargazer_class, user_dict
from src.http2_client import http2_client
from src.bcz_group_utils import bczGroup
import logging
import os
# 设置从当前文件的位置开始运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system('title stargazer')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
config = Config()
http2_client_obj = http2_client()
user_dict_obj = user_dict()
bcz_group_obj = bczGroup(http2_client_obj, user_dict_obj, config)
daka_list_obj = daka_list_class(logger, http2_client_obj, user_dict_obj, config, bcz_group_obj)
import queue
user_messages = queue.Queue()
star_gazer = stargazer_class(logger, http2_client_obj, config, daka_list_obj, user_messages, king=False)
star_gazer.start()
try:
    daka_list_obj.init_notice_storage()
except:
    http2_client_obj.set_closing_state(True)
    raise
os.system('title stargazer - Press Enter to exit...')
try:
    input("Press Enter to exit...")
except:
    pass
os.system('title stargazer - Exiting...')
daka_list_obj.close(no_check_daka=True, no_update_db=True)
http2_client_obj.set_closing_state(True)

