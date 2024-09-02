from src.thriftAPI import UserStudyApiService
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol
import base64


def print_thrift_object(obj, indent=0, index=-1):  
    """  
    递归打印Thrift对象及其嵌套结构  
    :param obj: Thrift对象  
    :param indent: 用于缩进的空格数  
    """  
    index_str = ''
    if index != -1:  
        index_str = f'[{index}]:'  
    indent_str = ' ' * indent  
    if isinstance(obj, dict):  
        for key, value in obj.items():  
            print(f"{indent_str}{index_str}{key}:")  
            print_thrift_object(value, indent + 4)  
    elif isinstance(obj, list):  
        for index, item in enumerate(obj):  
            print_thrift_object(item, indent, index = index)  
    elif hasattr(obj, '__dict__'):  
        # Thrift生成的类通常具有__dict__属性，包含字段名和值  
        for key, value in obj.__dict__.items():  
            # 忽略Thrift内部使用的属性，如thrift_spec, thrift_field_annotations等  
            if not key.startswith('_'):  
                print(f"{indent_str}{index_str}{key}:")  
                print_thrift_object(value, indent + 4)  
    else:  
        # 处理基本类型（如int, str等）  
        s = '\'' if isinstance(obj, str) else ''  
        print(f"{indent_str}{index_str}{s}{obj}{s}")  



content = 'HBgQMDMyYWU4Zjg0Mjc4ODVkNxgGSFVBV0VJGAhEQ08tQUwwMBgHYW5kcm9pZBgCMzIYBTcuNi4xFYjq3QYYAnFxGAliYWljaXpoYW4AAA=='
# 要从方法名后面开始复制！不然解读不了
decoded_content = base64.b64decode(content)
print(decoded_content)
transport = TTransport.TMemoryBuffer(decoded_content)
protocol = TCompactProtocol.TCompactProtocol(transport)

from src.thriftAPI.ttypes import get_app_beta_update_info_args
args = get_app_beta_update_info_args()
args.read(protocol) 
print_thrift_object(args)

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