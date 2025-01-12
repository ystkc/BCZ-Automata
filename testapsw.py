'''apsw测试机：第一次测试时，
sqlite 5us per row 
apsw 0.8us per row
不知为何，改了MEMBER表结构，将NICKNAME拆了一个表出去之后，sqlite变快了？
sqlite 1.01us per row
apsw 1.23us per row
(都是没插电情况，插电更快，sqlite可以去到0.53us per row)'''

import apsw
import time

def load_and_optimize_database(file_path):
    # 加载数据库到内存
    file_conn = apsw.Connection(file_path)
    # return file_conn
    memory_conn = apsw.Connection(":memory:")
    backup = memory_conn.backup("main", file_conn, "main") # 大问题，后面才是被备份的数据库，前面的会被覆盖
    while not backup.done:
        backup.step(-1)
    # # 获取所有表名
    # cursor = file_conn.cursor()
    # cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    # print(cursor.fetchall())
    # # 设置优化参数
    # cursor.execute("PRAGMA synchronous = OFF;")
    # cursor.execute("PRAGMA journal_mode = WAL;")
    # cursor.execute("PRAGMA cache_size = -524288;")  # 512MB 缓存
    # cursor.execute("PRAGMA temp_store = MEMORY;")
    # cursor.close()
    return memory_conn


if __name__ == "__main__":
    db_file = "../BCZ-Notice-Examiner/bcz_notice.db"
    table_name = "MEMBERS"

    # 用sqlite3实现相同功能，对比速度
    import sqlite3
    start_time = time.time()
    # file_conn = sqlite3.connect(db_file)
    # # 读取到内存中
    # conn = sqlite3.connect(":memory:")
    # file_conn.backup(conn)
    # file_conn.close()
    conn = sqlite3.connect(db_file, uri=True)
    print(f"Loaded database in {(time.time() - start_time)*100000:.2f} us")
    cursor = conn.cursor()
    # 打印表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print(cursor.fetchall())
    
    # cursor.execute("PRAGMA synchronous = OFF;")
    # cursor.execute("PRAGMA cache_size = -131072;")
    # cursor.execute("PRAGMA temp_store = MEMORY;")
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Table {table_name} has {count} rows")
    cursor.close()

    start_time = time.time()
    for i in range(0, count-1, count):
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {count} OFFSET {i}")
        data = cursor.fetchall()
        print(f"Fetched {len(data)} rows")
    print(f"Fetched all rows in {(time.time() - start_time)*100000:.2f} us, Average {(time.time() - start_time)*100000/count:.2f} us per row")
    conn.close()
    exit(0)
    # apsw
    start_time = time.time()
    conn = load_and_optimize_database(db_file)
    print(f"Loaded database in {(time.time() - start_time)*100000:.2f} us")


    # 读取表长度
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Table {table_name} has {count} rows")
    cursor.close()

    start_time = time.time()
    for i in range(0, count-1, count):
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {count} OFFSET {i}")
        data = cursor.fetchall()
        print(f"Fetched {len(data)} rows")
    print(f"Fetched all rows in {(time.time() - start_time)*100000:.2f} us, Average {(time.time() - start_time)*100000/count:.2f} us per row")
    conn.close()


