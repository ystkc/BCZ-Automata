'''thrift_utils，最底层的thrift接口，提供登录、注册、获取用户信息等基础功能'''

# RUN .\generator.bat
# thrift.exe -gen py d:/dotoro/project/#python/BCZ-Automata/src/thriftAPI


import traceback
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol

# 第一阶段：初始化
try:
    from src.thriftAPI.ttypes import *
    from src.thriftAPI import advertise_service, assistant_service, bcz_report_service, bcz_system_service, notify_service, report_event_service, resource_api_service, social_service, UnifiedUserService, UserStudyApiService
    from src.get_headers import getHeaders, bcz_info, get_device_str
    from src.http2_client import http2_client
except:
    from thriftAPI.ttypes import *
    from thriftAPI import advertise_service, assistant_service, bcz_report_service, bcz_system_service, notify_service, report_event_service, resource_api_service, social_service, UnifiedUserService, UserStudyApiService
    from get_headers import getHeaders, bcz_info, get_device_str
    from http2_client import http2_client
# import requests
import random
import gzip
import struct
import time
import json
# import httpx
# import certifi
import datetime
import threading


class user_dict:
    user_cookie_path = "user_cookie.json"
    def __init__(self):
        try:
            with open(self.user_cookie_path, 'r', encoding='utf-8') as f:
                self.__user_dict_list = json.load(f)
        except:
            print("账号信息为空，请访问/append/添加账号信息！")
            self.__user_dict_list = []

        self.modified = False
        self.arbiter_unique_ids = set()
        self.subscriber_unique_ids = set()
        self.unique_id_index = {}
        # 给用户分配索引（从0开始）
        for i, user_dict in enumerate(self.__user_dict_list):
            user_config = user_dict['config']
            user_config['user_index'] = i
            unique_id = user_config['unique_id']
            if user_config['arbiter']:
                self.arbiter_unique_ids.add(unique_id)
            if user_config['subscribe_notice']:
                self.subscriber_unique_ids.add(unique_id)
            self.unique_id_index[unique_id] = i

    def get_index_by_unique_id(self, unique_id:int=0):
        '''根据unique_id获取用户索引'''
        if unique_id == 0:
            return 0 # 默认第一个用户
        return self.unique_id_index.get(int(unique_id), None) # 找不到就返回None
    
    def get_access_token_by_unique_id(self, unique_id:int =0):
        index = self.get_index_by_unique_id(unique_id)
        if index is None:
            return None
        return self.__user_dict_list[index]['cookie']['access_token']
    
    def get_except_from_arbiter(self, dakaing_unique_ids: set, cnt, except_unique_id: set, daka_pk_status: dict, include_subscriber=False): # return the dict
        available = self.arbiter_unique_ids.copy()
        if include_subscriber:
            available = available.union(self.subscriber_unique_ids)
        available = available.difference(dakaing_unique_ids).difference(except_unique_id)
        results = []
        for id in available:
            index = self.unique_id_index[id]
            # if daka_pk_status.get(self.__user_dict_list[index]['config']['unique_id'], 0) == 2:
            #     continue # 能量耗尽的用户参与选取，在顶层剔除（防止和所有账户都被占用混淆）
            results.append(self.__user_dict_list[index])
            cnt -= 1
            if cnt == 0:
                break
        return results
    
    def format_user_strs(self, idx_start: int = 1, unique_ids:list = None):
        results = []
        if unique_ids:
            for uid in unique_ids:
                user_dict = self.__user_dict_list[self.unique_id_index.get(uid, 0)]
                user_config = user_dict['config']
                results.append(f"{idx_start}. {user_config.get('name', '未命名')}({uid}) 铜板{user_config.get('cooper', '未知')} 总班位{user_config.get('group_limit', '未知')} 可用{user_config.get('group_vacant', '未知')} 拥有小班{user_config.get('leader_group_cnt', '未知')}个 已授权{user_config.get('auth_group_cnt', '未知')}个")
                idx_start += 1
        return results
    
    def get_unique_ids(self, subscribe=True) -> set:
        '''返回unique_id列表，subscribe=True返回订阅用户，subscribe=False返回所有用户（包括订阅用户）'''
        if subscribe:
            return self.subscriber_unique_ids.copy()
        else:
            return set(self.unique_id_index.keys())

    def get_count(self):
        return len(self.__user_dict_list)
    
    def get_user_dict(self, index=0):
        return self.__user_dict_list[index]
    
    def get_config(self, index=0):
        return self.__user_dict_list[index]['config']
    
    def get_cookie(self, index=0):
        return self.__user_dict_list[index]['cookie']
    
    def get_user_dict_list(self):
        return self.__user_dict_list.copy()
    
    def update_user_dict(self, user_dict, save_to_db=True):
        unique_id = user_dict['config']['unique_id']
        index = self.get_index_by_unique_id(unique_id)
        if index is not None:
            self.__user_dict_list[index] = user_dict
            if save_to_db:
                self.modified = True
    
    def delete_user(self, unique_id):
        index = self.get_index_by_unique_id(unique_id)
        if index is not None:
            del self.__user_dict_list[index]
            self.modified = True
            self.save()

    def add_user(self, access_token, unique_id, name, device_id):
        new_user = {
            "config": {
                "book_id": 410,
                "name": name,
                "unique_id": int(unique_id),
                "adv_id": 166102,
                "timezone": "Asia/Shanghai",
                "device_name_ext": "DCO-AL00-HUAWEI",
                "app_channel": "Rongyao"
            },
            "cookie": {
                "access_token": access_token,
                "app_name": "7060100",
                "device_name": "android%2FDCO-AL00-HUAWEI",
                "client_time": "",
                "device_id": device_id,
                "serial": "",
                "channel": "qq",
                "version": "12",
                "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
                "bcz_dmid": "2a16dfbb",
                "device_version": "12",
            }
        }
        self.__user_dict_list.append(new_user)
        self.modified = True
        self.save()
    
    def del_user(self, unique_id):
        for i in range(len(self.__user_dict_list)):
            if self.__user_dict_list[i]['config']['unique_id'] == unique_id:
                del self.__user_dict_list[i]
                self.modified = True
                break
        self.save()


    def save(self): # 默认不保存退出，需要手动调用save()保存
        if self.modified:
            with open(user_dict.user_cookie_path, 'w', encoding='utf-8') as f:
                json.dump(self.__user_dict_list, f, indent=4, ensure_ascii=False)
            self.modified = False
    

