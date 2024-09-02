import datetime

def get_this_month_timestamp(year, month, day):
    # 获取当月第一天的日期
    timestamp = int(datetime.datetime(year, month, 1).timestamp()) + 1
    print(timestamp)

    result = []
    for i in range(day):
        result.append([year, month, i+1, timestamp + i*86400])
        print(result[i])

    return result

print(get_this_month_timestamp(2024, 9, 30))