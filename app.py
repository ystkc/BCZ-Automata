import sys
import time
import logging

from flask import Flask, Response, render_template, jsonify, request
from werkzeug.serving import WSGIRequestHandler, _log

from src import bcz
from src.config import Config

# if '--debug' in sys.argv or (hasattr(sys, 'gettrace') and sys.gettrace() is not None):
if '--debug' in sys.argv:
    level = logging.DEBUG
else:
    level = logging.INFO

logging.basicConfig(
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    level=level
)

WSGIRequestHandler.address_string = lambda self: self.headers.get('x-real-ip', self.client_address[0])
class MyRequestHandler(WSGIRequestHandler):
    def log(self, type, message, *args):
        _log(type, f'{self.address_string()} {message % args}\n')


app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False

config = Config()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/user', methods=['GET'])
def user():
    return render_template('user.html')

@app.route('/send_sms', methods=['POST'])
def send_sms():
    '''发送短信验证码'''
    phone = request.json.get('phone', '')
    if not phone:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        bcz.sendSmsVerifyCode(phone)
        return restful(200, '验证码已发送到您的手机，请查收')
    except Exception as e:
        return restful(400, f'{e}')

@app.route('/user_login', methods=['POST'])
def user_login():
    '''用户登陆'''
    phone = request.json.get('phone', '')
    code = request.json.get('code', '')
    '''
    UserLoginResult(
        access_token='',
        is_new_user=None,
        email='',
        public_key='',
        last_device='',
        unique_id=,
        phone='',
        force_bind_phone=None,
        role_new=1,
        role=RoleInfo(role_up=None, grade=6)
    )
    '''
    data = {
        'user_id': '',
        'token': '',
    }
    # return restful(200, '登陆成功', data)
    if not phone or not code:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        result = bcz.loginWithPhone(phone, code)
        data = {
            'user_id': result.unique_id,
            'token': result.access_token,
        }
        print(result)
        return restful(200, '登陆成功', data)
    except Exception as e:
        return restful(400, f'{e}')

def restful(code: int, msg: str = '', data: dict = {}) -> Response:
    '''以RESTful的方式进行返回响应'''
    retcode = 1
    if code == 200:
        retcode = 0
    return jsonify({'code': code,
            'retcode': retcode,
            'msg': msg,
            'data': data
    }), code

if __name__ == '__main__':
    token = ""
    # print(bcz.getAllBooks(token, True))
    # print(bcz.select_book(token, 968, 10, 10, 0))
    logging.info('BCZ-Automata 启动中...')
    app.run(config.host, config.port, request_handler=MyRequestHandler)