report_json = [
    {# 0
        "event_id": "bcz_active_heartbeat_detail",
        "extra_info": "{\"period\":30,\"plan_type\":\"\"}",
        "log_time": "1725061321587",
        "product_id": "bcz_app",
        "stat_group": "heartbeat-common"
    },
    {# 1
        "event_id": "close-notify",
        "extra_info": "{\"adv_id\":\"100240167527175029\"}",
        "log_time": "1723850458343",
        "notify_title": "100240167527175029",
        "product_id": "bcz_app",
        "stat_group": "notify-popup"
    },
    {# 2
        "event_id": "enter-main-view",
        "log_time": "1725062704325",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 3
        "event_id": "homepage-book-adv-show",
        "extra_info": "{\"adv_id\":\"100213198904513909\",\"id\":\"100213198904513909\",\"book_id\":\"410\"}",
        "log_time": "1725062704865",
        "product_id": "bcz_app",
        "stat_group": "adv-common"
    },
    {# 4
        "event_id": "homepage-banner-show",
        "extra_info": "{\"adv_id\":\"166102\",\"id\":\"166102\"}",
        "log_time": "1725063038669",
        "product_id": "bcz_app",
        "stat_group": "adv-common"
    },
    {# 5
        "event_id": "push_curr_permission",
        "extra_info": "{\"status\":\"1\"}",
        "log_time": "1725063038837",
        "product_id": "bcz_app",
        "stat_group": "push-common"
    },
    {# 6
        "event_id": "cold_launch",
        "extra_info": "{\"device_id\":\"DCO-AL00-HUAWEI-8d946f2ddaf90f18\",\"channel\":\"Rongyao\"}",
        "log_time": "1725063036294",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 7 显示新单词
        "log_time": "1723850610168",
        "product_id": "bcz_app_h5",
        "stat_group": "study-detail-common",
        "event_id": "strategy_study_enter",
        "extra_info": "{\"topic_id\":8741,\"strategy_id\":\"q1\",\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 8 用户选择
        "log_time": "1723850603106",
        "product_id": "bcz_app_h5",
        "stat_group": "study-detail-common",
        "event_id": "choose_in_recite_click",
        "extra_info": "{\"topic_id\":16066,\"strategy_id\":\"q1\",\"choice_topic_id\":16066,\"is_right\":1,\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 9 显示单词
        "log_time": "1723850514619",
        "product_id": "bcz_app_h5",
        "stat_group": "study-detail-common",
        "event_id": "topic_wiki_show",
        "extra_info": "{\"topic_id\":4951,\"book_id\":410,\"channel\":\"study_mainstream\",\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 10 开始拼写
        "log_time": "1723850626993",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "begin-spelling-plan"
    },
    {# 11 完成拼写
        "log_time": "1723850651181",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "finish-spelling-plan",
        "extra_info": "{\"plan_type\":\"XModelNewStudy\"}"
    },
    {# 12 复习过渡页
        "log_time": "1723850655161",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "review_midpage_view",
        "extra_info": "{\"mode_type\":3}"
    },
    {# 13 复习过渡页点击
        "log_time": "1723850658350",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "review_midpage_click",
        "extra_info": "{\"mode_type\":3,\"button_type\":\"yes\"}"
    },
    {# 14 开始复习
        "log_time": "1723850658359",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "begin-normal-plan",
        "extra_info": "{\"mode_type\":3,\"button_text\":\"复习\",\"home_state\":{\"state\":\"learning\",\"data\":{\"reviewingPoolCount\":999}}}"
    },
    {# 15 完成复习
        "log_time": "1723850707920",
        "product_id": "bcz_app_h5",
        "stat_group": "main-study",
        "event_id": "finish-normal-plan",
        "extra_info": "{\"plan_type\":\"XModelReviewStudy\"}"
    },
    {# 16 学习数据同步完成页面
        "stat_group": "main-study",
        "event_id": "account_finished_data_show",
        "product_id": "bcz_app_h5",
        "log_time": "1723850723866",
        "extra_info": "{\"word_num\":7,\"experience\":20}"
    },
    {# 17 点击首页去打卡
        "event_id": "homepage-daka-click",
        "log_time": "1723850773934",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 18 访问打卡页面
        "event_id": "daka_page_visit",
        "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"\"}",
        "log_time": "1723850774922",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 19 点击分享到微信
        "event_id": "daka-to-wx",
        "log_time": "1723850788432",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 20 点击分享
        "event_id": "daka_share_channel_click",
        "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"6373\",\"share_channel\":\"weixin\"}",
        "log_time": "1723850788412",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 21 分享结束
        "event_id": "return-on-finish-plan-share",
        "extra_info": "{\"daka_type\":\"poster\",\"daka_poster_id\":\"6373\",\"share_channel\":\"weixin\"}",
        "log_time": "1723850883118",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 22 领取同桌奖励
        "log_time": "1723852063541",
        "product_id": "bcz_app_h5",
        "stat_group": "explore-common",
        "event_id": "together_recite_click",
        "extra_info": "{\"button\":\"coin\",\"channel\":\"deskmate\"}"
    },
    {# 23 班级签到
        "log_time": "1723852064583",
        "product_id": "bcz_app_h5",
        "stat_group": "explore-common",
        "event_id": "together_recite_click",
        "extra_info": "{\"button\":\"coin\",\"channel\":\"class\"}"
    },
    {# 24 班级段位奖励
        "log_time": "1723852064583",
        "product_id": "bcz_app_h5",
        "stat_group": "explore-common",
        "event_id": "together_recite_click",
        "extra_info": "{\"button\":\"coin\",\"channel\":\"class_level\"}"
    },
    {# 25 点击商城
        "event_id": "mall-tab-click",
        "log_time": "1723852206439",
        "product_id": "bcz_app",
        "stat_group": "main-study"
    },
    {# 26 加载商城
        "event_id": "mall-tab-click_extra_v2",
        "extra_info": "{\"servertype\":1,\"imageurl\":\"https://vol-v6.bczcdn.com/r/ltxwm285a8njpqetlsmf66453zsulws4.png\",\"taobaoinstalled\":false,\"aid\":\"10000\",\"jumptype\":1}",
        "log_time": "1723852206446",
        "product_id": "bcz_app",
        "stat_group": "h5-error"
    },
    {# 27 商城heartbeat
        "log_time": "1723852214632",
        "product_id": "bcz_app_h5",
        "stat_group": "bcz-mall-common",
        "event_id": "mall_carousel_show",
        "extra_info": "{\"trace\":\"bcz_app_main\",\"_path\":\"/homeV2\",\"banner_idx\":2,\"link_url\":\"https://learn.baicizhan.com/new_copper/link-to-duiba?linkTo=https%3A%2F%2Factivity-6.m.duiba.com.cn%2Fhdtool%2Findex%3Fid%3D272751389954266%26dbnewopen\"}"
    },
    {# 28 任务中心
        "stat_group": "activity-common",
        "event_id": "study_task_main_show",
        "product_id": "bcz_app_h5",
        "log_time": "1725581943815",
        "extra_info": "{\"task_id\":1631590}"# 最后一个任务
    },
    {# 29 pk加载
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_ActivityHomePageView",
        "product_id": "bcz_app_h5",
        "log_time": 1725754449459,
        "extra_info": "{\"ABPage\":\"B\"}"
    },
    {# 30 pk主页面
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_ArenaHomePageView",
        "product_id": "bcz_app_h5",
        "log_time": 1725754449945,
        "extra_info": "{\"SignStatus\":1}"
    },
    {# 31 进入pk准备页面
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_ArenaHomePageGoPKClick",
        "product_id": "bcz_app_h5",
        "log_time": 1725754453782,
        "extra_info": "{\"SignStatus\":1}"
    },
    {# 32 pk练习页面
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_PKPracticeMainPageView",
        "product_id": "bcz_app_h5",
        "log_time": 1725754453883,
        "extra_info": "{}"
    },
    {# 33 pk开始
        "stat_group": "activity-common",
        "event_id": "PKPracticePageBeginClick",
        "product_id": "bcz_app_h5",
        "log_time": 1725756092359,
        "extra_info": "{}"
    },
    {# 34 pk回合开始
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_PKPracticeChallengeBegin",
        "product_id": "bcz_app_h5",
        "log_time": 1725756094213,
        "extra_info": "{\"CurrentRound\":0}"
    },
    {# 35 pk匹配成功
        "stat_group": "activity-common",
        "event_id": "PKMatchSuccess",
        "product_id": "bcz_app_h5",
        "log_time": 1725756096025,
        "extra_info": "{\"MatchTime\":1811}"
    },
    {# 36 pk选择答案
        "stat_group": "activity-common",
        "event_id": "PKQuestionChoiceClick",
        "product_id": "bcz_app_h5",
        "log_time": 1725756102245,
        "extra_info": "{\"ContestId\":null,\"ChallengeId\":15034976,\"QuesOrder\":1,\"PuzzleId\":12656,\"ChoiceOrder\":3,\"CostTime\":2824,\"IsRight\":false}"
    },
    {# 37 pk结束
        "stat_group": "activity-common",
        "event_id": "BCZ_NCSVC_PKPracticeChallengeFinish",
        "product_id": "bcz_app_h5",
        "log_time": 1725756149177,
        "extra_info": "{\"CurrentRound\":1}"
    },
    {# 38 单词对战进入
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962138195",
        "event_id": "enter-pk-main",
        "extra_info": "{}"
    },
    {# 39 单词对战开始匹配
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962243878",
        "event_id": "begin-rank-pk",
        "extra_info": ""
    },
    {# 40 单词对战匹配开始
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962247178",
        "event_id": "pk_matched_enter",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585,\"cost_time\":3}"
    },
    {# 41 单词对战匹配完成
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1729302070692",
        "event_id": "pk_matched_done",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585,\"cost_time\":4}"
    },
    {# 42 匹配成功
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1729302071448",
        "event_id": "pk_success",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585,\"cost_time\":5}"
    },
    {# 43 作答完毕
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962255353",
        "event_id": "click_pk_detail_score",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"topic_id\":19480,\"challenge_id\":421585,\"puzzle_order\":1,\"score\":\"\",\"challenge_type\":\"排位赛\",\"cost_time\":5}"
    },
    {# 44 单词对战结束
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962285330",
        "event_id": "pk_over",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\",\"challenge_type\":\"排位赛\",\"challenge_id\":421585}"
    },
    {# 45 查看单词对战结果
        "product_id": "bcz_app_h5",
        "stat_group": "pk-common",
        "log_time": "1728962287866",
        "event_id": "enter_result",
        "extra_info": "{\"trace\":\"together_tab\",\"session_id\":\"40\",\"pk_rank\":\"1\"}"
    }
]




