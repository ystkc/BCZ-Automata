# lm.py
'''【独立工具】通过账号密码获取令牌'''
from src.bcz import loginWithPassword, print_thrift_object

# 手机号令牌
user_name = input("请输入用户名：")
password = input("请输入密码：")

def escape_string(s): # 令牌中暂时只有这三种
    return s.replace('/', '%2F').replace('+', '%2B').replace('=', '%3D')
 
# 登录
result = loginWithPassword(user_name, password)
print_thrift_object(result)
import pyperclip
pyperclip.copy(escape_string(f"{result.unique_id}\t{result.access_token}"))
input("登录成功，unique_id + 令牌已复制到剪贴板...")