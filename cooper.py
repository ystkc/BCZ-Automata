import json
from math import log

json_path = "./user_cookie.json"
with open(json_path, "r", encoding="utf-8") as f:
    user_cookie = json.load(f)
names = []
coopers = []
for user_dict in user_cookie:
    names.append(user_dict['config']["name"])
    coopers.append(user_dict['config'].get("cooper", -1))


import matplotlib.pyplot as plt
import datetime
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号
plt.bar(names, coopers)
plt.yscale('log')
plt.title(datetime.datetime.now().strftime("%Y-%m-%d"))
# 在柱子上添加数值标签
for x, y in zip(names, coopers):
    plt.text(x, y+0.1, '%d' % y, ha='center', va='bottom', fontsize=10)
# 旋转x轴标签
plt.xticks(rotation=45)
plt.show()