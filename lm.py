# lm.py
'''【独立工具】通过账号密码获取令牌'''
from src.bcz import loginWithPassword, print_thrift_object

# 手机号令牌
user_name = input("请输入用户名：")
password = input("请输入密码：")

# 登录
print_thrift_object(loginWithPassword(user_name, password))
input("登录成功，记得复制结果...")