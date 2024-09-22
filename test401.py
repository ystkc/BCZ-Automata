import requests
from requests import 

with open('credential.txt', 'r') as f:
    username, password = f.read().split()

url = "https://www.shadlc.net/bcz-dev/"
response = requests.get(url, auth=HTTPBasicAuth('username', 'password'))
print(response.text)