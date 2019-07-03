# encoding: utf-8

import os
import json
from flask import jsonify, url_for, current_app, request
from flask_restful import Resource, reqparse
import requests
from app.ansibles.ansible_task import INVENTORY
from app.ansibles.ansible_core import Runner
from app import redis, socketio, api
from tasks.task import long_task, update_cmdb_task
from app import redis
from app import utils
from app.utils import get_all_device_data_from_cmdb_es, UpdateCmdbMeta
from app.apis.view import EventView




class UpdateCmdb(Resource):

    def put(self):
        device_data_list = list(utils.get_device_data_from_redis())
        device_data = json.loads(device_data_list[0])
        return jsonify(device_data)

    def post(self):
        device_data_list = list(utils.get_device_data_from_redis())
        print(device_data_list)
        return jsonify(device_data_list[0])

    def get(self):
        """
        device_id: 如果为空，全部更新
        """
       
        update_cmdb_meta = UpdateCmdbMeta()
        headers = update_cmdb_meta.get_headers()
        ansible_module_name = "setup"
        module_args = ""
        # device_id = request.json.get("device_id", "")
        device_id = ""
        # device_id = "8"
        INVENTORY = current_app.config["INVENTORY_PATH"]
        runner = Runner(resource=INVENTORY, ansible_vault_key=current_app.config.get("ANSIBLE_VAULT_KEY", ""))
        if device_id:
            # 根据device_id获取到主机ip
            prefix = current_app.config.get("ES_KEY_PREFIX", "zeus_cmdb_device_info:")
            device_data_value = redis.get(prefix + device_id)
            device_data_value = json.loads(device_data_value)
            if not device_data_value:
                return jsonify({"messege": "can not find device, device id: %s" %device_id, "code": 404})
            str_ip_list = [device_data_value.get("ip")]
        else:
            iplist = runner.get_all_hosts()
            str_ip_list = [str(ip) for ip in iplist]
        update_cmdb_task.delay(iplist=str_ip_list, headers=headers, module_name=ansible_module_name, module_args=module_args)
        return jsonify({"messege": "update success", "code": 200})
