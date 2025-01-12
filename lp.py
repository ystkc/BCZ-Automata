# lp.py
'''【独立工具】通过手机验证码获取令牌'''
from src.bcz import sendSmsVerifyCode, loginWithPhone, print_thrift_object

# 手机号令牌
phone_number = input("请输入手机号：")
print_thrift_object(sendSmsVerifyCode(phone_number))
code = input("验证码已发送，请输入验证码：")
result = loginWithPhone(phone_number, code)
print_thrift_object(result)


def escape_string(s): # 令牌中暂时只有这三种
    return s.replace('/', '%2F').replace('+', '%2B').replace('=', '%3D')

import pyperclip
pyperclip.copy(escape_string(f"{result.unique_id}\t{result.access_token}"))
input("登录成功，unique_id + 令牌已复制到剪贴板...")