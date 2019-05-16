# encoding: utf-8

import os
import logging
import ast
import json
from ansibles.ansible_core import Runner, ResultsCollector
from conf.config import Config
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY = os.path.join(BASE_DIR, 'ansible.host')
EXTRA_INVENTORY = Config.INVENTORY_PATH
print(EXTRA_INVENTORY)


class AnsibleTask(object):
    def __init__(self, iplist_or_ip, module_name, module_args):
        self.iplist_or_ip = iplist_or_ip
        self.module_name = module_name
        self.module_args = module_args

    def run_translate_task(self):
        hosts = INVENTORY
        extra_hosts = EXTRA_INVENTORY
        all_hosts = [hosts, extra_hosts]
        runner = Runner(resource=all_hosts, ip_list=self.iplist_or_ip,
                        module_name=self.module_name, module_args=self.module_args, ansible_vault_key='devops')
        runner.run()
        # 结果
        result = runner.get_result()
        # 成功
        succ = result['success']
        # 失败
        failed = result['failed']
        # 不可达
        unreachable = result['unreachable']
        return result
