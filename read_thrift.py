# read_thrift.py
'''【调试工具】读取thrift文件内容的脚本，用于测试thrift文件是否正确解析。'''
from src.thriftAPI import UserStudyApiService
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol
import base64


from src.thrift_utils import print_thrift_object



content = 'HBgLMTk5MTE1MTA5NzEYCUJBMjRFOThEMxggRENPLUFMMDAtSFVBV0VJLThkOTQ2ZjJkZGFmOTBmMTgAAA=='
print('''使用方法备忘：
1.编写thrift，编译
2.fiddler解压，从方法名后面开始复制 base64
3.从上一层结构开始（如bcz_login_result而不是UserLoginResult）
4.追踪进ttypes魔改fid+1(搞定了记得改回来)''')
decoded_content = base64.b64decode(content)
# print(decoded_content)
transport = TTransport.TMemoryBuffer(decoded_content)
protocol = TCompactProtocol.TCompactProtocol(transport)

from src.thriftAPI.ttypes import *
# client = UserStudyApiService.Client(protocol)
# 
args = bcz_login_args()
args.read(protocol)
print_thrift_object(args)
transport.close()

# print_thrift_object(result)

# i32读取方式：
# protocol.readStructBegin()
# protocol.readFieldBegin()
# args = protocol.readI32()
# protocol.readFieldEnd()
# protocol.readStructEnd()
# print_thrift_object(args)
# 由于BCZ服务器都是将success字段序号设置0，所以必须直接读取success字段的值，若出现AssertionError则是没有调用begin




# 输出结果：
# win_streak_status_args示例：client_date = 20240831
# get_startup_ad_args示例：screen_length=1280; screen_width=720; android_id='8d946f2ddaf90f18';oaid='unknown'
# update_done_data_args示例：last_sync_at:10位