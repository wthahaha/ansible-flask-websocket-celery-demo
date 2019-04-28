# encoding: utf-8

import os
import time
import requests
import json
from flask import current_app
from multiprocessing import current_process
from app.ansibles.ansible_task import AnsibleTask
from app import celery


@celery.task(bind=True, soft_time_limit=10)
def long_task(self, elementid, userid, iplist, url, module_name=None, module_args=None):
    """Background task that runs a long function with progress reports.
    后台任务"""
    total = len(iplist)
    for index, host in enumerate(iplist, 1):
        try:
            res = AnsibleTask(host, module_name=module_name,
                              module_args=module_args)
            current_process()._config = {'semprefix': '/mp'}
            result = res.run_translate_task()
            result = json.dumps(result)
        except Exception as e:
            result = json.dumps({host: "task exceed time, cancel task!"})
        meta = {'current': index, 'host': host, 'total': total,
                'status': result, 'elementid': elementid, 'userid': userid}
        requests.post(url, json=meta)
        time.sleep(1)
