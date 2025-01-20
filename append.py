# append.py
'''【独立工具】用于导入以及更新user_cookie.json文件'''
import pyperclip
import json

def append_user_data(text=None):
    '''用于导入以及更新user_cookie.json文件'''
    print("数据格式: can_daka(0/1)\tunique_id\tname\tword_count(新学词数)\tcooper(None)\tcan_pk(0/1)\tarbitor(0/1,是否允许PK反挂)\ttidal_group_limit(可用班位数)\t是否订阅该账户公告")
    
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
    pause = False
    result_str = ""
    if text is None:
        pause = True
        print("请先拷贝账号数据表格，格式如下(无需表头，一行一个，\\t分隔)")
        input("然后按回车键继续。")
        text = pyperclip.paste()
    text_line = text.split('\n')
    data = []
    for line in text_line:
        items = line.split('\t')
        for i in range(len(items)):
            if items[i] == '' or items[i] == '\r' or items[i] == '☐':
                items[i] = 0
            if items[i] == '☑':
                items[i] = 1
        data.append(items)
        
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
        if len(i) < 10:
            continue
        unique_id = int(i[1])
        access_token = i[5]
        if unique_id == 0 or access_token == 0:
            continue
        user_config = {
            "can_daka": int(i[0]),
            "unique_id": int(i[1]),
            "name": i[2],
            "word_count": int(i[3]),
            # "cooper": int(i[4]), # read only
            "can_pk": int(i[6]),
            "arbitor": int(i[7]), # arbitor
            "tidal_group_limit": int(i[8]),
            "subscribe_notice": int(i[9])
        }
        user_cookie = {
            "access_token": i[5],
        }
        
        if current_user_config.get(unique_id):
            cnt += 1
            print(f"User {unique_id} already exists in the database.")
            result_str += f"User {unique_id} already exists in the database.\n"
            for key, value in user_config.items():
                if user_config[key] != current_user_config[unique_id].get(key):
                    print(f"Updating {key} from {current_user_config[unique_id].get(key)} to {value}.")
                    result_str += f"Updating {key} from {current_user_config[unique_id].get(key)} to {value}.\n"
                    current_user_config[unique_id][key] = value
            for key, value in user_cookie.items():
                if user_cookie[key] != current_user_cookie[unique_id].get(key):
                    print(f"Updating {key} from {current_user_cookie[unique_id].get(key)} to {value}.")
                    result_str += f"Updating {key} from {current_user_cookie[unique_id].get(key)} to {value}.\n"
                    current_user_cookie[unique_id][key] = value
        else:
            cnt += 1
            print(f"\033[32mAdding user {user_config['name']} to the database.\033[0m can_daka: {user_config['can_daka']}")
            result_str += f"\033[32mAdding user {user_config['name']} to the database.\033[0m can_daka: {user_config['can_daka']}\n"
            user_cookie.update(template['cookie'])
            user_config.update(template['config'])
            current_user_config[unique_id] = user_config
            current_user_cookie[unique_id] = user_cookie


    result_list = []
    for unique_id, config in current_user_config.items():
        result_list.append({
            "config": config,
            "cookie": current_user_cookie[unique_id]
        })

    with open("./user_cookie.json", "w", encoding="utf-8") as f:
        json.dump(result_list, f, indent=4, ensure_ascii=False)

    tidal_result_list = []
    for unique_id, config in current_user_config.items():
        if config.get('tidal_group_limit', 0) <= 0:
            continue
        tidal_result_list.append({
            "unique_id": unique_id,
            "name": config['name'],
            "access_token": current_user_cookie[unique_id]['access_token'],
            "tidal_group_limit": config['tidal_group_limit']
        })
    with open("../shadlc-BCZ-Group-Manager/tidal_token.json", "w", encoding="utf-8") as f:
        json.dump(tidal_result_list, f, indent=4, ensure_ascii=False)


    print(f"\033[32m{cnt} users added to the database.\033[0m")
    result_str += f"\033[32m{cnt} users added to the database.\033[0m\n"
    if pause:
        input("Press any key to exit.")
    else:
        return result_str
if __name__ == '__main__':
    append_user_data()