def generator(content):
    # 压缩数据
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    yield content

def print_thrift_object(obj, indent=0, index=-1, f=None):  
    """  
    递归打印Thrift对象及其嵌套结构  
    :param obj: Thrift对象  
    :param indent: 用于缩进的空格数  
    """  
    index_str = ''
    if index != -1:  
        index_str = f'[{index}]:'  
    indent_str = ' ' * indent  
    if isinstance(obj, dict):  
        for key, value in obj.items():  
            if f is not None:
                f.write(f'{indent_str}{index_str}{key}:\n')
            else:
                print(f"{indent_str}{index_str}{key}:")  
            print_thrift_object(value, indent + 4, f=f)  
    elif isinstance(obj, list):  
        for index, item in enumerate(obj):  
            print_thrift_object(item, indent, index = index, f=f)  
    elif hasattr(obj, '__dict__'):  
        # Thrift生成的类通常具有__dict__属性，包含字段名和值  
        for key, value in obj.__dict__.items():  
            # 忽略Thrift内部使用的属性，如thrift_spec, thrift_field_annotations等  
            if not key.startswith('_'):  
                if f is not None:
                    f.write(f'{indent_str}{index_str}{key}:\n')
                else:
                    print(f"{indent_str}{index_str}{key}:")  
                print_thrift_object(value, indent + 4, f=f)  
    else:  
        # 处理基本类型（如int, str等）  
        if isinstance(obj, str):
            if f is not None:
                f.write(f'{indent_str}{index_str}\'{obj}\'\n')
            else:
                print(f"{indent_str}{index_str}'{obj}'")  
        else:
            if f is not None:
                f.write(f'{indent_str}{index_str}{obj}\n')
            else:
                print(f"{indent_str}{index_str}{obj}")  
  

