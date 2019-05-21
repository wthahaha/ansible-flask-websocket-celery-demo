# encoding: utf-8

import os
import time
import requests
import json
from flask import current_app
from multiprocessing import current_process
from app.ansibles.ansible_task import AnsibleTask
from app import celery
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded


@celery.task(bind=True, soft_time_limit=10)
def long_task(self, elementid, userid, iplist, url, module_name=None, module_args=None):
    """Background task that runs a long function with progress reports.
    后台任务"""
    total = len(iplist)
    for index, host in enumerate(iplist, 1):
        try:
            host = str(host)
            res = AnsibleTask(host, module_name=module_name,
                              module_args=module_args)
            current_process()._config = {'semprefix': '/mp'}
            result = res.run_translate_task()
            result = json.dumps(result)
        except SoftTimeLimitExceeded:
            host = str(host)
            result = json.dumps({host: "task exceed time, cancel task!"})
        except TimeLimitExceeded:
            host = str(host)
            result = json.dumps({host: "task exceed time, cancel task!"})
        except Exception as e:
            host = str(host)
            result = json.dumps({host: "some wrong ocured, cancel task!"})
        meta = {'current': index, 'host': host, 'total': total,
                'status': result, 'elementid': elementid, 'userid': userid}
        print(meta)
        requests.post(url, json=meta)
        # time.sleep(1)
