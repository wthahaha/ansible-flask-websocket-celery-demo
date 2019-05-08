# encoding: utf-8

import uuid
import os
import random
from collections import Counter
from flask import request, abort, jsonify, g, url_for, current_app, session
from flask_restful import Resource, reqparse, fields, marshal_with
from flask_socketio import (
    emit,
    disconnect
)
from app.ansibles.ansible_task import INVENTORY
from app.ansibles.ansible_core import Runner
from app import redis, socketio, api
from tasks.task import long_task


class AnsibleTaskView(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('elementid', type=str, location=[
                                   'json', 'args', 'headers'])
        self.args = self.reqparse.parse_args()
        super(AnsibleTaskView, self).__init__()

    def get(self):
        pass

    def post(self):
        # 接收前端发送的执行后台任务的请求
        # 接收前端发送来的userid、elementid
        elementid = request.json['elementid']
        userid = request.json['userid']
        print(userid, "接收前端发送到后台的userid------")
        # 启动long_task后台任务，并将其放到celery中执行
        iplist = ["192.168.204.131", "192.168.204.132", "192.168.204.133"]
        iplist = ["218.241.108.243", "218.241.108.195"]
        module_name = "setup"
        module_args = ""
        # module_name = 'copy'
        # module_args = "src=%s dest=%s" % ('/tmp/1.txt', '/tmp/')

        task = long_task.delay(elementid, userid, iplist=iplist, url=api.url_for(
            EventView, _external=True), module_name=module_name, module_args=module_args)
        return {}, 202


class EventView(Resource):
    def post(self):
        # 接收long_task后台任务返回的数据，并发送到前端celerystatus事件（可以在这里进一步加工处理后台任务返回的数据，然后再发送到前端）
        userid = request.json['userid']
        data = request.json
        print(data)
        namespace = current_app.clients.get(userid)
        if namespace and data:
            # 要发送的data必须的是json
            emit('celerystatus', data, broadcast=True, namespace=namespace)
            return 'ok'
        return 'error', 404

class ClientView(Resource):
    def get(self):
        print("clients")
        return jsonify({'clients': current_app.clients.keys()})

import json
class ClientIpListView(Resource):
    def get(self):
        INVENTORY = "/root/flask-celery-websocket-demo/app/ansibles/ansible.host"
        runner = Runner(resource=INVENTORY, ip_list="all", ansible_vault_key='devops')
        print(INVENTORY, "IN")
        res = runner.get_all_hosts()
        print(res,type(res))
        return jsonify({"res":str(res)})



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
    urls = api.url_for(
            EventView, _external=True)
    print(urls)
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
