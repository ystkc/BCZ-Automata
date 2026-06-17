'''与一起背功能有关的接口'''
import time
import datetime
from src.config import Config
from src.thrift_utils import user_dict
from src.http2_client import http2_client
from src.get_headers import getHeaders
class bczGroup:
    def __init__(self, http2_client_obj: http2_client, user_dict_obj: user_dict, config: Config):
        self.http2_client_obj: http2_client = http2_client_obj
        self.user_dict_obj: user_dict = user_dict_obj
        self.config: Config = config
        self.groups_info_buffer = {} # (share_key, access_token)或group_id -> (timestamp, group_info)
        self.rank_info_buffer = {} # share_key -> (timestamp, rank_info, last_week_rank_info)
        self.rank_roll_buffer = {} # rank: int -> (timestamp, [groups])
        self.poster_buffer = {} # sharekey -> content
        self.personal_detail_buffer = {} # unique_id -> (timestamp, personal_detail)

    # ---------------------------
    # util
    # ---------------------------
    
    def humanize_timestr_ago(self, time_str):
        """
        将日期字符串转换为人类易读的相对时间描述（仅处理过去时间）
        
        参数:
            time_str: 日期字符串，格式如 '2026-06-15 19:12:01'
        
        返回:
            相对时间描述字符串，如 '3秒前', '5分钟前', '2小时前' 等
        """
        # 解析输入时间
        try:
            target_time = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("时间格式错误，应为 'YYYY-MM-DD HH:MM:SS'")
        
        # 获取当前时间
        now = datetime.datetime.now()
        
        # 可能是卡了一些时差
        if target_time > now:
            return "现在"
        
        # 计算时间差
        delta = now - target_time
        seconds = int(delta.total_seconds())
        return self.humanize_second_ago(seconds)

    def humanize_second_ago(self, seconds):
        '''将秒数转换为人类易读的相对时间描述'''
        if seconds > 1576800000: # 如果是1970年1月1日，距今就是56年，将超过50年的时间判定为从未
            return '从未'
        # 定义时间单位和对应的秒数
        intervals = (
            (31536000, '年'),
            (2592000, '个月'),
            (604800, '周'),
            (86400, '天'),
            (3600, '小时'),
            (60, '分钟'),
            (1, '秒'),
        )
        
        # 找到合适的时间单位
        for seconds_in_unit, unit_name in intervals:
            count = seconds // seconds_in_unit
            if count >= 1:
                return f"{count}{unit_name}前"
        
        # 如果所有单位都不满足（理论上不会发生）
        return "刚刚"
    
    def groupShareKeytoId(self, group_share_key, user_cookie):
        '''将群组分享码转换为群组ID'''
        success, data = self.getGroupInfo(group_share_key, user_cookie)
        if not success:
            return False, data
        return True, data['groupInfo']['id']
    
    # ---------------------------
    # 用户个人相关
    # ---------------------------

    def getUserInfo(self, user_cookie: dict, user_id: str = None, buffer_time: int = 60000):
        '''【用户校牌】获取用户名等信息'''
        time_long = int(time.time() * 1000)
        if user_id in self.personal_detail_buffer and time_long - self.personal_detail_buffer[user_id][0] < buffer_time:
            return True, self.personal_detail_buffer[user_id][1]
        headers = getHeaders('$social', user_cookie, time_long, index=1)
        response = self.http2_client_obj.send_http2_request('GET', f'https://social.baicizhan.com/api/deskmate/personal_details?uniqueId={user_id}', headers=headers, content=None)
        response_json = response.json()
        if response_json['code'] != 1:
            return False, response_json
        self.personal_detail_buffer[user_id] = (time_long, response_json['data'])
        return True, response_json['data']
    
    def ownGroups(self, user_dict):
        '''获取用户的小班列表'''
        time_long = int(time.time() * 1000)
        headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = self.http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/own_groups?uniqueId=0', headers=headers, content=None)
        response_json = response.json()
        if response_json['code'] != 1:
            return False, response_json
        # 顺便更新班位、拥有的小班数量、已授权的小班数量
        groups = response_json['data']['list']
        leader_cnt = auth_cnt = 0
        for group in groups:
            if group['leader']:
                leader_cnt += 1
                if group['authorization']:
                    auth_cnt += 1
        if 'group_limit' not in user_dict['config']:
            self.getGroupLimit(user_dict)
        user_dict['config']['group_vacant'] = user_dict['config']['group_limit'] - len(groups)
        user_dict['config']['leader_group_cnt'] = leader_cnt
        user_dict['config']['auth_group_cnt'] = auth_cnt
        self.user_dict_obj.update_user_dict(user_dict)
        return True, groups
    
    def get_own_bronze_groups_share_key(self, user_dict):
        '''获取自己的青铜小班分享码'''
        status, groups = self.ownGroups(user_dict)
        if not status:
            return False, f'获取自己的青铜小班分享码失败! 请检查{groups}'
            
        result = []
        for group in groups:
            if group['rank'] == 1 and group['leader']:
                result.append(group['shareKey'])
        return True, result

    def getGroupLimit(self, user_dict):
        '''获取用户的群组上限、年级区和授权上限等等'''
        # GET https://group.baicizhan.com/group/get_group_user_info
        time_long = int(time.time() * 1000)
        headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = self.http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/get_group_user_info', headers=headers, content=None)
        response_json = response.json()
        if response_json['code'] != 1:
            return False, response_json
        # 顺便更新班位
        user_dict['config']['grade'] = response_json['data']['grade']
        user_dict['config']['group_limit'] = response_json['data']['groupLimiteNumber']
        user_dict['config']['auth_limit'] = response_json['data']['groupAuthorizationLimiteNumber']
        self.user_dict_obj.update_user_dict(user_dict)
        return True, response_json['data']
    
    def increaseGroupLimit(self, user_dict):
        '''增加用户的群组上限'''
        # POST https://group.baicizhan.com/group/add_group_limit_num {}
        time_long = int(time.time() * 1000)
        headers=getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        response = self.http2_client_obj.send_http2_request('POST', 'https://group.baicizhan.com/group/add_group_limit_num', headers=headers, content={})
        response_json = response.json()
        if response_json['code'] != 1:
            return False, response_json
        # 顺便更新班位
        user_dict['config']['group_limit'] += 1
        self.user_dict_obj.update_user_dict(user_dict)
        return True, response_json['data']
    
    def toggleLikeState(self, user_dict, target_id):
        '''为指定用户点赞'''
        # 检测是否已经点过了（因为likeAPI是toggle的）
        success, user_info = self.getUserInfo(user_dict['cookie'], target_id)
        if not success:
            return False, user_info
        if user_info['todayLikedState']:
            return True, '已点赞，不重复操作'
        # POST https://social.baicizhan.com/api/deskmate/like_unlike
        payload = {"uniqueId":target_id,"type":1}# 取消也是1  
        headers = getHeaders("$social", user_dict['cookie'], int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = self.http2_client_obj.send_http2_request('POST', 'https://social.baicizhan.com/api/deskmate/like_unlike', headers=headers, content = payload).json()
        # 刷新缓存
        success, user_info = self.getUserInfo(user_dict['cookie'], target_id, buffer_time=-1)
        if not success:
            return False, user_info
        if response_json['code'] == 1:
            return True, response_json['message']
        return False, response_json['message']
    
    def getRoleUp(self, user_cookie, user_config, http2_client_obj: http2_client):
        '''获取用户当前的年级区（注意不是年级）年级修改函数在bcz.py中
        1:小学1-3
        2:小学4-6
        3:初中
        4:高中
        5:大学、硕博、成人'''
        # GET 'https://group.baicizhan.com/group/get_group_user_info'
        if user_config.get('grade') is not None:
            return True, user_config['grade']
        header = getHeaders("$group", user_cookie, int(time.time()), index=1)
        response = http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/get_group_user_info', headers=header, content=None)
        if response.status_code != 200 or response.json().get('code') != 1:
            return False, f'获取用户年级区失败{response.status_code} {response.text}'
        user_config['grade'] = response.json()['data']['grade']
        return True, user_config['grade']
    
    def get_unread_count(self, user_cookie):
        '''获取这个账号的【小班】未读消息数量
        deprecated: 由于是破坏性的，只能读取一次（自动标记已读）。已经不再使用'''
        # https://notify.baicizhan.com/rest/notify/v2/home
        notifyHeader = getHeaders("$notify", user_cookie, int(time.time()), index=1)
        response = self.http2_client_obj.send_http2_request('GET', 'https://notify.baicizhan.com/rest/notify/v2/home', headers=notifyHeader, content=None)
        messages = response.json()['data']
        unread_count = 0
        for msg_class in messages:
            if msg_class["messageType"] != 4: # 1:不断电 2:精选 3:同桌 4:小班 6:调查 7:点赞 9:组队
                continue
            unread_count = msg_class["unread"]
        return unread_count
    
    def format_user_strs(self, idx_start: int = 1, unique_ids:list = None):
        return self.user_dict_obj.format_user_strs(idx_start, unique_ids)

    # ---------------------------
    # 班级信息
    # ---------------------------

    def num_to_rank(self, num):
        '''将数字转换为等级（注意！这是一般从0开始的info，如果是和官方小班放一起的要-1再调用）'''
        if num == 0:
            return '青铜'
        elif num == 1:
            return '白银'
        elif num == 2:
            return '黄金'
        elif num == 3:
            return '铂金'
        elif num == 4:
            return '钻石'
        elif num == 5:
            return '星耀'
        return '王者'
    
    def getGroupInfo(self, share_key: str, user_cookie: dict, buffered_time: int = 60000):
        '''获取【班内主页】信息group/information
        buffered_time为缓存时间，单位毫秒'''
        time_long = int(time.time()*1000)
        access_token = user_cookie['access_token']
        tp = (share_key, access_token)
        if tp in self.groups_info_buffer and time_long - self.groups_info_buffer[tp][0] < buffered_time:  
            return True, self.groups_info_buffer[tp][1]
        url = f'https://group.baicizhan.com/group/information?shareKey={share_key}'
        headers = getHeaders('$group', user_cookie, time_long, index=1)
        auth_response = self.http2_client_obj.send_http2_request('GET', url, headers=headers, content=None)
        response_json = auth_response.json()
        if auth_response.status_code != 200 or response_json.get('code') != 1:
            return False, f'使用{access_token[:10]}...获取分享码为{share_key}的小班信息失败{auth_response.status_code} {auth_response.text}'
        self.groups_info_buffer[(share_key, access_token)] = (time_long, response_json['data'])
        return True, response_json['data']
    
    def getGroupInfobyId(self, group_id: str, user_cookie: dict, buffered_time: int = 60000):
        '''根据班级id获取班级信息
        buffered_time为缓存时间，单位毫秒'''
        time_long = int(time.time()*1000)
        headers = getHeaders('$group', user_cookie, time_long, index=1)
        if group_id in self.groups_info_buffer and time_long - self.groups_info_buffer[group_id][0] < buffered_time:  
            return True, self.groups_info_buffer[group_id][1]
        # GET https: //group.baicizhan.com/group/get_group_info?groupId=
        url = f'https://group.baicizhan.com/group/get_group_info?groupId={group_id}'
        auth_response = self.http2_client_obj.send_http2_request('GET', url, headers=headers, content=None)
        response_json = auth_response.json()
        if auth_response.status_code != 200 or response_json.get('code') != 1:
            return False, f'{group_id}获取班级信息失败{auth_response.status_code} {auth_response.text}'
        self.groups_info_buffer[group_id] = (time_long, response_json['data'])
        return True, response_json['data']
    
    def formatGroupInfo(self, share_key: str, user_cookie: dict, buffer_time: int = 60000):
        '''简短的班级介绍'''
        status, data = self.getGroupInfo(share_key, user_cookie, buffer_time)
        if not status:
            return False, None
        group_info = data['groupInfo']
        group_name = group_info['name']
        group_id = group_info['id']
        group_type = self.num_to_rank(group_info['rank']-1)
        group_count = group_info['memberCount']
        group_limit = group_info['countLimit']
        group_finishing_rate = group_info['finishingRate']
        only_public_key_join = group_info['onlyPublicKeyJoin']
        return f"{group_name}({group_id})[{share_key}]\n{group_type} 人数{group_count}/{group_limit} 完成率{group_finishing_rate*100:.2f}% {'【仅邀请码加入】' if only_public_key_join else '公开'}"
    
    def getGroupLeader(self, share_key: str, user_cookie: dict, buffer_time: int = 60000):
        '''获取当前班级的班长->(id, name)
        buffer_time为缓存时间，单位毫秒'''
        status, group_info = self.getGroupInfo(share_key, user_cookie, buffer_time)
        if not status:
            return False, None, None
        for member in group_info['members']:
            if member['leader']:
                return True, member['uniqueId'], member['nickname']
        return False, None, None

    
    def getRankInfo(self, share_key: str, user_cookie: dict, buffered_time: int = 60000):
        '''获取当前班级的【本周&上周】排名信息
        buffered_time为缓存时间，单位毫秒
        '''
        time_long = int(time.time() * 1000)
        if share_key in self.rank_info_buffer and time_long - self.rank_info_buffer[share_key][0] < buffered_time:
            return True, self.rank_info_buffer[share_key][1], self.rank_info_buffer[share_key][2]
        headers = getHeaders('$group', user_cookie, time_long, index=1)
        # rank = requests.get(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=1', headers=headers)
        rank = self.http2_client_obj.send_http2_request('GET', f'https://group.baicizhan.com/group/get_week_rank?shareKey={share_key}&week=1', headers=headers, content=None)
        # last_week_rank = requests.get(f'https://group.baicizhan.com/group/get_week_rank?shareKey={group_share_key}&week=2', headers=headers)
        last_week_rank = self.http2_client_obj.send_http2_request('GET', f'https://group.baicizhan.com/group/get_week_rank?shareKey={share_key}&week=2', headers=headers, content=None)
        if rank.status_code != 200 or last_week_rank.status_code != 200:
            return False, f'使用{user_cookie["access_token"][:10]}...获取分享码为{share_key}的本周&上周排名信息失败{rank.status_code} {rank.text} {last_week_rank.status_code} {last_week_rank.text}', None
        tp = (time_long, rank.json()['data'], last_week_rank.json()['data'])
        self.rank_info_buffer[share_key] = tp
        return True, tp[1], tp[2]
    
    def getRank(self, group_id: int, user_cookie: dict, rank: int = None, buffer_time: int = 60000) -> int:
        '''获取当前班级在【班级排行榜】的排名
        rank不为None时在指定等级查找，0表示未找到（未上榜或者等级不匹配）'''
        # https://group.baicizhan.com/group/get_group_rank?rank=7
        if rank is None:
            status, group_info = self.getGroupInfobyId(group_id, user_cookie, buffer_time)
            if not status:
                return False, group_info
            rank = group_info['rank']
        else:
            rank = int(rank)
        group_id = int(group_id)
        time_long = int(time.time() * 1000)
        if rank not in self.rank_roll_buffer or time_long - self.rank_roll_buffer[rank][0] > buffer_time:
            headers = getHeaders('$group', user_cookie, time_long, index=1)
            response = self.http2_client_obj.send_http2_request('GET', f"https://group.baicizhan.com/group/get_group_rank?rank={rank}", headers=headers, content=None)
            self.rank_roll_buffer[rank] = (time_long, response.json().get('data')['list'])
        for i, group in enumerate(self.rank_roll_buffer[rank][1]):
            if group['groupId'] == group_id:
                return i + 1
        return 0
    
    def getGroupJoinedAccounts(self, share_key: str, user_cookie: dict, index: int = -999):
        '''获取当前班级中自己【已加入】的账号（在user_dict中且加入了小班的账号）
        如果index为-1 -> 报告字符串
        如果index不是-1 -> 对应的unique_id'''
        status, group_info = self.getGroupInfo(share_key, user_cookie)
        if not status:
            return False, group_info, None
        member_list = group_info['members']
        not_joined_users = self.user_dict_obj.get_unique_ids()
        joined_users = []
        for member in member_list:
            member_unique_id = member['uniqueId']
            if member_unique_id in not_joined_users:
                joined_users.append(member_unique_id)
                not_joined_users.remove(member_unique_id)
        not_joined_users = list(not_joined_users)
        joined_user_str_list = self.format_user_strs(1, joined_users)
        not_joined_user_str_list = self.format_user_strs(idx_start=len(joined_user_str_list)+1, unique_ids=not_joined_users)
        joined_user_str = '\n'.join(joined_user_str_list)
        not_joined_user_str = '\n'.join(not_joined_user_str_list)
        user_str = '在班账号：\n' + joined_user_str + '\n不在班账号：\n' + not_joined_user_str
        if index == -999:
            return True, user_str
        if index < 0:
            return False, user_str, '账号索引不能小于0'
        if index < len(joined_users):
            return True, user_str, joined_users[index]
        index -= len(joined_users)
        if index < len(not_joined_users):
            return True, user_str, not_joined_users[index]
        return False, user_str, '账号索引超出范围'
    
    def get_nickname(self, unique_id, group_share_key, user_dict):
        '''返回班内昵称和打卡情况
        my_reply: str
        group_nickname[unique_id]: {
        "group_nickname": "xxx",
        "nickname": "xxx",
        "avatar": "xxx",
        "two_week_daka_dates": [-2, -2, -2, -2, -2, -2, -2, 1, 1, 0, 0, 1, -1, -1],
        "completed_times": 3,
        "duration_days": 5,
        }'''
        last_monday = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday() + 7)
        # 1.从周榜获取班内昵称
        status, rank, last_week_rank = self.getRankInfo(group_share_key, user_dict['cookie'])
        if not status:
            return False, rank
        member_list = rank['list']
        last_week_member_list = last_week_rank['list']
        group_nickname = {}
        my_reply = ""
        monitor_reply = ""
        my_unique_ids = set(self.user_dict_obj.get_unique_ids())
        wd = datetime.datetime.now().weekday()
        for member in member_list:
            unique_id = member['uniqueId']
            nickname = member['nickname']
            duration_days = member['durationDays']
            week_daka_dates = member['weekDakaDates']
            if member['leader'] == 1:
                monitor_reply = nickname
                nickname = '【班长】' + nickname
            if unique_id == user_dict['config']['unique_id']:
                my_reply = nickname
                nickname = '【我】' + nickname
            if unique_id in my_unique_ids:
                nickname = '【订阅】' + nickname
            # two_week_daka_dates是14个0、1，表示两周内每天的打卡情况
            two_week_daka_dates = [0] * 14
            # 如果duration_days不够两周，后面的标记-2
            if duration_days < 8 + wd:
                for i in range(8 + wd - duration_days):
                    two_week_daka_dates[i] = -2
            # 将本周未到达的日期设置为-1
            for i in range(6-wd):
                two_week_daka_dates[-1-i] = -1
            for date in week_daka_dates:
                # 计算距离上周一的天数
                delta = (datetime.datetime.strptime(date, '%Y-%m-%d') - last_monday).days + 1
                two_week_daka_dates[delta] = 1

            group_nickname[unique_id] = {
                "group_nickname": nickname,
                "two_week_daka_dates": two_week_daka_dates
            }

        # 2.再获取默认昵称
        main_cookie = user_dict['cookie'].copy()
        main_cookie['access_token'] = self.config.main_token
        status, group_info = self.getGroupInfo(group_share_key, main_cookie)
        if not status:
            return False, group_info
        group_member_list = group_info['members']
        # 遍历，如果有人的default_nickname和昵称相同，则是没改过昵称。
        for member in group_member_list:
            unique_id = member['uniqueId']
            if unique_id in group_nickname:
                if group_nickname[unique_id]['group_nickname'] == member['nickname'] and member['leader'] == 0: # 无论班长有没有改名都显示
                    del group_nickname[unique_id]
                else:
                    group_nickname[unique_id]['nickname'] = member['nickname']
                    group_nickname[unique_id]['avatar'] = member['avatar']
                    group_nickname[unique_id]['completed_times'] = member['completedTimes']
                    group_nickname[unique_id]['duration_days'] = member['durationDays']


        # 3.补全上周打卡情况
        for member in last_week_member_list:
            unique_id = member['uniqueId']
            if unique_id in group_nickname:
                last_week_daka_dates = member['weekDakaDates']
                two_week_daka_dates = group_nickname[unique_id]['two_week_daka_dates']
                for date in last_week_daka_dates:
                    # 计算距离上周一的天数
                    delta = (datetime.datetime.strptime(date, '%Y-%m-%d') - last_monday).days + 1
                    two_week_daka_dates[delta] = 1
        return my_reply, monitor_reply, group_nickname
    
    # ---------------------------
    # 授权功能
    # ---------------------------

    def getAuthGroups(self, user_cookie, unique_id):
        '''获取用户自己的【授权分班】页面'''
        # GET https://group.baicizhan.com/group/get_group_authorization_page?uniqueId=
        time_long = int(time.time() * 1000)
        headers = getHeaders("$group", user_cookie, time_long, index=1)
        response_json = self.http2_client_obj.send_http2_request('GET', f'https://group.baicizhan.com/group/get_group_authorization_page?uniqueId={unique_id}', headers=headers, content=None).json()
        if response_json.get('code') != 1:
            return False, f'使用{user_cookie["access_token"][:10]}...获取用户{unique_id}的授权分班页面失败{response_json.status_code} {response_json.text}'
        return True, response_json['data']['authorizationGroups']

    def getLastweekGroupRank(self, user_cookie: dict):
        '''获取【小班段位报告】用户加入的小班上周打卡数和排名'''
        # GET https://group.baicizhan.com/group/get_group_rank_report
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_cookie, time_long, index=1)
        response_json = self.http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/get_group_rank_report', headers=headers, content=None).json()
        if response_json.get('code') != 1:
            return False, f'使用{user_cookie["access_token"][:10]}...获取小班段位报告失败{response_json.status_code} {response_json.text}'
        return True, response_json['data']['list']
    
    # ---------------------------
    # 通知功能
    # ---------------------------
    def noticeGetAckList(self, share_key: str, user_cookie: dict):
        '''获取通知【收到列表】以及当前用户是否点了收到'''
        # GET https://group.baicizhan.com/group/notice?shareKey=
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_cookie, time_long, index=1)
        response_json = self.http2_client_obj.send_http2_request('GET', f'https://group.baicizhan.com/group/notice?shareKey={share_key}', headers=headers, content=None).json()
        if response_json.get('code') != 1:
            return False, f'使用{user_cookie["access_token"][:10]}...获取分享码为{share_key}的通知收到列表失败{response_json.status_code} {response_json.text}', None
        # 将memberIdList转换为uniqueIdList
        memberIds = set(response_json['data']['memberIdList'])
        meAcked = response_json['data']['received']
        status, group_info = self.getGroupInfo(share_key, user_cookie)
        if not status:
            return False, group_info, meAcked
        ackedList = []
        for member in group_info['members']:
            if member['id'] in memberIds:
                ackedList.append(member['uniqueId'])
        return True, ackedList, meAcked
    

    def noticeReply(self, share_key: str, user_cookie: dict, content: str=''):
        '''修改用户的【班内昵称】用于公告互动'''
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        if content != '' and content is not None:
            payload = {
                'shareKey': share_key,
                'nickname': content,
            }
            response_json = self.http2_client_obj.send_http2_request('POST', 'https://group.baicizhan.com/group/set_nickname', headers=headers, content = payload).json()
            if response_json['code'] == 1:
                return True, response_json
            return False, response_json
        return False, '回复内容不能为空'
    groupNicknameChange = noticeReply

    def noticeAckToggle(self, group_id: int, share_key: str, user_cookie: dict, target: bool=True):
        '''切换当前用户在这个班级的通知【收到】状态
        target为True时保持收到，为False时取消收到
        '''
        #  POST https://group.baicizhan.com/group/receive_notice?groupId=
        status, ackedList, meAcked = self.noticeGetAckList(share_key, user_cookie)
        if not status:
            return False, f'获取{group_id}的通知收到列表失败{ackedList}'
        if meAcked == target:
            return True, f'用户已经{"点击" if target else "取消"}了收到'
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = self.http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/receive_notice?groupId={group_id}', headers=headers, content={}).json()
        if response_json['code'] == 1:
            return True, response_json
        return False, response_json
    
    # ---------------------------
    # 班级操作
    # ---------------------------
    
    def groupJoin(self, user_dict: dict, group_share_key: str='', group_invite_key: str=''):
        '''加入群组
        group_share_key为分享码，group_invite_key为邀请码，有分享码时将忽略邀请码
        '''
        user_cookie = user_dict['cookie']
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_cookie, time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        if group_share_key != '':
            payload = {
                'shareKey': group_share_key,
                'source': 3
            }
            response_json = self.http2_client_obj.send_http2_request('POST', 'https://group.baicizhan.com/group/join', headers=headers, content=payload).json()
            # 刷新owngroups和group缓存(不管成功失败，都要刷新)
            status, own_groups = self.ownGroups(user_dict)
            if not status:
                return False, own_groups
            time.sleep(0.5) # 等待0.5秒，确保服务器端成员列表更新
            status, data = self.getGroupInfo(group_share_key, user_cookie, -1)
            if not status:
                return False, data
            if response_json['code'] == 1:
                return True, response_json
            return False, response_json
        else:
            payload = {
                'inviteKey': group_invite_key,
                'source': 0
            }
            response_json = self.http2_client_obj.send_http2_request('POST', 'https://group.baicizhan.com/group/join', content=(payload), headers=headers).json()
            # 刷新owngroups和group缓存(不管成功失败，都要刷新)
            status, own_groups = self.ownGroups(user_dict)
            if not status:
                return False, own_groups
            time.sleep(0.5) # 等待0.5秒，确保服务器端成员列表更新
            status, data = self.getGroupInfo(group_invite_key, user_cookie, -1)
            if not status:
                return False, data
            if response_json['code'] == 1:
                return True, response_json
            return False, response_json
        
    def groupQuit(self, user_dict: dict, group_share_key: str=''):
        '''退出群组'''
        time_long = int(time.time() * 1000)
        headers = getHeaders('$group', user_dict['cookie'], time_long, index = 1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = self.http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/quit?shareKey={group_share_key}', headers=headers, content={}).json()
        # 刷新owngroups和group缓存(不管成功失败，都要刷新)
        status, own_groups = self.ownGroups(user_dict)
        if not status:
            return False, own_groups
        time.sleep(0.5) # 等待0.5秒，确保服务器端成员列表更新
        status, data = self.getGroupInfo(group_share_key, user_dict['cookie'], -1)
        if not status:
            return False, data
        if response_json['code'] == 1:
            return True, response_json
        return False, response_json
    
    # imported from shadlc_BCZ_Group_Manager/src/bcz.py
    def setGroupOnlyInviteCodeJoin(self, share_key: str, user_cookie: dict, target: bool):
        '''设置小班仅允许邀请码加入，target为True时仅允许邀请码加入，False时允许所有用户加入'''
        status, group_info = self.getGroupInfo(share_key, user_cookie)
        if not status:
            return False, group_info
        onlyPublicKeyJoin = group_info['groupInfo']['onlyPublicKeyJoin']
        if onlyPublicKeyJoin == target:
            return True, '已经处于相同状态'
        headers = getHeaders('$group', user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        # https://group.baicizhan.com/group/set_only_public_key_join?shareKey=
        response = self.http2_client_obj.send_http2_request('POST', f'https://{headers["Host"]}/group/set_only_public_key_join?shareKey={share_key}', content={}, headers=headers)
        if response.json().get("code",0) != 1:
            return False, response.json()
        return True, response.json()
    
    # ---------------------------
    # 授权分班操作
    # ---------------------------
    
    def authHandle(self, user_dict, group_share_key, operation: int):
        '''处理授权申请
        operation: int 1:同意授权 2:拒绝授权 3:解除授权 '''
        # https://group.baicizhan.com/group/authorization_handle
        payload = {
            "shareKey": group_share_key,
            "type": int(operation)
        }
        headers = getHeaders("$group", user_dict['cookie'], int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = self.http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/authorization_handle', headers=headers, content = payload).json()
        if response_json['code'] == 1:
            return True, response_json
        return False, response_json
    
    def authApply(self, user_cookie, group_id: int, licensor_unique_id: int, type: int=1):
        '''申请/撤回授权
        1:申请授权 2:撤回授权'''
        # POST https://group.baicizhan.com/group/apply_authorization {'groupId': int(groupId), 'licensorUniqueId': int(licensorUniqueId), 'type': 1}
        payload = {
            "licensorUniqueId": int(licensor_unique_id),
            "type": int(type)
        }
        if type == 1:
            payload['groupId'] = int(group_id)
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = self.http2_client_obj.send_http2_request('POST', f'https://group.baicizhan.com/group/apply_authorization', headers=headers, content = payload).json()
        if response_json['code'] == 1:
            return True, response_json
        return False, response_json

    def inProcessAuthApply(self, user_cookie):
        '''扫描当前用户发出的授权分班申请'''
        # GET https://group.baicizhan.com/group/get_in_process_apply_record
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = self.http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/get_in_process_apply_record', headers=headers, content=None).json()
        if response_json['code'] == 1:
            return True, response_json['data']
        return False, response_json
    
    # ---------------------------
    # 招新卡
    # ---------------------------

    def preview_recommended_ordinary_groups(self, user_cookie):
        '''查看当前用户这个年级下的推荐小班'''
        # POST https://group.baicizhan.com/group/get_recommend_ordinary_groups {direction: 1}
        payload = {"direction": 1}
        header = getHeaders("$group", user_cookie, int(time.time()), index=1)
        header['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = self.http2_client_obj.send_http2_request('POST', 'https://group.baicizhan.com/group/get_recommend_ordinary_groups', headers=header, content = payload).json()
        results = []
        if response_json['code'] == 1:
            groups = response_json['data']['groupVoList']
            for group in groups:
                results.append(f'{self.num_to_rank(group["rank"]-1)} {group["memberCount"]}/{group["countLimit"]} {group["finishingRate"]*100:.2f}% {self.humanize_timestr_ago(group["buyTime"])}发布 {"[需要邀请码]"if group["onlyPublicKeyJoin"] else ""}{"[我的班级]"if group["leader"] else ""}{group["name"]} {group["introduction"]}')
        return '\n<br>'.join(results)

    def get_prop_card_cnt(self, user_cookie):
        '''获取用户当前拥有招新卡的数量'''
        # GET https://social.baicizhan.com/api/deskmate/goods/get_user_goods
        header = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = self.http2_client_obj.send_http2_request('GET', 'https://social.baicizhan.com/api/deskmate/goods/get_user_goods', headers=header, content=None)
        data = response.json()['data']
        for item in data:
            if item['id'] == 261 and item['name'] == '小班招新卡':
                return item['num']
        return None
    
    def get_cooper_and_prop_card_price(self, user_cookie):
        '''获取当前用户铜板数量和他看到的招新卡的价格（访问小卖部）'''
        # GET /api/deskmate/goods/get_sale_goods
        header = getHeaders("$social", user_cookie, int(time.time()), index=1)
        response = self.http2_client_obj.send_http2_request('GET', 'https://social.baicizhan.com/api/deskmate/goods/get_sale_goods', headers=header, content=None)
        data = response.json()['data']
        cooper_cnt = data['creditCount']
        goodslist = data['goodsInfoList']
        for good in goodslist:
            if good['id'] == 261 and good['name'] == '小班招新卡':
                return cooper_cnt, good['credit']
        return cooper_cnt, None
    
    def buy_prop_card(self, user_cookie):
        '''为当前用户购买招新卡'''
        # POST https://social.baicizhan.com/api/deskmate/goods/buy_goods?goodsId=261 {} => {"data":null,"message":"ok","code":1}
        header = getHeaders("$social", user_cookie, int(time.time()), index=1)
        header['Content-Type'] = 'application/json'
        response = self.http2_client_obj.send_http2_request('POST', 'https://social.baicizhan.com/api/deskmate/goods/buy_goods?goodsId=261', headers=header, content={})
        if response.json()['code'] != 1:
            return False, f'购买招新卡失败{response.json()}'
        return True, f'购买招新卡成功{response.json()}'

    def use_prop_card(self, user_cookie, group_id):
        '''为用户的班级使用招新卡'''
        # POST https://group.baicizhan.com/group/use_prop_card {"groupId":2865525,"propCardId":261}
        header = getHeaders("$group", user_cookie, int(time.time()), index=1)
        header['Content-Type'] = 'application/json'
        response = self.http2_client_obj.send_http2_request('POST', 'https://group.baicizhan.com/group/use_prop_card', headers=header, content={'groupId': group_id, 'propCardId': 261})
        print(response.json())
        if response.json()['code'] != 1:
            return False, f'使用招新卡失败{response.json()}'
        return True, f'使用招新卡成功{response.json()}'
    
    # ---------------------------
    # 海报
    # ---------------------------
    def getGroupPoster(self, user_cookie, share_key: str):
        '''获取当前小班的海报'''
        if share_key in self.poster_buffer:
            return True, self.poster_buffer[share_key]
        status, data = self.getGroupInfo(share_key, user_cookie)
        if not status:
            return False, data
        group_info = data['groupInfo']
        group_name = group_info['name']
        group_type = self.num_to_rank(group_info['rank']-1)
        group_count = group_info['memberCount']
        group_limit = group_info['countLimit']
        group_introduction = group_info['introduction']
        group_notice = group_info['notice']
        group_finishing_rate = int(group_info['finishingRate']*100)
        self.poster_buffer[share_key] = f'🌟麦花的授权分班(๑>ᴗ<๑)🌟{group_finishing_rate}+高完成率精品{group_type}小班「{group_name}」招新！最后{group_limit-group_count+1}个空位✧(≖◡≖✿)\n\n{group_introduction}\n💗\n{group_notice[:50]}'
        return True, self.poster_buffer[share_key]
    
    def setGroupPoster(self, share_key: str, poster: str):
        '''设置当前小班的海报'''
        self.poster_buffer[share_key] = poster

    def preview_posters(self, user_cookie, cnt_limit=10):
        '''查看当前用户这个年级下的海报'''
        # GET https://group.baicizhan.com/group/get_recruitment_post_list?anchorId=0&direction=1
        headers = getHeaders("$group", user_cookie, int(time.time()), index=1)
        response = self.http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/get_recruitment_post_list?anchorId=0&direction=1', headers=headers, content=None)
        data = response.json()
        if data.get("code",0) != 1:
            return False, f'查看海报失败 {data}'
        posters = data['data']['recruitmentPostVoList']
        results = []
        for poster in posters[:cnt_limit]:
            poster_content = poster['content'].replace('\n', '\\n')
            results.append(f"{poster['viewCount']}阅读 {self.humanize_timestr_ago(poster['createdAt'])} {poster_content}")
        return True, '\n\n'.join(results) + f'\n---------------以上是最新的{cnt_limit}个海报---------------'



    def sendPoster(self, user_cookie: dict, group_id: str, poster: str) -> bool:
        '''用当前账号给指定小班发送海报'''
        if len(poster) > 150:
            return False, f"海报内容过长，最多150个字符，当前长度{len(poster)}"
        time_long = int(time.time())
        headers = getHeaders("$group", user_cookie, time_long, index=1)
        response = self.http2_client_obj.send_http2_request('GET', 'https://group.baicizhan.com/group/get_recruitment_style_info', headers=headers, content=None)
        style_info = response.json().get('data')['list']
        style = -1
        for post in style_info:
            if post['credit'] == 0 and post['count'] > 0: # 查询还有没有免费的海报
                style = post['id']
                break
        for post in style_info:
            if post['count'] > 0:
                style = post['id']
                break
        if style == -1:
            return False, "没有可用的海报样式"
        
        headers["Content-Type"] = "application/json"
        headers["Origin"] = "https://group.baicizhan.com"
        headers["Referer"] = "https://group.baicizhan.com/wanted_board/create"
        payload = {
            "content": poster,
            "groupId": group_id,
            "style": style,
            "type": 1,
        }
        time.sleep(1)
        # https://group.baicizhan.com/group/publish_post
        response = self.http2_client_obj.send_http2_request('POST', 'https://group.baicizhan.com/group/publish_post', headers=headers, content=payload)
        data = response.json()
        if data.get("code",0) != 1:
            return False, f'发送海报失败 {data}'
        if data['data']['state'] == 2:
            return True, f'发送成功，已过审 {data}'
        else:
            return False, f'海报存在未知问题 {data}'
