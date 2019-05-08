# -*- coding: utf-8 -*-

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from tempfile import NamedTemporaryFile
from ansible.plugins.callback import CallbackBase
from ansible.module_utils._text import to_bytes
from ansible.parsing.vault import VaultSecret


class Runner(object):
    """
    This is a General object for parallel execute modules.
    本方法依赖hosts文件，在调用本方法之前，需要先生成hosts文件，可以通过手动编辑或者动态生成的方式生成hosts文件。
    如果在hosts文件里指定了ansible_ssh_private_key_file、ansible_python_interpreter、ansible_ssh_user等变量，
    调用本接口时就无需再传入这些变量了,即使传了这些变量也没用，因为hosts文件中变量的优先级最高
    使用密码或公钥指定一个即可，另一个设为None。比如：如果传入了公钥参数，则self.passwords就设为None
    """

    def __init__(self, resource, *args, **kwargs):
        # resource： 可以为hosts文件的绝对路径（或者绝对路径列表）， 也可以是以逗号隔开的ip字符串，如：'1.1.1.1,2.2.2.2,3.3.3.3',只有一个ip时也要加逗号，
        # 这个ip字符串会被ansible当做hosts文件
        self.resource = resource
        self.variable_manager = None
        self.loader = None
        self.options = None
        self.passwords = None  # 主机登录密码
        self.private_key_file = None  # 登录私钥
        self.ansible_vault_key = kwargs.get(
            'ansible_vault_key', '')  # ansible加解密密码
        self.callback = ResultsCollector()  # ansible回调函数，处理返回结果
        self.ansible_ssh_user = kwargs.get(
            'ansible_ssh_user', 'root')  # 主机登录用户
        self.become_user = kwargs.get('module_name', '')  # 登录主机后切换的用户
        self.ansible_python_interpreter = kwargs.get(
            'ansible_python_interpreter', "/usr/bin/python")   # 远程机器使用的python解释器
        self.__initializeData()
        self.results_raw = {}
        # ip_list是执行ansible任务的ip列表，这个ip列表中的ip必须全都在self.resource里
        self.ip_list = kwargs.get('ip_list', [])
        self.module_name = kwargs.get('module_name', '')  # ansible调用的模块名
        self.module_args = kwargs.get('module_args', '')  # 模块需要的参数

    def __initializeData(self):
        """
        初始化ansible
        """

        Options = namedtuple('Options',
                             ['ansible_python_interpreter', 'connection', 'module_path', 'forks', 'become',
                              'become_method', 'become_user', 'check',
                              'diff', 'private_key_file', 'remote_user'])
        self.loader = DataLoader()
        # 加载hosts文件解密密码
        self.loader.set_vault_secrets(
            [('default', VaultSecret(_bytes=to_bytes(self.ansible_vault_key)))])
        self.options = Options(ansible_python_interpreter=self.ansible_python_interpreter,
                               connection='ssh', module_path='', forks=100, become=None,
                               become_method=None, become_user=self.become_user,
                               check=False, diff=False, private_key_file=self.private_key_file,
                               remote_user=self.ansible_ssh_user)

        self.passwords = dict(conn_pass=self.passwords)

        self.inventory = InventoryManager(
            loader=self.loader, sources=self.resource)

        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory)

    def run(self):
        """
        运行ansible任务.

        """
        # create play with tasks
        play_source = dict(
            name="Ansible Play",
            hosts=self.ip_list,
            gather_facts='no',
            tasks=[
                dict(action=dict(module=self.module_name, args=self.module_args))
            ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        # 运行
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback='default',
            )
            tqm._stdout_callback = self.callback
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()
        return result

    def get_result(self):

        # 将ansible返回的数据组装为自己需要的数据格式

        self.results_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
        for host, result in self.callback.host_ok.items():
            self.results_raw['success'][host] = result._result

        for host, result in self.callback.host_failed.items():
            self.results_raw['failed'][host] = result._result

        for host, result in self.callback.host_unreachable.items():
            self.results_raw['unreachable'][host] = result._result['msg']

        return self.results_raw


class ResultsCollector(CallbackBase):
    """
    结果处理回调
    重写CallbackBase的v2函数
    """

    def __init__(self, *args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result
