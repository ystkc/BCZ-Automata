import re
import gzip
import time
import struct
import sqlite3
import hashlib
import requests
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol

from src.thriftAPI.ttypes import UserSelectedBookInfo, select_book_args, update_done_data_args, login_with_phone_args, send_sms_verify_code_args
from src.thriftAPI.UserStudyApiService import UserDoneWordRecord, UserBookListInfo, UserBasicInfoPlusV2
from src.thriftAPI.UnifiedUserService import PhoneLoginRequest, PhoneVerifyCodeRequest, UserLoginResult

class ProcessError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def daka(token: str, date: str, count: int):
    """为用户打卡

    Args:
        token (str): 用户令牌
        date (str): 打卡日期
        count (int): 打卡单词数
    """    
    url = "https://learn.baicizhan.com/api/study/xMode/daka"
    timestamp = round(time.time()*1000)
    device_id = hashlib.md5(token.encode("utf-8")).hexdigest()[:16]
    serial = hashlib.md5(token.encode("utf-8")).hexdigest()[:24]
    headers = {
        "Accept": "*/*",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "bcz_app/android/7.6.5",
        "Host": "learn.baicizhan.com",
        "Cookie": (
            f"access_token={token}; app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
            f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
        ),
    }
    response = requests.post(url, headers=headers, data=f"date={date}&count={count}")
    if response.status_code != 200:
        raise ProcessError(f'{response.status_code} {response.content}')
    try:
        result = response.json()
        if result.get('code') != 1:
            raise ProcessError(result.get('message'))
    except:
        raise ProcessError(f'{response.status_code} {response.content}')

def updateDoneData(token: str, book_id: int, words: list[int]):
    """为用户学习单词

    Args:
        token (str): 用户令牌
        book_id (int): 词书ID
        words (list[int]): 学习单词列表
    """    
    timestamp = round(time.time())
    timestamp_long = round(time.time()*1000)
    url = f"https://learn.baicizhan.com/rpc/user_study/update_done_data/{timestamp_long}"

    device_id = hashlib.md5(token.encode("utf-8")).hexdigest()[:16]
    serial = hashlib.md5(token.encode("utf-8")).hexdigest()[:24]
    headers = {
        "Accept": "application/x-thrift",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Compress-Type": "gzip",
        "Content-Type": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.5",
        "Host": "learn.baicizhan.com",
        "Cookie": (
            f"access_token={token}; app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
            f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
        ),
    }
    done_records = []
    for word_id in words:
        done_records.append(
            UserDoneWordRecord(
                word_topic_id=word_id,
                current_score=5,
                span_days=0,
                used_time=0,
                done_times=1,
                wrong_times=0,
                is_first_do_at_today=0,
                tag_id=0,
                spell_score=0,
                listening_score=1,
                chn_score=1,
                review_round=0
            )
        )

    args = update_done_data_args(
        last_sync_at = timestamp,
        arr_done_records = done_records,
        current_word_level_id = book_id,
        is_today_completed = True
    )

    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    args.write(protocol)
    thrift_data = transport.getvalue()
    thrift_data = b"\x82\x21\x01\x10" + b"update_done_data" + thrift_data
    length_data = struct.pack("!i", len(thrift_data))
    thrift_data = length_data + thrift_data
    compressed_data = gzip.compress(thrift_data)
    response = requests.post(url, headers=headers, data=compressed_data)
    content = response.content.decode(errors='ignore')
    if response.status_code != 200:
        raise ProcessError(f'{response.status_code} {content}')
    temp = content.split('update_done_data')
    if temp[-1] != '\x05\x00\x00\x00':
        print(response.content)
        content = temp[-1]
        raise ProcessError(content)

def getAllBooks(token: str, show_hidden: bool = False) -> UserBookListInfo:
    """获取全部单词书列表信息

    Args:
        token (str): 用户令牌

    Returns:
        UserBookListInfo: 单词书列表信息
    """    
    timestamp = round(time.time())
    url = "https://learn.baicizhan.com/rpc/user_study/get_all_books_basic_info_v3/{timestamp}"
    device_id = hashlib.md5(token.encode("utf-8")).hexdigest()[:16]
    serial = hashlib.md5(token.encode("utf-8")).hexdigest()[:24]
    headers = {
        "Accept": "application/x-thrift",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Compress-Type": "gzip",
        "Content-Type": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.5",
        "Host": "learn.baicizhan.com",
        "Cookie": (
            f"access_token={token}; app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
            f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
        ),
    }


    thrift_data = b'\x00'
    thrift_data = b"\x82\x21\x01\x1b" + b"get_all_books_basic_info_v3" + thrift_data
    length_data = struct.pack("!i", len(thrift_data))
    thrift_data = length_data + thrift_data
    compressed_data = gzip.compress(thrift_data)
    response = requests.post(url, headers=headers, data=compressed_data)
    content = response.content.decode(errors='ignore')
    if response.status_code != 200:
        raise ProcessError(f'{response.status_code} {content}')
    header_len = len('get_all_books_basic_info_v3') + 10
    transport = TTransport.TMemoryBuffer(response.content[header_len:])
    protocol = TCompactProtocol.TCompactProtocol(transport)
    result = UserBookListInfo()
    result.read(protocol)
    book_dict = {}
    for book in result.books_info:
        if book.book_flag == 0 and not show_hidden:
            continue
        book_dict[book.id] = {
            'name': book.name,
            'desc': book.desc,
            'img': book.img,
            'count': book.total_words_count,
            'book_flag': book.book_flag,
        }
    return book_dict

