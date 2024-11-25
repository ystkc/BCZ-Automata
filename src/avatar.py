# 根据用户头像查找其unique_id，若数据库不存在则返回'None'
import sqlite3

db_path = '../shadlc-BCZ-Group-Manager/data.db'


def find_unique_id_by_name(name):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT USER_ID FROM MEMBERS WHERE NICKNAME = ?", (name,))
        result = c.fetchone()
    except sqlite3.Error as e:
        print(e)    
    finally:
        if conn:
            conn.close()
        if result:
            return str(result[0])
        else:
            return 'None'

def find_unique_id(avatar_url, nickname=None):
    # avatar=https://vol-v6.bczcdn.com/ugc/990656050/avatar/B85C89121FCF93AD96A1661B072095AE.jpg
    avatar_url = str(avatar_url)
    if 'bczcdn' in avatar_url:
        unique_id = avatar_url.split('/')[-3]
        if unique_id == 'pack' and nickname is not None: # 对方使用了默认头像
            return find_unique_id_by_name(nickname)
        return avatar_url + ': '+ str(unique_id)
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT USER_ID FROM MEMBERS WHERE AVATAR = ?", (avatar_url,))
        result = c.fetchone()
    except sqlite3.Error as e:
        print(e)    
    finally:
        if conn:
            conn.close()
    if result:
        return str(result[0])
    else:
        return 'None' if nickname is None else find_unique_id_by_name(nickname)
