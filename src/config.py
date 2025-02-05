import os
import sys
import time
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self) -> None:
        '''配置类'''
        self.config_file = f'config.json'
        self.default_config_dict = {
            'host': '127.0.0.1',
            'port': 8850,
            'database_path': '../BCZ-Notice-Examiner/bcz_notice.db',
            'dict_patch_db_path': 'lookup_patch.db',
            'puzzle_path': 'puzzle.db',
            'main_token': '',
            'sync_command': [], # 每天早上执行一次，可以手动添加备份命令，或启动订阅公告start subscribe.py等方便管理的小工具
            'prevent_sleep_command': 'timeout',
            'allow_sleep_command': 'timeout reverse',
            'local': False,
            'log_dir': './logs/',
            'check_notice_pace': 3,
            'pk_blacklist': [],
            'pk_whitelist': [],
            'archiever_enable': False,
            'class_list_2048': [],
            'stargazer_enable': True,
        }
        self.initConfig()
        self.raw = self.read()
        self.host = self.raw.get('host', '')
        self.port = self.raw.get('port', '')
        self.database_path = self.raw.get('database_path', '')
        self.main_token = self.raw.get('main_token', '')
        self.local = self.raw.get('local', False)
        self.sync_command = self.raw.get('sync_command', [])
        self.prevent_sleep_command = self.raw.get('prevent_sleep_command', '')
        self.allow_sleep_command = self.raw.get('allow_sleep_command', '')
        self.log_dir = self.raw.get('log_dir', '')
        self.check_notice_pace = self.raw.get('check_notice_pace', 3)
        self.puzzle_path = self.raw.get('puzzle_path', 'puzzle.db')
        self.pk_blacklist = self.raw.get('pk_blacklist', [])
        self.pk_whitelist = self.raw.get('pk_whitelist', [])
        self.dict_patch_db_path = self.raw.get('dict_patch_db_path', '')
        self.archiever_enable = self.raw.get('archiever_enable', False)
        self.class_list_2048 = self.raw.get('class_list_2048', [])
        self.stargazer_enable = self.raw.get('stargazer_enable', True)
        self.verify()

    def initConfig(self):
        '''初始化配置文件'''
        try:
            if path := os.path.dirname(self.config_file):
                os.makedirs(path, exist_ok=True)
            open(self.config_file, encoding='utf-8')
        except:
            json.dump(self.default_config_dict, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            logger.info('初次启动，已在当前执行目录生成配置文件，请修改配置后再次启动，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def read(self, key: str = '') -> list | dict | str | int | bool:
        '''获取指定配置'''
        try:
            json_data = json.load(open(self.config_file, encoding='utf-8'))
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
            json_data = json.load(open(self.config_file, encoding='utf-8'))
            json_data[key] = value
            json.dump(json_data, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    def verify(self):
        '''验证配置文件的完整性'''
        value = None
        if self.host == '':
            key = 'host'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.host = value
        if self.port == '':
            key = 'port'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.port = value
        if self.database_path == '':
            key = 'database_path'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.database_path = value
        if self.main_token == '':
            key ='main_token'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.main_token = value
        if self.local == '':
            key = 'local'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.local = value
        if self.sync_command == []:
            key ='sync_command'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.sync_command = value
        if self.prevent_sleep_command == '':
            key = 'prevent_sleep_command'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.prevent_sleep_command = value
        if self.allow_sleep_command == '':
            key = 'allow_sleep_command'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.allow_sleep_command = value
        if self.log_dir == '':
            key = 'log_dir'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.log_dir = value
        if self.check_notice_pace == '':
            key = 'check_notice_pace'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.check_notice_pace = value
        if self.puzzle_path == '':
            key = 'puzzle_path'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.puzzle_path = value
        if self.pk_blacklist == []:
            key = 'pk_blacklist'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.pk_blacklist = value
        if self.pk_whitelist == []:
            key = 'pk_whitelist'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.pk_whitelist = value
        if self.dict_patch_db_path == '':
            key = 'dict_patch_db_path'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.dict_patch_db_path = value
        if self.archiever_enable == '':
            key = 'archiever_enable'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.archiever_enable = value
        if self.class_list_2048 == []:
            key = 'class_list_2048'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.class_list_2048 = value
        if self.stargazer_enable == '':
            key ='stargazer_enable'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.stargazer_enable = value