class bcz_system:
    def __init__(self, http2_client_obj: http2_client):
        self.http2_client_obj = http2_client_obj
    
    def send_http2_request(self, method, url, headers, content, jsonify=False):
        return self.http2_client_obj.send_http2_request(method, url, headers, content)
    
    def bcz_system_check_infos(self, user_cookie, user_config):
        '''check_infos'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_check_infos()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/check_infos/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_check_infos()
        transport.close()

        return result


    def bcz_system_get_switches(self, user_cookie, user_config):
        '''get_switches'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_switches()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_switches/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_switches()
        transport.close()

        return result


    def bcz_system_get_static_config(self, user_cookie, user_config):
        '''get_static_config'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_static_config()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_static_config/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_static_config()
        transport.close()

        return result


    def bcz_system_get_domain_whitelist(self, user_cookie, user_config):
        '''get_domain_whitelist'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_domain_whitelist()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_domain_whitelist/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()    


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_domain_whitelist()
        transport.close()

        return result


    def bcz_system_get_privacy_agreement_version(self, user_cookie, user_config):
        '''get_privacy_agreement_version'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        client.send_get_privacy_agreement_version()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_privacy_agreement_version/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_privacy_agreement_version()
        transport.close()

        return result


    def bcz_system_get_app_beta_update_info(self, user_cookie, user_config):
        '''get_app_beta_update_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        
        args = AppBetaUpdateRequest(
            device_id=user_cookie['device_id'],
            device_manufacturer=bcz_info.device_manufacturer,
            device_model=bcz_info.device_model,
            os_name=bcz_info.os_name,
            os_sdk=bcz_info.os_sdk,
            short_version=bcz_info.short_version,
            long_version=bcz_info.long_version,
            app_channel=user_cookie['channel'],
            app_name=bcz_info.app_name,
        )
        client.send_get_app_beta_update_info(args)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$system", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_system/get_app_beta_update_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()


        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_system_service.Client(protocol)
        result = client.recv_get_app_beta_update_info()
        transport.close()

        return result
    
