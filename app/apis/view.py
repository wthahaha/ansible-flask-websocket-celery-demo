# encoding: utf-8

import uuid
import os
import random
import json
from collections import Counter
from flask import request, abort, jsonify, g, url_for, current_app, session
from flask_restful import Resource, reqparse
from flask_socketio import (
    emit,
    disconnect
)
from app.ansibles.ansible_task import INVENTORY
from app.ansibles.ansible_core import Runner
from app import redis, socketio, api
from tasks.task import long_task
from app import redis

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
        # gather_subset="hardware" 只获取hardware的数据
        print(request.json)
        ansible_module_name = request.json['ansible_module_name']
        ansible_module_args = request.json['ansible_module_args']
        print(userid, "接收前端发送到后台的userid------")
        # 启动long_task后台任务，并将其放到celery中执行
        # iplist = ["192.168.204.131", "192.168.204.132", "192.168.204.133"]
        INVENTORY = current_app.config["INVENTORY_PATH"]
        ip_group = "ipv4_moniters"
        runner = Runner(resource=INVENTORY, ip_list=ip_group,
                        ansible_vault_key='devops')
        iplist = runner.get_all_hosts()
        module_name = ansible_module_name
        module_args = ansible_module_args
        # module_name = 'copy'
        # module_args = "src=%s dest=%s" % ('/tmp/1.txt', '/tmp/')
        str_ip_list = []
        for ip in iplist:
            str_ip_list.append(str(ip))

        task = long_task.delay(elementid, userid, iplist=str_ip_list, url=api.url_for(
            EventView, _external=True), module_name=module_name, module_args=module_args)
        return jsonify({"messege": "", "code": 200})


class EventView(Resource):
    def post(self):
        # 接收long_task后台任务返回的数据，并发送到前端celerystatus事件（可以在这里进一步加工处理后台任务返回的数据，然后再发送到前端）
        userid = request.json['userid']
        data = request.json

        ansible_hardware_data = data["status"]
        ansible_hardware_data = json.loads(ansible_hardware_data)
        ansible_hardware_data_success = ansible_hardware_data.get(
            "success", None)
        new_update_data_dict = {}
        if ansible_hardware_data_success:
            for host in ansible_hardware_data_success:
                """
                {"success": {"192.168.204.132": {"invocation": {"module_args": {"filter": "*", "gather_subset": ["hardware"],
                 "fact_path": "/etc/ansible/facts.d", "gather_timeout": 10}}, 
                 "ansible_facts": {"ansible_product_serial": "6CU3240C5M", "ansible_form_factor": "Rack Mount Chassis"
                """
                hardware_data = ansible_hardware_data_success[host]["ansible_facts"]
                device_size_total = 0
                ansible_devices = hardware_data['ansible_devices']
                # 获取磁盘总大小：G
                # print succ
                for device in ansible_devices:
                    if device.startswith('sd'):
                        if "GB" in ansible_devices[device]["size"]:
                            device_size = float(
                                ansible_devices[device]["size"].replace("GB", ""))

                        elif "TB" in ansible_devices[device]["size"]:
                            device_size = float(
                                ansible_devices[device]["size"].replace("TB", ""))
                        device_size_total += device_size
                device_size_total = format(device_size_total, ".1f")
                # 获取内存总大小：G
                total_memory = int(hardware_data
                                   ['ansible_memtotal_mb'])/1024

                # 获取cpu个数
                cpu_count = int(hardware_data
                                ["ansible_processor_count"])

                # 获取操作系统名称  centos  6.5-x86_64
                os_name = hardware_data["ansible_distribution"]
                os_version = hardware_data["ansible_distribution_version"]
                os_bit = hardware_data["ansible_architecture"]
                os_version_bit = os_version + "-" + os_bit

                # 是否为虚拟机， VMware 或kvm是虚拟机，由于ansible无法区分刀片和架式机，故设备类型只更新虚拟机
                virtualization_type = hardware_data["ansible_virtualization_type"]
                # 设备品牌
                ansible_system_vendor = hardware_data["ansible_system_vendor"]
                # 设备型号
                ansible_product_name = hardware_data["ansible_product_name"]
                # 设备序列号
                ansible_product_serial = hardware_data["ansible_product_serial"]
                # 主机名
                ansible_hostname = hardware_data["ansible_nodename"]
                # 所有的ipv4地址
                ansible_all_ipv4_addresses = hardware_data["ansible_all_ipv4_addresses"]
                # 所有的ipv6地址
                ansible_all_ipv6_addresses = hardware_data["ansible_all_ipv6_addresses"]

                new_update_data_dict["ip"] = host
                new_update_data_dict["device_size_total"] = device_size_total
                new_update_data_dict["total_memory"] = total_memory
                new_update_data_dict["cpu_count"] = cpu_count
                new_update_data_dict["os_name"] = os_name
                new_update_data_dict["os_version_bit"] = os_version_bit
                new_update_data_dict["virtualization_type"] = virtualization_type
                new_update_data_dict["ansible_system_vendor"] = ansible_system_vendor
                new_update_data_dict["ansible_product_name"] = ansible_product_name
                new_update_data_dict["ansible_product_serial"] = ansible_product_serial
                new_update_data_dict["ansible_hostname"] = ansible_hostname
                new_update_data_dict["ansible_all_ipv4_addresses"] = ansible_all_ipv4_addresses
                new_update_data_dict["ansible_all_ipv6_addresses"] = ansible_all_ipv6_addresses

                redis.set("info:"+host, json.dumps(new_update_data_dict))
        else:
            print(ansible_hardware_data, "超时")
            new_update_data_dict = ansible_hardware_data

        namespace = current_app.clients.get(userid)
        if namespace and data:
            data["status"] = new_update_data_dict
            # 要发送的data必须的是json
            emit('celerystatus', data,
                 broadcast=True, namespace=namespace)
            return 'ok'
        return 'error', 404


class ClientView(Resource):
    def get(self):
        print("clients")
        return jsonify({'clients': current_app.clients.keys()})


class ClientIpListView(Resource):
    def get(self):
        INVENTORY = current_app.config["INVENTORY_PATH"]
        print(INVENTORY)
        runner = Runner(resource=INVENTORY, ip_list="all",
                        ansible_vault_key='devops')
        print(INVENTORY, "IN")
        res = runner.get_all_hosts()
        print(res, type(res))
        return jsonify({"res": str(res)})


# 前端websocket连接过来后，执行的第二个函数
# 接收命名空间为/events、名字为"status"事件的数据
@socketio.on('status', namespace='/events')
def events_message(message):
    print("前端websocket连接过来后，执行的第二个函数")
    print(message, "接收到的message")
    # 将事件名为“status”的数据（{'status': message['status']}），发送到前端
    emit('status', {'status': message['status'], "userid":current_app.clients})

# 接收/events命名空间的disconnect request事件的路由
@socketio.on('disconnect request', namespace='/events')
def disconnect_request():
    emit('status', {'status': 'disconnected'})
    disconnect()

# 前端websocket连接过来后，执行的第一个函数
# 接收命名空间为/events、名字为“connect”事件的数据
@socketio.on('connect', namespace='/events')
def events_connect():
    print("前端websocket连接过来后，执行的第一个函数")
    del current_app.clients[session['userid']]
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
    emit('status', {'status': 'connected', 'userid': userid})


@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    del current_app.clients[session['userid']]
    print('Client %s disconnected' % session['userid'])