def sendSmsVerifyCode(phone_number: str):
    """发送短信验证码

    Args:
        phone_number (str): 手机号
    """    
    timestamp = round(time.time())
    timestamp_long = round(time.time()*1000)
    url = f"https://passport.baicizhan.com/rpc/unified_user_service/send_sms_verify_code/{timestamp_long}"

    device_id = hashlib.md5(str(timestamp).encode()).hexdigest()[:16]
    serial = hashlib.md5(str(timestamp).encode()).hexdigest()[:24]
    headers = {
        "Accept": "application/x-thrift",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Compress-Type": "gzip",
        "Content-Type": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.5",
        "Host": "passport.baicizhan.com",
        "Cookie": (
            f"app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
            f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
        ),
    }

    args = send_sms_verify_code_args(
        phone=phone_number,
        verify_type=5
    )

    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    args.write(protocol)
    thrift_data = transport.getvalue()
    thrift_data = b"\x82\x21\x01\x14" + b"send_sms_verify_code" + thrift_data
    length_data = struct.pack("!i", len(thrift_data))
    thrift_data = length_data + thrift_data
    compressed_data = gzip.compress(thrift_data)
    response = requests.post(url, headers=headers, data=compressed_data)
    content = response.content.decode(errors='ignore')
    if response.status_code != 200:
        raise ProcessError(f'{response.status_code} {content}')
    chs_result = re.findall('[\u4e00-\u9fa5]', content)
    if chs_result:
        raise ProcessError(''.join(chs_result))

def loginWithPhone(phone_number: str, code: str) -> UserLoginResult:
    """手机号登陆

    Args:
        phone_number (str): 手机号
        code (str): 验证码

    Returns:
        UserLoginResult: 登陆结果
    """    
    timestamp = round(time.time())
    timestamp_long = round(time.time()*1000)
    url = f"https://passport.baicizhan.com/rpc/unified_user_service/login_with_phone/{timestamp_long}"

    device_id = hashlib.md5(str(timestamp).encode()).hexdigest()[:16]
    serial = hashlib.md5(str(timestamp).encode()).hexdigest()[:24]
    headers = {
        "Accept": "application/x-thrift",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Compress-Type": "gzip",
        "Content-Type": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.5",
        "Host": "passport.baicizhan.com",
        "Cookie": (
            f"app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
            f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
        ),
    }

    args = login_with_phone_args(
        request=PhoneLoginRequest(
            verify_code_request= PhoneVerifyCodeRequest(
                phone=phone_number,
                verify_code=code
            ),
            free_verify_request=None,
            device=f'V2218A-vivo-{device_id}'
        )
    )

    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    args.write(protocol)
    thrift_data = transport.getvalue()
    thrift_data = b"\x82\x21\x01\x10" + b"login_with_phone" + thrift_data
    length_data = struct.pack("!i", len(thrift_data))
    thrift_data = length_data + thrift_data
    compressed_data = gzip.compress(thrift_data)
    response = requests.post(url, headers=headers, data=compressed_data)
    content = response.content.decode(errors='ignore')
    if response.status_code != 200:
        raise ProcessError(f'{response.status_code} {content}')
    header_len = len('login_with_phone') + 10
    transport = TTransport.TMemoryBuffer(response.content[header_len:])
    protocol = TCompactProtocol.TCompactProtocol(transport)
    result = UserLoginResult()
    try:
        result.read(protocol)
        return result
    except:
        chs_result = re.findall('[\u4e00-\u9fa5]', content)
        raise ProcessError(''.join(chs_result))

