# append.py
'''【独立工具】用于导入以及更新user_cookie.json文件'''
import pyperclip
import json

def delete_user_data(text=None):
    return append_user_data(text, delete=True)

def append_user_data(text=None, delete=False):
    '''用于导入以及更新user_cookie.json文件'''
    print("数据格式: can_daka(0/1)\tunique_id\tname\tword_count(新学词数)\tcooper(None)\tcan_pk(0/1)\tarbiter(0/1,是否允许PK反挂)\ttidal_group_limit(可用班位数)\t是否订阅该账户公告")
    
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
                try:
                    can_daka = user['config']['can_daka']
                    unique_id = int(user['config']['unique_id'])
                    name = user['config']['name']
                    access_token = user['cookie']['access_token']

                    assert can_daka in [0, 1]
                    assert unique_id > 0
                    assert name != 0
                    assert access_token != 0
                    
                    current_user_config[unique_id] = user['config']
                    current_user_cookie[unique_id] = user['cookie']
                    current_user_config[unique_id]['unique_id'] = unique_id
                except Exception as e:
                    print(f"Invalid existing user: {user} {e}")
                    result_str += f"Invalid existing user: {user} {e}\n"
    except: # 可能原先没有账号数据
        pass

    cnt = 0
    unique_id = 0
    for i in data:
        if len(i) < 7:
            continue
        try: # 这些是必填项
            assert int(i[0]) in [0, 1]
            assert int(i[1]) > 0
            assert i[2] != 0
            assert i[5] != 0
        except:
            print(f"Ignore user: {i[2]}({i[1]})")
            result_str += f"Ignore user: {i[2]}({i[1]})\n"
            continue
        try:
            unique_id = int(i[1])
            user_config = {
                "can_daka": int(i[0]) if i[0] != '' else 0,
                "unique_id": unique_id,
                "name": i[2],
                "word_count": int(i[3]) if i[3] != '' else 5,
                # "cooper": int(i[4]), # read only
                # "token": str(i[5]), # cookies only, not here
                "can_team": int(i[6]) if i[6] != '' else 0,
                "can_pk": int(i[7]) if i[7] != '' else 0,
                "arbiter": int(i[8]) if i[8] != '' else 0, # arbiter
                "tidal_group_limit": int(i[9]) if i[9] != '' else 0,
                "subscribe_notice": int(i[10]) if i[10] != '' else 0,
                "check_notice": int(i[11]) if i[11] != '' else 0,
            }
            if user_config['word_count'] < 5:
                user_config['word_count'] = 5
            user_cookie = {
                "access_token": i[5],
            }
        except:
            print(f"Invalid user infos: {i[2]}({i[1]})")
            result_str += f"Invalid user infos: {i[2]}({i[1]})\n"
            continue
        
        if current_user_config.get(unique_id):
            cnt += 1
            if delete:
                print(f"\033[32mDeleting user {unique_id} from the database.\033[0m")
                result_str += f"\033[32mDeleting user {unique_id} from the database.\033[0m\n"
                del current_user_config[unique_id]
                del current_user_cookie[unique_id]
                continue
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
            if delete:
                print(f"\033[31mUser {unique_id} not found in the database.\033[0m")
                result_str += f"\033[31mUser {unique_id} not found in the database.\033[0m\n"
                continue
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
        if config.get('tidal_group_limit', 0) == 0:
            continue
        tidal_result_list.append({
            "unique_id": unique_id,
            "name": config['name'],
            "access_token": current_user_cookie[unique_id]['access_token'],
            "tidal_group_limit": config['tidal_group_limit']
        })
    with open("../shadlc-BCZ-Group-Manager/tidal_token.json", "w", encoding="utf-8") as f:
        json.dump(tidal_result_list, f, indent=4, ensure_ascii=False)


    if delete:
        print(f"\033[32m{cnt} users deleted from the database.\033[0m")
        result_str += f"\033[32m{cnt} users deleted from the database.\033[0m\n"
    else:
        print(f"\033[32m{cnt} users added to the database.\033[0m")
        result_str += f"\033[32m{cnt} users added to the database.\033[0m\n"
    if pause:
        input("Press any key to exit.")
    else:
        return result_str
if __name__ == '__main__':
    try:
        import os
        # 设置启动目录
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        i = input("Append or Delete? (A/D) ")
        if i in ('D', 'd'):
            delete_user_data()
        elif i in ('A', 'a'):
            append_user_data()
        else:
            print("Invalid input.")
    finally:
        input("Press any key to exit.")