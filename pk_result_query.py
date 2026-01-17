# pk_result_query.py
'''【独立工具】查找pk对局记录'''
# 读取/logs/pk_%YYYY-%MM-%DD %HH-%MM-%SS.csv文件，供用户查询
# 格式：我的名字,对手ID,对手名字,我的分数,对手分数
# 查询方式：对手id或对手名字（允许子串匹配），列出所有符合条件的对局记录
import csv
import os
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def read_pk_result(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        result = []
        for row in reader:
            result.append(row)
        return result

def search_pk_result(result, query_str):
    # 转义
    query_str = re.escape(query_str)
    pattern = re.compile(query_str, re.IGNORECASE)
    matches = []
    for row in result:
        if pattern.search(row[0]) or pattern.search(row[1]) or pattern.search(row[2]):
            matches.append(row)
    return matches

def print_pk_result(date_str, matches):
    if len(matches) == 0:
        # print("No match found.")
        ...
    else:
        print(date_str)
        print("{:20s} {:10s} {:20s} {:10s} {:10s}".format("My Name", "Opponent ID", "Opponent Name", "My Score", "Opponent Score"))
        for row in matches:
            print("{:20s} {:10s} {:20s} {:10s} {:10s}".format(row[0], row[1], row[2], row[3], row[4]))
        print()

if __name__ == '__main__':
    
    # 加载所有pk结果文件，并储存对应日期
    results = []
    for filename in os.listdir('logs'):
        if filename.startswith('pk_') and filename.endswith('.csv'):
            date_str = filename.split('_')[1].split(' ')[0]
            results.append((filename, read_pk_result(os.path.join('logs', filename))))
    
    # 显示所有对局记录
    while True:
        query_str = input("Enter query string: ")
        for result in results:
            matches = search_pk_result(result[1], query_str)
            print_pk_result(result[0], matches)
        print('\033[32mAll results have been shown.\033[0m')