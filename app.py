import os
import random
import time
import uuid
import json
from flask import (
    Flask,
    request,
    render_template,
    session,
    redirect,
    url_for,
    jsonify,
    current_app
)
from celery import Celery
from flask_socketio import (
    SocketIO,
    emit,
    disconnect
)
import requests
from multiprocessing import current_process
from ansibles.ansible_task import AnsibleTask

app = Flask(__name__)
app.debug = True
app.clients = {}
app.config['SECRET_KEY'] = 'top-secret!'

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['CELERY_ACCEPT_CONTENT'] = ['pickle', 'json', 'msgpack', 'yaml']

# SocketIO
socketio = SocketIO(app)

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task(bind=True, soft_time_limit=10)
def long_task(self, elementid, userid,iplist, url, module_name=None, module_args=None):
    """Background task that runs a long function with progress reports.
    模拟后台任务"""
    total = len(iplist)
    for index, host in enumerate(iplist, 1):
        try:
            if host == "192.168.204.132":
                time.sleep(60)
            print(host)
            res = AnsibleTask(host,module_name=module_name, module_args=module_args)
            current_process()._config = {'semprefix': '/mp'}
            result = res.run_translate_task()
            result = json.dumps(result)
        except Exception as e:
            result = json.dumps({host: "task exceed time, cancel task!"})
        meta={'current': index,'host':host, 'total': total,
                                'status': result,'elementid': elementid, 'userid': userid}
        requests.post(url, json=meta)
        time.sleep(1)

    # meta = {'current': 100, 'total': 100, 'status': 'Task completed!',
    #         'result': 42, 'elementid': elementid, 'userid': userid}
    # # 将任务的状态与结果数据发给服务器的event路由
    # requests.post(url, json=meta)
    





@app.route('/clients', methods=['GET'])
def clients():
    print("clients")
    return jsonify({'clients': app.clients.keys()})


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    return redirect(url_for('index'))


@app.route('/longtask', methods=['POST'])
def longtask():
    # 接收前端发送的执行后台任务的请求
    # 接收前端发送来的userid、elementid
    elementid = request.json['elementid']
    userid = request.json['userid']
    print(userid, "接收前端发送到后台的userid------")
    # 启动long_task后台任务，并将其放到celery中执行
    iplist = ["192.168.204.131","192.168.204.132","192.168.204.133"]
    # module_name = "setup"
    # module_args = ""
    module_name = 'copy'
    module_args = "src=%s dest=%s" % ('/tmp/1.txt', '/tmp/')

    task = long_task.delay(elementid, userid,iplist=iplist, url=url_for('event', _external=True),module_name=module_name,module_args=module_args)
    return jsonify({}), 202


@app.route('/event/', methods=['POST'])
def event():
    # 接收long_task后台任务返回的数据，并发送到前端celerystatus事件（可以在这里进一步加工处理后台任务返回的数据，然后再发送到前端）
    userid = request.json['userid']
    data = request.json
    print(data)
    namespace = app.clients.get(userid)
    print(namespace, 'lllllllllllllllllllllllll')
    if namespace and data:
        # 要发送的data必须的是son
        emit('celerystatus', data, broadcast=True, namespace=namespace)
        return 'ok'
    return 'error', 404

# 前端websocket连接过来后，执行的第二个函数
# 接收命名空间为/events、名字为"status"事件的数据
@socketio.on('status', namespace='/events')
def events_message(message):
    print("前端websocket连接过来后，执行的第二个函数")
    print(message, "接收到的message")
    # 将事件名为“status”的数据（{'status': message['status']}），发送到前端
    emit('status', {'status': message['status']})

# 接收/events命名空间的disconnect request事件的路由
@socketio.on('disconnect request', namespace='/events')
def disconnect_request():
    emit('status', {'status': 'Disconnected!'})
    disconnect()

# 前端websocket连接过来后，执行的第一个函数
# 接收命名空间为/events、名字为“connect”事件的数据
@socketio.on('connect', namespace='/events')
def events_connect():
    print("前端websocket连接过来后，执行的第一个函数")
    userid = str(uuid.uuid4())
    print(userid, "生成新的userid")
    session['userid'] = userid
    current_app.clients[userid] = request.namespace
    print(current_app.clients, "打印所有的current_app.clients数据")
    # 将事件名为“userid”的数据（{'userid': userid}）发到前端
    emit('userid', {'userid': userid})
    # 将事件名为“status”的数据（{'status': 'Connected user', 'userid': userid}）发到前端
    emit('status', {'status': 'Connected user', 'userid': userid})


@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    del current_app.clients[session['userid']]
    print('Client %s disconnected' % session['userid'])


if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, host="0.0.0.0")
