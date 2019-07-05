# encoding: utf-8

import os
import time
import requests
import json
from flask import current_app
from multiprocessing import current_process
from app.ansibles.ansible_task import AnsibleTask
from app import celery
from app import redis
from app import utils
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded


@celery.task(bind=True, soft_time_limit=60)
def long_task(self, elementid, userid, iplist, url, module_name=None, module_args=None, next_ip=""):
    """Background task that runs a long function with progress reports.
    后台任务"""
    total = len(iplist)
    for index, host in enumerate(iplist, 1):
        host = str(host)
        try:
            res = AnsibleTask(host, module_name=module_name,
                              module_args=module_args)
            current_process()._config = {'semprefix': '/mp'}
            result = res.run_translate_task()
            result = json.dumps(result)
        except SoftTimeLimitExceeded:
            result = json.dumps({"success": {}, "unreachable": {}, "failed": {
                                host: "task exceed time, cancel task!"}})
        except TimeLimitExceeded:
            result = json.dumps({"success": {}, "unreachable": {}, "failed": {
                                host: "task exceed time, cancel task!"}})
        except Exception as e:
            result = json.dumps({"success": {}, "unreachable": {}, "failed": {host: e}})
        try:
            next_ip = iplist[index]
        except IndexError:
            next_ip = "没有了"
        meta = {'current': index, 'host': host, 'total': total,
                'status': result, 'elementid': elementid, 'userid': userid, "next_ip": next_ip}
        requests.post(url, json=meta)

@celery.task(bind=True, soft_time_limit=60)
def update_cmdb_task(self, iplist, headers, module_name=None, module_args=None):
    """Background task that runs a long function with progress reports.
    后台任务"""

    for _, host in enumerate(iplist, 1):
        host = str(host)
        try:
            res = AnsibleTask(host, module_name=module_name, module_args=module_args)
            current_process()._config = {'semprefix': '/mp'}
            result = res.run_translate_task()
            result = json.dumps(result)
        except Exception as e:
            result = json.dumps({"success": {}, "unreachable": {}, "failed": {host: e}})
        meta = {'host': host, 'status': result}
        format_data = utils.format_ansible_response_device_data(meta)
        device_id = format_data.get("device_id", "")
        if device_id:
            update_cmdb_url = current_app.config.get("UPDATE_CMDB_URL", "") + str(device_id)
            try:
                res = requests.put(update_cmdb_url, json=format_data, headers=headers)
                print(res.json())
            except Exception as e:
                print(e)

