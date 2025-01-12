# extract.py
'''【独立工具】导出指定账号的铜板数'''
import pyperclip

print("格式：can_daka(0/1)\tunique_id\tname\tword_count(新学词数)\tcooper(None)\tcan_pk(0/1)\tarbitor(0/1,是否允许PK反挂)\ttidal_group_limit(可用班位数)")
input("请拷贝 需要导出的账号 数据表格。按回车继续。")
template = {
        "cookie": {
            # "access_token": "",
            "app_name": "7060100",
            "device_name": "android%2FDCO-AL00-HUAWEI",
            "client_time": "",
            "device_id": "bf6b66213c31a7e8",
            "serial": "",
            "channel": "qq",
            "device_version": "12",
            "version": "12",
            "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
            "bcz_dmid": "2a16dfbb"
        },
        "config": {
            "book_id": 410,
            # "name": "",
            # "unique_id": "",
            "adv_id": 166102,
            "timezone": "Asia/Shanghai",
            "device_name_ext": "DCO-AL00-HUAWEI",
            "app_channel": "Rongyao",
            "user_index": 999,
            # "cooper": 0,
            # "grade": 3
        }
    }
text = pyperclip.paste()
text_line = text.split('\n')
data = []
for line in text_line:
    items = line.split('\t')
    for i in range(len(items)):
        if items[i] == '☐':
            items[i] = 0
        if items[i] == '☑':
            items[i] = 1
    data.append(items)
# exit()
import json
current_user_config = {}
current_user_cookie = {}
try:
    with open("./user_cookie.json", 'r', encoding='utf-8') as f:
        users = json.load(f)
        for user in users:
            unique_id = int(user['config']['unique_id'])
            current_user_config[unique_id] = user['config']
            current_user_cookie[unique_id] = user['cookie']
except:
    pass

cnt = 0
for i in data:
    if len(i) < 9:
        continue
    try:
        unique_id = int(i[1])
        access_token = i[4]
    except:
        continue
    if unique_id == 0 or access_token == 0:
        continue
    if current_user_config.get(unique_id) is not None:
        print(f"用户{unique_id}数据导出成功")
        i[4] = current_user_config[unique_id].get('cooper', -1) # 导出原有数据
    else:
        print(f"找不到用户{unique_id}")
        continue

# 导出数据到剪切板
text = ''
for i in data:
    text += '\t'.join(map(str, i)) + '\n'
pyperclip.copy(text)
print("数据已复制到剪切板，可直接粘贴到原表格中")
input("按回车退出")