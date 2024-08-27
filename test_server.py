import socket  
  
def http_server():  
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    server_socket.bind(('localhost', 8080))  
    server_socket.listen(1)  
    print("Server is listening on port 8080...")  
  
    while True:  
        # 接受连接  
        client_connection, client_address = server_socket.accept()  
  
        request = client_connection.recv(1024).decode()  
        print(f"Received request: {request}")  
  
        # 简单的HTTP响应  
        http_response = """\  
HTTP/1.1 200 OK  
  
<html>  
<head><title>Hello, world!</title></head>  
<body>  
<h1>Hello, world!</h1>  
<p>This is a simple HTTP server.</p>  
</body>  
</html>  
"""  
  
        # 发送响应  
        client_connection.sendall(http_response.encode())  
        client_connection.close()  
  
if __name__ == '__main__':  
    http_server()