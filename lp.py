# lp.py
'''【独立工具】通过手机验证码获取令牌'''
from src.bcz import sendSmsVerifyCode, loginWithPhone, print_thrift_object

# 手机号令牌
phone_number = input("请输入手机号：")
print_thrift_object(sendSmsVerifyCode(phone_number))
code = input("验证码已发送，请输入验证码：")
print_thrift_object(loginWithPhone(phone_number, code))
input("登录成功，记得复制结果...")