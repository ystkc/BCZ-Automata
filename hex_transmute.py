res_string = ""
line = input('fiddler parser, end with enter:')
while line != '':
    res_string += line
    res_string += '\n'
    line = input('fiddler parser, end with enter:')



result = {"path":"","method":"","Headers":{}}

# parse url
url_start = res_string.find(' ')
url_end = res_string.find(' ',url_start+1)
result["path"] = res_string[url_start+1:url_end]

# parse method
method_start = 0
method_end = res_string.find(' ')
result["method"] = res_string[method_start:method_end]

# parse headers
headers_start = res_string.find('\n')
headers_end = len(res_string)
headers_str = res_string[headers_start+1:headers_end]
headers_list = headers_str.split('\n')
for header in headers_list:
    if ':' in header:
        key,value = header.split(':',1)
        key = key.strip()
        value = value.strip()
        if key == 'Cookie':
            result["Headers"][key] = {}
        else:
            result["Headers"][key] = value

# parse cookies
if 'Cookie' in result["Headers"]:
    cookie_start = headers_str.find('Cookie:')
    cookie_end = headers_str.find('\n',cookie_start+7)
    cookie_str = headers_str[cookie_start+7:cookie_end]
    cookie_list = cookie_str.split(';')
    for cookie in cookie_list:
        item = cookie.split('=',1)
        key = item[0].strip()
        value = item[1].strip()
        # print(key,value)
        result["Headers"]["Cookie"][key] = value


print(result)
# 将result放入剪切板
import pyperclip
import json
pyperclip.copy(json.dumps(result))


