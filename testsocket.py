import socket  
import struct  
  
def create_socket_with_keepalive(host, port):  
    # 创建一个socket对象  
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
      
    # 启用keepalive  
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  
      
    # （可选）设置keepalive的空闲时间（TCP_KEEPIDLE）  
    # 注意：TCP_KEEPIDLE是一个非标准选项，可能在某些平台上不可用  
    # 如果需要设置，请检查你的平台是否支持，并可能需要使用setsockopt的变体或平台特定的代码  
    # 例如，在Linux上，你可能需要这样做（但注意TCP_KEEPIDLE是int类型，需要转换为适合setsockopt的格式）  
    if hasattr(socket, 'TCP_KEEPIDLE'):  
        # 假设我们想要设置keepalive的空闲时间为30秒  
        idle = 30  
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, struct.pack('L', idle))  
      
    # （可选）设置keepalive的间隔时间（TCP_KEEPINTVL）  
    # 同样，这也是一个非标准选项  
    if hasattr(socket, 'TCP_KEEPINTVL'):  
        # 假设我们想要设置keepalive的间隔时间为10秒  
        interval = 10  
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, struct.pack('L', interval))  
      
    # （可选）设置keepalive的探测次数（TCP_KEEPCNT）  
    # 这也是一个非标准选项  
    if hasattr(socket, 'TCP_KEEPCNT'):  
        # 假设我们想要设置keepalive的探测次数为5次  
        count = 5  
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, struct.pack('L', count))  
      
    # 连接到服务器  
    sock.connect((host, port))  
      
    return sock  
  
# 使用示例  
host = 'www.baidu.com'  
port = 80
sock = create_socket_with_keepalive(host, port)  
# 现在sock是一个启用了keepalive的TCP连接  
# ... 在这里使用sock进行通信 ...  
# 发送GET请求  
sock.sendall(b'GET / HTTP/1.1\r\nHost: www.baidu.com\r\n\r\n')  
# 接收响应  
response = b''  
while True:  
    data = sock.recv(4096)  
    if not data:  
        break  
    response += data  
print(response)  
# 最后，不要忘了关闭连接  
sock.close()