class advertise:
    
    def __init__(self, http2_client_obj: http2_client):
        self.http2_client_obj = http2_client_obj
    
    def send_http2_request(self, method, url, headers, content, jsonify=False):
        return self.http2_client_obj.send_http2_request(method, url, headers, content)
    
    def advertise_get_startup_ad(self, user_cookie, user_config, screen_length=1920, screen_width=1080):
        '''get_startup_ad'''
        oaid = bcz_info.oaid
        android_id = user_cookie['device_id']
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        args = StartupAdRequest(screen_length=screen_length, screen_width=screen_width, android_id=android_id, oaid=oaid)
        client.send_get_startup_ad(args)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_startup_ad/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_startup_ad()
        transport.close()

        return result


    def advertise_get_mall_tab_icon_info(self, user_cookie, user_config):
        '''get_mall_tab_icon_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_mall_tab_icon_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_mall_tab_icon_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_mall_tab_icon_info()
        transport.close()

        return result


    def advertise_get_practice_popup_adv(self, user_cookie, user_config):
        '''get_practice_popup_adv'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_practice_popup_adv()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_practice_popup_adv/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_practice_popup_adv()
        transport.close()

        return result


    def advertise_get_explore_popup_adv(self, user_cookie, user_config):
        '''get_explore_popup_adv'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_explore_popup_adv()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_explore_popup_adv/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_explore_popup_adv()
        transport.close()

        return result


    def advertise_get_loading_ad_items(self, user_cookie, user_config):
        '''get_loading_ad_items'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_loading_ad_items()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_loading_ad_items/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_loading_ad_items()
        transport.close()

        return result


    def advertise_get_loading_ad_info(self, user_cookie, user_config):
        '''get_loading_ad_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_loading_ad_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_loading_ad_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_loading_ad_info()
        transport.close()

        return result


    def advertise_get_live_streaming_info(self, user_cookie, user_config):
        '''get_live_streaming_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_live_streaming_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_live_streaming_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_live_streaming_info()
        transport.close()

        return result


    def advertise_get_main_view_bottom_advs_v2(self, user_cookie, user_config) -> BottomAdvInfos:
        '''get_main_view_bottom_advs_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_main_view_bottom_advs_v2()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_main_view_bottom_advs_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_main_view_bottom_advs_v2()
        transport.close()

        return result


    def advertise_get_main_view_top_banner_advs(self, user_cookie, user_config) -> list:
        '''get_main_view_top_banner_advs'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_main_view_top_banner_advs()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_main_view_top_banner_advs/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_main_view_top_banner_advs()
        transport.close()

        return result

    def advertise_get_practice_banner_adv(self, user_cookie, user_config):
        '''get_practice_banner_adv'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        client.send_get_practice_banner_adv()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$advertise", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/advertise/get_practice_banner_adv/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = advertise_service.Client(protocol)
        result = client.recv_get_practice_banner_adv()
        transport.close()

        return result   
    
class user_study:
    
    def __init__(self, http2_client_obj: http2_client):
        self.http2_client_obj = http2_client_obj
    
    def send_http2_request(self, method, url, headers, content, jsonify=False):
        return self.http2_client_obj.send_http2_request(method, url, headers, content)
    
    def user_study_user_basic_info_v2(self, user_cookie, user_config):
        '''user_basic_info_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_user_basic_info_v2()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/user_basic_info_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_user_basic_info_v2()
        transport.close()

        return result


    def user_study_get_user_study_config(self, user_cookie, user_config):
        '''get_user_study_config'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_user_study_config()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_user_study_config/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_user_study_config()
        transport.close()

        return result


    def user_study_get_user_study_mode(self, user_cookie, user_config):
        '''get_user_study_mode'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_user_study_mode()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_user_study_mode/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_user_study_mode()
        transport.close()

        return result




    def user_study_user_limit_info_v2(self, user_cookie, user_config):
        '''user_limit_info_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_user_limit_info_v2()    
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/user_limit_info_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_user_limit_info_v2()
        transport.close()

        return result


    def user_study_win_streak_status(self, user_cookie, user_config, date=int(datetime.datetime.now().strftime('%Y%m%d'))):
        '''win_streak_status'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_win_streak_status(date)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/win_streak_status/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_win_streak_status()
        transport.close()

        return result

    def user_study_submit_win_streak_records(self, user_cookie, user_config, client_date=int(datetime.datetime.now().strftime('%Y%m%d'))):
        '''submit_win_streak_records'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        try:
            client_date = int(client_date)
        except:
            client_date = int(datetime.datetime.now().strftime('%Y%m%d'))
        client.send_submit_win_streak_records(client_date=client_date, win_streak_dates=[client_date])
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/submit_win_streak_records/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_submit_win_streak_records()
        transport.close()

        result = f"{result}.{client_date}.{datetime.datetime.now().strftime('%Y%m%d')}"

        return result


    def user_study_get_books_replace_info(self, user_cookie, user_config):
        '''get_books_replace_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_books_replace_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_books_replace_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_books_replace_info()
        transport.close()

        return result


    def user_study_get_main_page_js(self, user_cookie, user_config):
        '''get_main_page_js'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_main_page_js()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_main_page_js/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_main_page_js()
        transport.close()

        return result

    def user_study_user_daka_v2(self, user_cookie, user_config, daka_dates=[]):
        '''user_daka_v2
        params: daka_dates: list of (year, month, day, timestamp), the whole month(1 to today), ascending'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        user_daka_dates = []

        def get_this_month_timestamp(year, month, day):
            # 获取当月第一天的日期
            timestamp = int(datetime.datetime(year, month, 1).timestamp()) + 1
            result = []
            for i in range(day):
                result.append([year, month, i+1, timestamp + i*86400])
            return result
        
        if daka_dates == []:
            today_date = datetime.datetime.now().date()
            year = today_date.year
            month = today_date.month
            day = today_date.day
            daka_dates = get_this_month_timestamp(year, month, day)

        for date in daka_dates:
            user_daka_dates.append(UserDakaDate(year=date[0], month=date[1], day=date[2], timestamp=date[3]))
        
        client.send_user_daka_v2(UserDakaRequest(
            book_id = user_config['book_id'],
            count = 7,# 今日学习+复习单词数
            daka_dates=user_daka_dates,
            timezone=user_config['timezone'],
            client_date=user_daka_dates[-1],
            poster_topic_ids=[]
        ))
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/user_daka_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_user_daka_v2()
        transport.close()

        return result


    def user_study_get_train_page_resource(self, user_cookie, user_config):
        '''get_train_page_resource'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_train_page_resource()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_train_page_resource/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_train_page_resource()
        transport.close()

        return result
    
    def user_study_update_done_data(self, user_cookie, user_config, done_data={}):
        '''update_done_data
        params: done_data: dict{topicId:{current_score, span_days, used_time, done_times, wrong_times, is_first_do_at_today, tag_id, spell_score, listening_score, chn_score, review_round}} '''
        word_list = []
        for topic_id, data in done_data.items():
            word_list.append(UserDoneWordRecord(
                word_topic_id=int(topic_id),
                current_score=data['current_score'],
                span_days=data['span_days'],
                used_time=data['used_time'],
                done_times=data['done_times'],
                wrong_times=data['wrong_times'],
                is_first_do_at_today=data['is_first_do_at_today'],
                tag_id=data['tag_id'],
                spell_score=data['spell_score'],
                listening_score=data['listening_score'],
                chn_score=data['chn_score'],
                review_round=data['review_round']
            ))
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        time_stamp_short = int(time.time())
        client.send_update_done_data(
            last_sync_at=time_stamp_short,
            arr_done_records=word_list,
            current_word_level_id=user_config['book_id'],
            is_today_completed=True
        )
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/update_done_data/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_update_done_data()
        transport.close()

        return result
    
    def user_study_submit_experience_record(self, user_cookie, user_config, word_count=5, wrong_count=1, review_count=5, review_wrong_count=1):
        '''submit_experience_record
        params: experience_record: list of experiences'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        experience_list = [
            StudyExperienceRecord(
                # 已知：behavior: 1 第一次正确 2 改正 3 第一次错误 4 点击下一个的次数
                # 斩的不计入正确或更正，只计入错误
                questionType='deep-learning-one',
                behavior=1,
                cnt=word_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-two',
                behavior=1,
                cnt=word_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-three',
                behavior=1,
                cnt=word_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=1,
                cnt=word_count - wrong_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=2,
                cnt=wrong_count
            ),
            StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=3,
                cnt=word_count
            )]
        if review_count > 0:
            experience_list.extend([
                StudyExperienceRecord(
                    questionType='deep-review-one',
                    behavior=1,
                    cnt=review_count
                ),
                StudyExperienceRecord(
                    questionType='deep-review-spell',
                    behavior=1,
                    cnt=review_count - review_wrong_count
                ),
                StudyExperienceRecord(
                    questionType='deep-review-spell',
                    behavior=2,
                    cnt=review_wrong_count
                ),
                StudyExperienceRecord(
                    questionType='deep-review-spell',
                    behavior=3,
                    cnt=review_wrong_count
                )
            ])
        
        if random.random() < 0.5:
            experience_list.append(StudyExperienceRecord(
                questionType='deep-learning-spell',
                behavior=4,
                cnt=1
            ))
        if random.random() < 0.5:
            experience_list.append(StudyExperienceRecord(
                questionType='deep-review-spell',
                behavior=4,
                cnt=1
            ))
        client.send_submit_experience_record(experience_list)
            
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/submit_experience_record/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_submit_experience_record()
        transport.close()

        return result
    
    def get_daka_background_datas(self, learn_list, user_cookie, user_config):
        '''get_daka_background_datas'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_get_daka_background_datas(learn_list)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/get_daka_background_datas/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_get_daka_background_datas()
        transport.close()

        return result
    
    def user_study_share_bonus(self, user_cookie, user_config):
        '''share_bonus'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        time_long = int(time.time() * 1000)
        client.send_share_bonus(client_timestamp_ms = time_long)
        content = transport.getvalue()
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/share_bonus/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_share_bonus()
        transport.close()

        return result
    
    def user_study_credit_task_center(self, user_cookie, user_config):
        '''credit_task_center'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        client.send_credit_task_center()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/credit_task_center/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_credit_task_center()
        transport.close()

        return result
    # void upload_task_action(1: list<TaskUploadReq> req) throws (1: LogicException bomb, 2: SystemException boom)
    def user_study_upload_task_action(self, user_cookie, user_config, task_upload_req_list=[]):
        '''upload_task_action
        args: list[[action, cnt]]
        actions: learnMore'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        task_upload_req_list = [TaskUploadReq(action=action, cnt=cnt) for action, cnt in task_upload_req_list]
        client.send_upload_task_action(task_upload_req_list)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$learn", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/user_study/upload_task_action/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UserStudyApiService.Client(protocol)
        result = client.recv_upload_task_action()
        transport.close()

        return result

    