def userBasicInfo(token: str) -> UserBasicInfoPlusV2:
    """获取用户基本信息

    Args:
        token (str): 用户令牌

    Returns:
        UserBasicInfoPlusV2: 用户信息
    """    
    timestamp = round(time.time())
    url = "https://learn.baicizhan.com/rpc/user_study/user_basic_info_v2/{timestamp}"
    device_id = hashlib.md5(token.encode("utf-8")).hexdigest()[:16]
    serial = hashlib.md5(token.encode("utf-8")).hexdigest()[:24]
    headers = {
        "Accept": "application/x-thrift",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Compress-Type": "gzip",
        "Content-Type": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.5",
        "Host": "learn.baicizhan.com",
        "Cookie": (
            f"access_token={token}; app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
            f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
        ),
    }

    thrift_data = b'\x00'
    thrift_data = b"\x82\x21\x01\x12" + b"user_basic_info_v2" + thrift_data
    length_data = struct.pack("!i", len(thrift_data))
    thrift_data = length_data + thrift_data
    compressed_data = gzip.compress(thrift_data)
    response = requests.post(url, headers=headers, data=compressed_data)
    content = response.content.decode(errors='ignore')
    if response.status_code != 200:
        raise ProcessError(f'{response.status_code} {content}')
    header_len = len('user_basic_info_v2') + 10
    transport = TTransport.TMemoryBuffer(response.content[header_len:])
    protocol = TCompactProtocol.TCompactProtocol(transport)
    result = UserBasicInfoPlusV2()
    result.read(protocol)
    return result

def select_book(
        token: str,
        book_id: int,
        daily_plan_count: int,
        review_plan_count: int,
        mode: int
    )-> UserSelectedBookInfo:
    """更换词书和学习计划

    Args:
        token (str): 用户令牌
        book_id (int): 词书ID
        daily_plan_count (int): 每日学习单词数
        review_plan_count (int): 每日复习单词数
        mode (int): 学习模式  # 0: 图片模式 1: 图片模式 2: 押韵模式 3: 深度模式 4: 未知

    Returns:
        UserSelectedBookInfo: 选中词书信息
    """    
    timestamp = round(time.time())
    timestamp_long = round(time.time()*1000)
    url = f"https://learn.baicizhan.com/rpc/user_study/select_book/{timestamp_long}"

    device_id = hashlib.md5(str(timestamp).encode()).hexdigest()[:16]
    serial = hashlib.md5(str(timestamp).encode()).hexdigest()[:24]
    headers = {
        "Accept": "application/x-thrift",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Compress-Type": "gzip",
        "Content-Type": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.5",
        "Host": "learn.baicizhan.com",
        "Cookie": (
            f"access_token={token}; app_name=7050502; channel=download; version=12;  client_time={timestamp}; "
            f"device_name=android%2FV2218A-vivo; device_id={device_id}; serial={serial};"
        ),
    }

    args = select_book_args(
        book_id=book_id,
        daily_plan_count=daily_plan_count,
        review_plan_count=review_plan_count,
        mode=mode
    )

    transport = TTransport.TMemoryBuffer()
    protocol = TCompactProtocol.TCompactProtocol(transport)
    args.write(protocol)
    thrift_data = transport.getvalue()
    thrift_data = b"\x82\x21\x01\x0b" + b"select_book" + thrift_data
    length_data = struct.pack("!i", len(thrift_data))
    thrift_data = length_data + thrift_data
    compressed_data = gzip.compress(thrift_data)
    response = requests.post(url, headers=headers, data=compressed_data)
    content = response.content.decode(errors='ignore')
    if response.status_code != 200:
        raise ProcessError(f'{response.status_code} {content}')
    header_len = len('select_book') + 10
    transport = TTransport.TMemoryBuffer(response.content[header_len:])
    protocol = TCompactProtocol.TCompactProtocol(transport)
    result = UserSelectedBookInfo()
    result.read(protocol)
    if not result.book_id:
        raise ProcessError(content.split('select_book')[-1])
    return result


def getCurrentBook(token: str) -> int:
    """获取当前用户背的词书ID

    Args:
        token (str): 用户令牌

    Returns:
        int: 词书ID
    """    
    info = userBasicInfo(token)
    return info.user_info.current_word_level_id

def getRandomWordIDInBook(db_path: str, book_id: int, count: int) -> list[int]:
    """获取指定单词数内指定数量随机单词ID

    Args:
        db_path (str): 词库路径
        book_id (int): 词书ID
        count (int): 单词数量

    Returns:
        list[int]: 单词ID列表
    """    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT TOPIC_ID FROM TOPIC_BOOK_MAP WHERE BOOK_IDS LIKE ? ORDER BY RANDOM() LIMIT ?;",
        (f'%{book_id}%', count )
    )
    result = cursor.fetchall()
    conn.close()
    words = [i[0] for i in result]
    return words
    

if __name__ == "__main__":
    ...
    token = ""
    date = time.strftime(r"%Y%m%d", time.localtime())
    print(date)
    count = 10

    # book_id = getCurrentBook(token)
    # print(updateDoneData(token, book_id, getRandomWordIDInBook('lookup.db', book_id, count)))

    # print(daka(token, date, count))

    # print(getAllBooks(token))
    # print(sendSmsVerifyCode(""))
    # print(loginWithPhone("", ""))
