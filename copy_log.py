# copy_log.py
'''【独立工具】读取当前文件夹下，当天创建的txt日志和错误信息文件，连接并拷贝内容'''
import os
import time

# 获取当前时间
today = time.strftime('%Y-%m-%d', time.localtime())

result = ''
path = './logs/'
# 遍历当前文件夹下所有文件
for file in os.listdir(path):
    # 判断文件是否为txt文件，且创建时间为当天
    if file.endswith('.txt') and today in file:
        # 读取文件内容
        with open(path + file, 'r', encoding='utf-8') as f:
            result += f.read()
        result += '\n\n'
import pyperclip
# 将内容复制到剪贴板
pyperclip.copy(result)
print('内容已复制到剪贴板')