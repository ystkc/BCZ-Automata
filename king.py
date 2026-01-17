# king.py
'''【独立工具】将所有允许pk的用户进行上段，到王者为止'''
from src.config import Config
from src.daka_utils import daka_list_class, stargazer_class, open_console_window
from src.http2_client import http2_client
import logging
import datetime
import traceback
import os
# 设置从当前文件的位置开始运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system('title king')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
config = Config()
http2_client_obj = http2_client()
daka_list_obj = daka_list_class(logger, http2_client_obj, config)
print("默认订阅账号：", daka_list_obj.user_dict_obj.subscriber_unique_ids)
print("默认虚拟账号：", daka_list_obj.user_dict_obj.arbiter_unique_ids)
print("请输入指定id(多个请用英文逗号分隔)，不输入默认全部订阅、虚拟账号")
mode = input("请确保账号信息已添加至数据库：")

if len(mode) > 0:
    ids = mode.split(',')
    int_id = 0
    int_ids = []
    for id in ids:
        try:
            int_id = int(id)
            uindex = daka_list_obj.user_dict_obj.get_index_by_unique_id(int_id)  # 由于历史遗留问题，如果数据库查找不到id会返回第一个账号
            user_config = daka_list_obj.user_dict_obj.get_config(uindex)
            user_cookie = daka_list_obj.user_dict_obj.get_cookie(uindex)
            config_id = user_config.get('unique_id', 0)
            assert config_id == int_id
            config_pk_status = user_config.get('can_pk', False)
            if not config_pk_status: 
                logger.warning(f"账号{config_id}配置为不允许PK，已临时允许")
                user_config['can_pk'] = True
                daka_list_obj.user_dict_obj.update_user_dict({'config': user_config, 'cookie': user_cookie}, save_to_db=False)
            int_ids.append(int_id)
        except ValueError:
            logger.error(f"id必须是数字:{id}")
            exit(0)
        except AssertionError:
            logger.error(f"数据库中没有找到id:{int_id}")
            exit(0)
    daka_list_obj.user_dict_obj.subscriber_unique_ids = set(int_ids)
    daka_list_obj.user_dict_obj.arbiter_unique_ids = set()
import queue
user_messages = queue.Queue()
star_gazer = stargazer_class(logger, http2_client_obj, config, daka_list_obj, user_messages, king=True)
star_gazer.start()
try:
    daka_list_obj.init_notice_storage()
except:
    http2_client_obj.set_closing_state(True)
    raise
os.system('title king - q to quit... p to check progress...')

def calc_progress(level, star):
    accumulated_star = 0
    if level == 'wood':
        accumulated_star = 0
    elif level == 'iron':
        accumulated_star = 3
    elif level == 'copper':
        accumulated_star = 6
    elif level =='silver':
        accumulated_star = 11
    elif level == 'gold':
        accumulated_star = 16
    elif level == 'venus':
        accumulated_star = 23
    elif level == 'crystal':
        accumulated_star = 30
    elif level == 'legend':
        accumulated_star = 39
    elif level == 'king':
        accumulated_star = 48
    return (accumulated_star + star)

try:
    s=" "
    items = ['name', 'id', '段位', '星级', '能量', '进度'] # 每个字段占16个字符
    items_str = ''.join([f'{item:<16}' for item in items])
    while s!="q":
        s = input("Press q to quit... p to check progress...\n\n\n")
        if s=="p":
            stars = 0
            users = len(daka_list_obj.user_dict_obj.subscriber_unique_ids)
            result = f"当前进度：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{users}个订阅token:\n{items_str}\n"
            for unique_id in daka_list_obj.user_dict_obj.subscriber_unique_ids:
                config = daka_list_obj.user_dict_obj.get_config(daka_list_obj.user_dict_obj.get_index_by_unique_id(unique_id))
                name = config.get('name', '未知')
                pk_infos = daka_list_obj.is_king.get(unique_id, ["unknown", 0, 60])
                st = calc_progress(pk_infos[0], pk_infos[1])
                stars += st
                result += f"{name:<16}{str(unique_id):<16}{str(pk_infos[0]):<16}{str(pk_infos[1]):<16}{str(pk_infos[2]):<16}{st}/49\n"
            users1 = len(daka_list_obj.user_dict_obj.arbiter_unique_ids)
            result += f"\n\n\n{users1}个裁判token:\n{items_str}\n"
            for unique_id in daka_list_obj.user_dict_obj.arbiter_unique_ids:
                config = daka_list_obj.user_dict_obj.get_config(daka_list_obj.user_dict_obj.get_index_by_unique_id(unique_id))
                name = config.get('name', '未知')
                pk_infos = daka_list_obj.is_king.get(unique_id, ["unknown", 0, 60])
                st = calc_progress(pk_infos[0], pk_infos[1])
                stars += st
                result += f"{name:<16}{str(unique_id):<16}{str(pk_infos[0]):<16}{str(pk_infos[1]):<16}{str(pk_infos[2]):<16}{st}/49\n"
            result += f"\n\n\n总进度：{stars}/{(users + users1)*49}\n\n\n\n\n\n\n\n\n"
            open_console_window(result)
            

except KeyboardInterrupt:
    pass
except Exception as e:
    traceback.print_exc()
    pass
os.system('title king - Exiting...')
http2_client_obj.set_closing_state(True)
daka_list_obj.close(no_check_daka=True, no_update_db=True)