class unified_user:
    
    def __init__(self, http2_client_obj: http2_client):
        self.http2_client_obj = http2_client_obj
    
    def send_http2_request(self, method, url, headers, content, jsonify=False):
        return self.http2_client_obj.send_http2_request(method, url, headers, content)
    
    def unified_user_get_bind_info(self, user_cookie, user_config):
        '''get_bind_info'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        client.send_get_bind_info()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$passport", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/unified_user_service/get_bind_info/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        result = client.recv_get_bind_info()
        transport.close()

        return result


    def unified_user_check_access_token(self, user_cookie, user_config):
        '''check_access_token'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        client.send_check_access_token(get_device_str(user_cookie['device_id']))
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$passport", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/unified_user_service/check_access_token/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        result = client.recv_check_access_token()
        transport.close()

        return result

    def unified_user_update_role_extra(self, user_cookie, user_config, grade=1, role_up=1):
        '''update_role_extra
        grade始终为1，role_up义务教育1-9、高中10-12，大学14-19，成人23-24
        '''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        client.send_update_role_extra(grade=grade, role_up=role_up)
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$passport", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/unified_user_service/update_role_extra/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = UnifiedUserService.Client(protocol)
        result = client.recv_update_role_extra()
        transport.close()

        return result

class assistant:
    
    def __init__(self, http2_client_obj: http2_client):
        self.http2_client_obj = http2_client_obj
    
    def send_http2_request(self, method, url, headers, content, jsonify=False):
        return self.http2_client_obj.send_http2_request(method, url, headers, content)
    
    def assistant_check_feedback_msg(self, user_cookie, user_config):
        '''check_feedback_msg'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        client.send_check_feedback_msg(get_device_str(user_cookie['device_id']))
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$assistant", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/assistant/check_feedback_msg/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        result = client.recv_check_feedback_msg()
        transport.close()

        return result

    def assistant_get_activity_updated_time(self, user_cookie, user_config):
        '''get_activity_updated_time'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        client.send_get_activity_updated_time()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$assistant", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/assistant/get_activity_updated_time/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        result = client.recv_get_activity_updated_time()
        transport.close()

        return result


    def assistant_get_beta_user_types_v2(self, user_cookie, user_config):
        '''get_beta_user_types_v2'''
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        client.send_get_beta_user_types_v2()
        content = transport.getvalue()
        time_long = int(time.time() * 1000)
        headers = getHeaders("$assistant", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/assistant/get_beta_user_types_v2/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = self.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = assistant_service.Client(protocol)
        result = client.recv_get_beta_user_types_v2()
        transport.close()

        return result



def get_report_event_jsons(args: list, thrift=True) -> list[str]:
    jsons = []
    for arg in args:
        json_dict = report_json[arg['index']].copy()
        json_dict['log_time'] = str(int(time.time() * 1000))
        if 'extra_info' in arg:
            json_dict['extra_info'] = arg['extra_info']
        if thrift:
            jsons.append(json.dumps(json_dict, ensure_ascii=False))
        else:
            jsons.append(json_dict)
    return jsons

def report_event(user_cookie, user_config, http2_client_obj:http2_client, jsons=[], type=0, host=0):
    '''report_event
    args:jsons[{"index":int,"extra_info":str}]
    type:0 thrift; 1 json
    host:0 events; 1 system(only for json)'''
    time_long = int(time.time() * 1000)
    if type == 0:
        transport = TTransport.TMemoryBuffer()
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_report_service.Client(protocol)
        client.send_report_event(get_report_event_jsons(jsons))
        content = transport.getvalue()
        headers = getHeaders("$report", user_cookie, int(time.time()))
        url = f'https://{headers["Host"]}/rpc/bcz_report/report_event/{time_long}'
        content = gzip.compress(struct.pack("!i", len(content)) + content)
        response = http2_client_obj.send_http2_request('POST', url, headers, content)
        transport.close()

        result = response.content[4:]
        transport = TTransport.TMemoryBuffer(result)
        protocol = TCompactProtocol.TCompactProtocol(transport)
        client = bcz_report_service.Client(protocol)
        result = client.recv_report_event()
        transport.close()
        return result
    else:
        if host == 0:
            headers = getHeaders('$report', user_cookie, int(time.time()), index=1, quote=True)
            # https://events.baicizhan.com/api/system/report_event
        else:
            headers = getHeaders('$system', user_cookie, int(time.time()), index=1, quote=True)
        headers['Content-Type'] = 'text/plain'

        # https://system.baicizhan.com/api/system/report_event
        # https://events.baicizhan.com/api/system/report_event_without_login
        if jsons[0].get('without_login', False) == True:
            url = f'https://{headers["Host"]}/api/system/report_event_without_login'
        else:
            url = f'https://{headers["Host"]}/api/system/report_event'
        result = http2_client_obj.send_http2_request('POST', url, headers, json.dumps(get_report_event_jsons(jsons, False), ensure_ascii=False))

        return result


    

# 下面是notify接口
def notify_get_remind_info(user_cookie, user_config, http2_client_obj:http2_client):
    '''get_remind_info'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    client.send_get_remind_info()
    content = transport.getvalue()
    time_long = int(time.time() * 1000)
    headers = getHeaders("$notify", user_cookie, int(time.time()))
    url = f'https://{headers["Host"]}/rpc/notify/get_remind_info/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = http2_client_obj.send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    result = client.recv_get_remind_info()
    transport.close()

    return result

def notify_get_latest_notify(user_cookie, user_config, http2_client_obj:http2_client):
    '''get_latest_notify'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    client.send_get_latest_notify()
    content = transport.getvalue()
    time_long = int(time.time() * 1000)
    headers = getHeaders("$notify", user_cookie, int(time.time()))
    url = f'https://{headers["Host"]}/rpc/notify/get_latest_notify/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = http2_client_obj.send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = notify_service.Client(protocol)
    result = client.recv_get_latest_notify()
    transport.close()

    return result

# 下面是resource接口
def resource_get_book_resource_update_info(user_cookie, user_config, http2_client_obj:http2_client):
    '''get_book_resource_update_info'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = resource_api_service.Client(protocol)
    book_id = user_config['book_id']
    client.send_get_book_resource_update_info(book_id)
    content = transport.getvalue()
    time_long = int(time.time() * 1000)
    headers = getHeaders("$resource", user_cookie, int(time.time()))
    url = f'https://{headers["Host"]}/rpc/resource_api/get_book_resource_update_info/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = http2_client_obj.send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = resource_api_service.Client(protocol)
    result = client.recv_get_book_resource_update_info()
    transport.close()

    return result

def social_send_share_success(user_cookie, user_config, http2_client_obj:http2_client, channel=1):
    '''send_share_success'''
    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = social_service.Client(protocol)
    time_long = int(time.time() * 1000)
    client.send_send_share_success(module_name=0, timestamp=time_long, channel=channel)
    content = transport.getvalue()
    headers = getHeaders("$DATA", user_cookie, int(time.time()))
    # https://www.baicizhan.com/rpc/socials/send_share_success/1723850883199
    url = f'https://{headers["Host"]}/rpc/socials/send_share_success/{time_long}'
    content = gzip.compress(struct.pack("!i", len(content)) + content)
    response = http2_client_obj.send_http2_request('POST', url, headers, content)
    transport.close()

    result = response.content[4:]
    transport = TTransport.TMemoryBuffer(result)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    client = social_service.Client(protocol)
    result = client.recv_send_share_success()
    transport.close()

    return result

class thrift_logger:
    def __init__(self):
        self.f = open(f'log{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.txt', 'w', encoding='utf-8')
        self.threads = []
        self.lock = threading.Lock()

    
    def run(self, generator):
        def threaded_run(name, generator):
            result = []
            for i in generator:
                result.append(i)
            with self.lock:
                # print(f'\033[1;37m--[{name}]\033[0m\n')
                self.f.write(f'\n\n\n\n\n\n# 🌟[{name}]\n')
                for i in result:
                    # print(f'\033[1;36m[{i.__class__.__name__}]\033[0m\n')
                    self.f.write(f'## ❄️[{i.__class__.__name__}]\n')
                    print_thrift_object(i, f=self.f)
        self.threads.append(threading.Thread(target=threaded_run, args=(generator.__name__, generator)))
        self.threads[-1].start()

    def close(self):
        for t in self.threads:
            t.join()
        self.f.close()

    def __del__(self):
        self.close()

class cold_launch:
    '''模仿bcz客户端冷启动，将读取到的数据写入txt日志'''
    def __init__(self, http2_client_obj:http2_client):
        self.http2_client_obj = http2_client_obj
    # fiddler_filter: regex:^https://system\.baicizhan\.com.+(0|1|2|3|4|5|6|7|8|9)$
    def user_study_cold_launch(self, user_cookie, user_config, cold_launch=True, daka_dates=[]):
        '''user_study_cold_launch'''
        user_study_ = user_study(self.http2_client_obj)
        if cold_launch:
            yield user_study_.user_study_user_basic_info_v2(user_cookie, user_config)
            yield user_study_.user_study_get_user_study_config(user_cookie, user_config)
            yield user_study_.user_study_get_user_study_mode(user_cookie, user_config)
        yield user_study_.user_study_user_limit_info_v2(user_cookie, user_config)
        yield user_study_.user_study_win_streak_status(user_cookie, user_config)
        if cold_launch:
            yield user_study_.user_study_get_books_replace_info(user_cookie, user_config)
            yield user_study_.user_study_get_main_page_js(user_cookie, user_config)
            yield user_study_.user_study_user_daka_v2(user_cookie, user_config, daka_dates=daka_dates)
            yield user_study_.user_study_get_train_page_resource(user_cookie, user_config)


    def bcz_system_cold_launch(self, user_cookie, user_config, cold_launch=True):
        '''bcz_system_cold_launch'''
        bcz_system_ = bcz_system(self.http2_client_obj)
        yield bcz_system_.bcz_system_check_infos(user_cookie, user_config)
        if cold_launch:
            yield bcz_system_.bcz_system_get_switches(user_cookie, user_config)
            yield bcz_system_.bcz_system_get_static_config(user_cookie, user_config)
            yield bcz_system_.bcz_system_get_domain_whitelist(user_cookie, user_config)
            yield bcz_system_.bcz_system_get_privacy_agreement_version(user_cookie, user_config)
            yield bcz_system_.bcz_system_get_app_beta_update_info(user_cookie, user_config)



    def advertise_cold_launch(self, user_cookie, user_config, cold_launch=True):
        '''advertise_cold_launch'''
        advertise_ = advertise(self.http2_client_obj)
        yield advertise_.advertise_get_startup_ad(user_cookie, user_config)
        if cold_launch:
            yield advertise_.advertise_get_mall_tab_icon_info(user_cookie, user_config)
        yield advertise_.advertise_get_practice_popup_adv(user_cookie, user_config)
        yield advertise_.advertise_get_explore_popup_adv(user_cookie, user_config)
        yield advertise_.advertise_get_loading_ad_items(user_cookie, user_config)
        yield advertise_.advertise_get_loading_ad_info(user_cookie, user_config)
        yield advertise_.advertise_get_live_streaming_info(user_cookie, user_config)
        yield advertise_.advertise_get_main_view_bottom_advs_v2(user_cookie, user_config)
        yield advertise_.advertise_get_main_view_top_banner_advs(user_cookie, user_config)
        if cold_launch:
            yield advertise_.advertise_get_practice_banner_adv(user_cookie, user_config)
        


    def assistant_cold_launch(self, user_cookie, user_config, cold_launch=True):
        '''assistant_cold_launch'''
        assistant_ = assistant(self.http2_client_obj)
        yield assistant_.assistant_check_feedback_msg(user_cookie, user_config)
        yield assistant_.assistant_get_activity_updated_time(user_cookie, user_config)
        yield assistant_.assistant_get_beta_user_types_v2(user_cookie, user_config)

    def report_event_cold_launch(self, user_cookie, user_config, cold_launch=True):
        '''report_event_cold_launch'''
        selfreport_event = [
            {"index": 0},
            {"index": 2},
            {"index": 4, "extra_info": "{" + f"adv_id\":\"{user_config['adv_id']}\",\"id\":\"{user_config['adv_id']}\"" + "}"},
            {"index": 5},
            {"index": 6, "extra_info": "{" + f"\"device_id\":\"{get_device_str(user_cookie['device_id'])}\",\"channel\":\"{user_config['app_channel']}\"" + "}"},
        ]
        yield report_event(user_cookie, user_config, self.http2_client_obj, jsons = selfreport_event)


    def notify_cold_launch(self, user_cookie, user_config, cold_launch=True):
        '''notify_cold_launch'''

        yield notify_get_remind_info(user_cookie, user_config, self.http2_client_obj)
        yield notify_get_latest_notify(user_cookie, user_config, self.http2_client_obj)

    def resource_cold_launch(self, user_cookie, user_config, cold_launch=True):
        '''resource_cold_launch'''
        if cold_launch:
            yield resource_get_book_resource_update_info(user_cookie, user_config, self.http2_client_obj)

    def unified_user_cold_launch(self, user_cookie, user_config, cold_launch=True):
        '''unified_user_cold_launch'''
        unified_user_ = unified_user(self.http2_client_obj)
        if cold_launch:
            yield unified_user_.unified_user_get_bind_info(user_cookie, user_config)
        yield unified_user_.unified_user_check_access_token(user_cookie, user_config)


    def example(self, user_cookie, user_config):

        logger = thrift_logger()
        print('\033[1;37m--[$bcz_system]\033[0m')
        logger.run(self.bcz_system_cold_launch(user_cookie, user_config))
        
        print('\033[1;37m--[$advertise]\033[0m')
        logger.run(self.advertise_cold_launch(user_cookie, user_config))

        print('\033[1;37m--[$passport/unified_user_service]\033[0m')
        logger.run(self.unified_user_cold_launch(user_cookie, user_config))

        print('\033[1;37m--[$assistant]\033[0m')
        logger.run(self.assistant_cold_launch(user_cookie, user_config))

        print('\033[1;37m--[$notify]\033[0m')
        notify_generator = self.notify_cold_launch(user_cookie, user_config)
        logger.run(notify_generator)

        print('\033[1;37m--[$resource]\033[0m')
        resource_generator = self.resource_cold_launch(user_cookie, user_config)
        logger.run(resource_generator)
        
        
        print('\033[1;37m--[$learn/user_study]\033[0m')
        
        user_study_generator = self.user_study_cold_launch(user_cookie, user_config)
        logger.run(user_study_generator)
        print('\033[1;37m--[$report]\033[0m')
        logger.run(self.report_event_cold_launch(user_cookie, user_config))

        logger.close()

if __name__ == '__main__':
    # init
    user_dict_obj = user_dict()
    user_config = user_dict_obj.get_config(0)
    user_cookie = user_dict_obj.get_cookie(0)
    http2_client_obj = http2_client()


    # unified_user = unified_user(http2_client_obj)
    # result = unified_user.unified_user_update_role_extra(user_cookie, user_config, grade=1, role_up=8)
    # print_thrift_object(result)
    # exit()
    # cold_launch_ = cold_launch(http2_client_obj)
    # cold_launch_.example(user_cookie, user_config)
    # exit()
    user_study_ = user_study(http2_client_obj)
    result = user_study_.user_study_user_basic_info_v2(user_cookie, user_config)
    print_thrift_object(result)
    exit()


