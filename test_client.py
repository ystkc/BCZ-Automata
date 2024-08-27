import socket  
  
def http_client():  
    host = '202.89.233.101'  
    port = 8000
  
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    client_socket.connect((host, port))  
  
    # 发送HTTP GET请求  
    request = f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"  
    client_socket.sendall(request.encode())  
  
    # 接收响应  
    response = client_socket.recv(4096).decode()  
    print(f"Received response:\n{response}")  
  
    client_socket.close()  
  
if __name__ == '__main__':  
    http_client()