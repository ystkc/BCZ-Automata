# config.py
'''配置类'''
import os
import sys
import time
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self) -> None:
        '''配置类'''
        self.config_file = 'config.json'
        self.generated_config_file = 'generated.json'
        self.default_config_dict = {
            'host': '127.0.0.1',
            'port': 8850,
            'main_token': '', # 试用账号令牌
            'database_path': '../BCZ-Notice-Examiner/bcz_notice.db', # archiever储存库，含公告、用户、班级、连胜信息
            'notice_backup_db_dir': '../BCZ-Notice-Examiner/notice_backup', # 备份数据库目录
            'archiever_enable': False, # archiever开关，开启时每天固定时间爬取信息并储存
            'class_list_2048': [], # 如果要archiever额外爬取不在榜上的小班id，可以加入此处。不受archiever开关控制。
            "class_list_2048_sharekey_source": "http://127.0.0.1:8840", # 如果数据库内没有2048小班id对应的sharekey 则从此处获取（shadlc-BCZ-Group-Manager客户端地址）
            'dict_patch_db_path': 'lookup_patch.db', # pk补丁包，记录做过的题，减少查询和错误
            'puzzle_path': 'puzzle.db', # YZDD记录表
            'local': False, # 本地模式。开启时会每天固定时间执行同步、阻止休眠、允许休眠和关机命令
            'sync_command': [], # 每天早上执行一次，可以手动添加备份命令，或启动如订阅公告start subscribe.py等方便管理的小工具
            'prevent_sleep_command': 'timeout', # 每天傍晚执行一次，防止在晚上爬取数据时本地设备休眠而无法正常运行，功能：设置笔记本合盖操作无，睡眠永不，休眠永不
            'allow_sleep_command': 'timeout reverse', # 每天半夜数据爬取结束后执行一次，功能：睡眠3分钟，休眠3分钟
            'shutdown_delay_with_target': 23400, # 每天半夜数据爬取结束后执行一次，用于自动关机。当目标进程存在时执行
            'shutdown_delay_without_target': 90, # 同上，当目标进程不存在时执行
            'target_process_name': 'java.exe', # 关机时根据这个进程是否运行决定运行哪条关机指令
            'log_dir': './logs/', # 日志目录，包括daka、pk、subscribe、stargazer、cheat_tracker
            'check_notice_pace': 3, # 涉嫌违禁公告自动后往前查违禁步长。在公告前面加上#可以取消自动，加>改方向为前往后
            'pk_blacklist': [], # pk黑名单，遇到后改为强反挂模式。但属于被动反挂，对于极端挂无法获胜。反极端挂请使用stargazer
            'pk_whitelist': [], # pk白名单，遇到后禁用反挂，即便对方开挂也只会跟随分数
            'stargazer_enable': True, # 启动stargazer功能
            'stargazer_db': 'stargazer.db', # stargazer跟踪记录
            'anticheat_power': 10, # 初始反挂力度，最低0时第一手188，最高25时第一手199，建议5-10
            'do_not_charge_pk_energy': True, # 不使用铜板充能
            'arbiter_interval': 4.5, # arbiter发车时间间隔，单位秒，发车总时长=arbiter_size * arbiter_interval + arbiter_offset
            'arbiter_offset_win': 3, # arbiter对方胜利（或发现对方+2）后，开始下一轮的延迟，单位秒
            'arbiter_offset_lose': 2, # arbiter对方失败（或平局）后，开始下一轮的延迟，单位秒
            'arbiter_size': 8, # 建议最大值：总账号数 / (60秒每体力 * 10体力每次) * 30s每局 * 2，理论最大值18，还要测试确保带宽足够
            'bot_enabled_time': [['-1 * * * *','* * * * *']], # 启动和关闭机器人，每个元素为一个时间段，任一个-1则不启动，格式：min hour day month week，支持*,-语法
            'bot_uin': 123456789, # 机器人QQ号，用于自动回复
            'ws_uri': "ws://localhost:6100", # NapCat websocket服务器 地址
            'napcat_token': '', # NapCat登录令牌
            'whitelist_groups': [], # 允许使用的QQ群号列表
            'whitelist_users': [], # 允许使用的用户QQ号列表
            'base_group': 0 # 用于管理机器人的QQ群组
        }
        self.default_generated_config_dict = {
            'subscribe_class_list': []
        }
        self.initConfig()
        self.raw = self.read()
        self.host = self.raw.get('host', '127.0.0.1')
        self.port = self.raw.get('port', 8850)
        self.main_token = self.raw.get('main_token', '')
        if not self.main_token:
            raise Exception('请在config.json中设置main_token，最好不要加入任何小班，可用试用账号令牌')
        self.database_path = self.raw.get('database_path', '../BCZ-Notice-Examiner/bcz_notice.db')
        self.notice_backup_db_dir = self.raw.get('notice_backup_db_dir', '../BCZ-Notice-Examiner/notice_backup')
        self.local = self.raw.get('local', False)
        self.sync_command = self.raw.get('sync_command', [])
        self.prevent_sleep_command = self.raw.get('prevent_sleep_command', 'timeout')
        self.allow_sleep_command = self.raw.get('allow_sleep_command', 'timeout reverse')
        self.shutdown_delay_with_target = self.raw.get('shutdown_delay_with_target', 23400) # 90: 1.5分钟  23400:6.5小时
        self.shutdown_delay_without_target = self.raw.get('shutdown_delay_without_target', 90)
        self.target_process_name = self.raw.get('target_process_name', 'java.exe') # 关机时根据这个进程是否运行决定运行哪条关机指令
        self.log_dir = self.raw.get('log_dir', './logs/')
        self.check_notice_pace = self.raw.get('check_notice_pace', 3)
        self.puzzle_path = self.raw.get('puzzle_path', 'puzzle.db')
        self.dict_patch_db_path = self.raw.get('dict_patch_db_path', 'lookup_patch.db')
        self.archiever_enable = self.raw.get('archiever_enable', False)
        self.class_list_2048 = self.raw.get('class_list_2048', [])
        self.pk_blacklist = self.raw.get('pk_blacklist', [])
        self.pk_whitelist = self.raw.get('pk_whitelist', [])
        self.stargazer_enable = self.raw.get('stargazer_enable', True)
        self.stargazer_db = self.raw.get('stargazer_db','stargazer.db')
        self.anticheat_power = self.raw.get('anticheat_power', 10)
        self.do_not_charge_pk_energy = self.raw.get('do_not_charge_pk_energy', True)
        self.arbiter_interval = self.raw.get('arbiter_interval', 4.5)
        self.arbiter_offset_win = self.raw.get('arbiter_offset_win', 3)
        self.arbiter_offset_lose = self.raw.get('arbiter_offset_lose', 2)
        self.arbiter_size = self.raw.get('arbiter_size', 8)
        self.bot_enabled_time = self.raw.get('bot_enabled_time', [['-1 * * * *','* * * * *']])
        self.bot_uin = self.raw.get('bot_uin', 123456789)
        self.ws_uri = self.raw.get('ws_uri', "ws://localhost:6100")
        self.napcat_token = self.raw.get('napcat_token', '')
        self.whitelist_groups = self.raw.get('whitelist_groups', [])
        self.whitelist_users = self.raw.get('whitelist_users', [])
        self.base_group = self.raw.get('base_group', 0)
        # generated
        self.subscribe_class_list = self.raw.get('subscribe_class_list', [])
        self.verify()

    def initConfig(self):
        '''初始化配置文件'''
        try:
            if path := os.path.dirname(self.config_file):
                os.makedirs(path, exist_ok=True)
            open(self.config_file, encoding='utf-8')
            open(self.generated_config_file, encoding='utf-8')
        except:
            json.dump(self.default_config_dict, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            json.dump(self.default_generated_config_dict, open(self.generated_config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            logger.info('初次启动，已在当前执行目录生成配置文件，请修改配置后再次启动，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def read(self, key: str = '') -> list | dict | str | int | bool:
        '''获取指定配置'''
        try:
            json_data = json.load(open(self.config_file, encoding='utf-8'))
            json_data.update(json.load(open(self.generated_config_file, encoding='utf-8')))
            if key:
                json_data = json.load(open(self.config_file, encoding='utf-8')).get(key)
            return json_data
        except Exception as e:
            logger.error(f'配置文件读取异常: {e}，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def save(self, key, value: list | dict | str | int | bool = '') -> None:
        '''保存指定配置文件'''
        try:
            # 判断key属于哪个文件
            if key not in self.__dict__:
                raise AttributeError(f'配置项 {key} 不存在')
            self.__setattr__(key, value)
            if key in self.default_config_dict:
                json_data = json.load(open(self.config_file, encoding='utf-8'))
                json_data[key] = value
                json.dump(json_data, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            else:
                json_data = json.load(open(self.generated_config_file, encoding='utf-8'))
                json_data[key] = value
                json.dump(json_data, open(self.generated_config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    def verify(self):
        '''验证配置文件的完整性'''
        value = None