'''已废弃（供以后参考？'''
from ncatbot.core import BotClient, GroupMessage, PrivateMessage
from ncatbot.utils.config import config
from ncatbot.utils.logger import get_log
from src.notice_parser import static_export_class, NoticeParser
from src.config import Config
from src.get_headers import getHeaders
from src.http2_client import http2_client
from src.schedule import Schedule
import time
import os

class RFHelper:
    blacklist_path = "./blacklist.xlsx"
    bot_name = "椽花喵"
    def __init__(self, automata_config: Config, http2_client_obj: http2_client):
        self.bad_notice = []
        self.setup_success = True
        self.is_running = False
        self.user_deskmate_url = 'https://social.baicizhan.com/api/deskmate/social/get_user_deskmate_info'
        self.user_card_info = 'https://social.baicizhan.com/api/deskmate/personal_details'
        self.user_team_url = 'https://activity.baicizhan.com/api/activity/team-up-recite/person_home' # 注意参数字段名bcz_id
        self.automata_config = automata_config
        self._log = get_log()
        if not self.setup_schedule(self.automata_config.bot_enabled_time):
            self.setup_success = False
            self._log.warning("self.bot 未启用，如有需要请在config.json中将bot_enabled设置为true后重启程序。")
            return
        if not os.path.exists(RFHelper.blacklist_path):
            self._log.warning("黑名单文件不存在，请检查路径是否正确。")
        else:
            self.blacklist_reader = static_export_class() # 用于读取黑名单
            # self.blacklist_reader.read_blacklist()
            self.blacklist = self.blacklist_reader.blacklist
            self.hash_dict = self.blacklist_reader.hash_dict # 储存blacklist中数字对应的字符串（因为黑名单中有大量重复字符串）
        self.notice_parser = NoticeParser() # 用于检查是否有违规内容


        config.set_bot_uin(automata_config.bot_uin)  # 设置 self.bot qq 号 (必填)
        config.set_ws_uri(automata_config.ws_uri)  # 设置 napcat websocket server 地址
        config.set_token(automata_config.napcat_token)  # 设置 token (napcat 服务器的 token)
        self.at_str = f'[CQ:at,qq={self.automata_config.bot_uin}]'

        self.sessions = []
        self.bot = BotClient()
        async def on_notice(msg: GroupMessage):
            self._log.info(msg)
            if not self.is_running:
                return
            if msg['sub_type'] == 'poke':
                sender_id = msg['user_id']
                for session in self.sessions:
                    print(session)
                    if session[1].user_id == sender_id and time.time() - session[2] < 60:
                        await self.bot.api.post_group_msg(msg['group_id'], text=f"收到啦，等下抓只麦花鸽来帮你找", reply=msg['message_id'], at=sender_id)
                        self.bad_notice.append(session[0])
                        time.sleep(1)
                        await self.bot.api.send_group_forward_msg(self.automata_config.base_group, [session[3]])
                        self.sessions.remove(session)

        self.bot.notice_event(on_notice)
            
        @self.bot.group_event()
        async def on_group_message(msg: GroupMessage):
            self._log.info(msg)
            if not self.is_running:
                return
            if msg.group_id not in self.automata_config.whitelist_groups:
                return
            if msg.raw_message.startswith(self.at_str):
                trimmed_message = msg.raw_message[len(self.at_str):].strip()
                print(trimmed_message)
                timestamp = time.time()
                sender = msg.sender
                message_id = msg.message_id
                if trimmed_message.startswith("公告"):
                    notice_content = trimmed_message[2:]
                    if notice_content[0] == '+':
                        await self.bot.api.post_group_msg(msg.group_id, text=f"可以不用打加号哦")
                    # 构造转发信息
                    auto_str, cnt = self.notice_parser.check_notice_auto(notice_content, include_compulsory=True)
                    time.sleep(1)
                    if cnt == 0:
                        await self.bot.api.post_group_msg(msg.group_id, text=f"咕！没有发现违规内容。等下抓麦花鸽来帮你找", reply=message_id, at=sender.user_id)
                        self.bad_notice.append(notice_content)
                        time.sleep(1)
                        print(message_id)
                        await self.bot.api.send_group_forward_msg(self.automata_config.base_group, [message_id])
                        return
                    report = await self.bot.api.post_group_msg(self.automata_config.base_group, text=auto_str)
                    # {'status': 'ok', 'retcode': 0, 'data': {'message_id': int}, 'message': '', 'wording': '', 'echo': timestamp(s)}
                    time.sleep(1)
                    # 构造转发信息
                    report_2 = await self.bot.api.send_group_forward_msg(msg.group_id, [report['data']['message_id']])
                    time.sleep(1)
                    await self.bot.api.post_group_msg(msg.group_id, text=f"嗷！找到了{cnt}处违规内容。如果还不过请拍一拍我/吃糖", reply=message_id, at=sender.user_id)
                    self.sessions.append((notice_content, sender, timestamp, message_id))
                else:
                    await self.bot.api.post_group_msg(msg.group_id, text=f"呱！{self.bot_name}睡不醒\n使用方式：\n{self.at_str}公告+内容", reply=message_id, at=sender.user_id)
    
                # if trimmed_message.startswith("添加"):
                #     uid = trimmed_message[2:]
                #     if not uid.isdigit():
                #         await self.bot.api.post_group_msg(msg.group_id, text=f"UID是纯数字哦", reply=message_id, at=sender_id)
                #         return
        
        
                

        @self.bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            self._log.info(msg)
            if not self.is_running:
                return
            return
            if msg.raw_message == "测试":
                await self.bot.api.post_private_msg(msg.user_id, text="NcatBot 测试成功喵~")
    
        self.bot.run(reload=False)

    def punch_in(self):
        self._log.info("打卡开始")
        self.is_running = True

    def punch_out(self):
        self._log.info("打卡结束")
        self.is_running = False

    def setup_schedule(self, bot_enabled_time: list) -> bool: # 格式:[[cron表达式, cron表达式], [cron表达式, cron表达式]]
        valid = False
        for cron_expr in bot_enabled_time:
            if len(cron_expr) != 2:
                self._log.warning(f"bot_enabled_time 格式错误，每个元素必须为长度为2的cron列表。{cron_expr}")
            sc1 = Schedule(cron_expr[0], self.punch_in)
            sc2 = Schedule(cron_expr[1], self.punch_out)
            if sc1.valid and sc2.valid:
                self._log.info(f"bot 已启用，每天 {cron_expr[0]} 开启，每天 {cron_expr[1]} 关闭")
                valid = True
        return valid
                

    # import from https://github.com/shadlc/BCZ-Group-Manager/blob/caprice/src/bcz.py
    def getUserInfo(self, user_id: str = None, token: str = '') -> dict | None:
        '''【用户校牌】获取用户名、同桌天数、是否靠谱头像框'''
        # 获取同桌信息
        if not user_id:
            return
        url = f'{self.user_deskmate_url}?uniqueId={user_id}'
        if token == '':
            token = self.automata_config.main_token
        headers = getHeaders(token)
        response = self.http2_client_obj.get(url, headers=headers, timeout=10)
        if response.status_code != 200 or response.json().get('code') != 1:
            msg = f'用户不存在呃，是不是打错了？'
            self._log.error(f'{msg}\n{response.text}')
            raise Exception(msg)
        user_info = {}
        user_info['unique_id'] = user_id
        user_info['name'] = response.json()['data']['userInfo']['name']
        user_info['deskmate_days'] = response.json()['data']['deskmateDays']
        return user_info
        response = self.http2_client_obj.get(f'{self.user_card_info}?uniqueId={user_id}', headers=headers, timeout=10)
        user_info['max_daka_days'] = response.json()['data']['dakaDays']
        # 获取小队信息
        url = f'{self.user_team_url}?bcz_id={user_id}'
        response = self.http2_client_obj.get(url, headers=headers, timeout=10)
        if response.status_code != 200 or response.json().get('code') != 1:
            self._log.warning(f'获取小队信息失败!\n{response.text}')
        team_info = response.json().get('data').get('members')
        if team_info is None or len(team_info) == 0:
            # 未加入小队
            user_info['dependable_frame'] = 4
        else:
            for member in team_info:
                if member['bczId'] == user_id:
                    user_info['dependable_frame'] = member['tag']
                    # 3靠谱，0不靠谱，1萌新
        if user_info.get('dependable_frame') is None:
            user_info['dependable_frame'] = 4
        return user_info


if __name__ == "__main__":
    automata_config = Config()
    http2_client_obj = http2_client()
    rfhelper = RFHelper(automata_config, http2_client_obj)
    rfhelper.run()

