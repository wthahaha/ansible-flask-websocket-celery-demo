# encoding: utf-8

import json
from app import redis
import elasticsearch
import requests
from flask import current_app


# 从redis获取所有的资产硬件数据
def get_device_data_from_redis():
    prefix = current_app.config.get("ES_KEY_PREFIX", "zeus_cmdb_device_info:")
    device_data_keys = redis.keys(prefix + "*")
    for key in device_data_keys:
        device_data = redis.get(key)
        yield device_data

# 根据序列号或者资产编号从es搜索数据
def get_all_device_data_from_cmdb_es(serial_number=None, nic_id=None):
    es_host = current_app.config.get("ES_HOST", "")
    es_port = current_app.config.get("ES_PORT", "")
    es_index = current_app.config.get("ES_INDEX", "")
    es = elasticsearch.Elasticsearch([{"host": es_host, "port": es_port}])
    try:
        if serial_number:
            qbody = {"query": {"match": {"serial_number": serial_number}}}
        if nic_id:
            qbody = {"query": {"match": {"nic_id": nic_id}}}
        res = es.search(
            index=es_index, doc_type="all", body=json.dumps(qbody)
        )
        device_hits_data = res["hits"]["hits"][0]["_source"]
        
        return device_hits_data
    except Exception as e:
        return []

    
class UpdateCmdbMeta(object):
    def __init__(self):
        self.model_api_url = current_app.config.get("UPDATE_CMDB_EMAIL", "")
        self.email = current_app.config.get("UPDATE_CMDB_EMAIL", "")
        self.passwd = current_app.config.get("UPDATE_CMDB_PASS", "")
        self.cmdb_token_api = current_app.config.get("UPDATE_CMDB_TOKEN_API", "")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Authorization": self.get_token(), 
        }

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Authorization": self.get_token(), 
        }

    def get_all_item(self, api_url):
        response_data = requests.get(api_url, headers=self.headers)
        data_list = response_data.json()["data"]
        return data_list

    def get_model_id(self, device_type_id):
        """items:{}

        """
        all_device_data = self.get_all_item(self.model_api_url)
        brand = self.items.get("设备品牌")
        model = self.items.get("设备型号")
        for item in all_device_data:
            if item["device_brand"] == brand and item["device_model"] == model:
                brand_id = item["id"]
                return brand_id
        brand_msg_dict = {
            "brand": brand,
            "model": model,
            "device_type": str(device_type_id),
            "height": "1",
        }
        response_data = requests.post(
            self.model_api_url, data=json.dumps(brand_msg_dict), headers=self.headers
        )
        print(response_data.json())
        return_data = response_data.json()["data"]
        if return_data:
            result = str(return_data["Location"])
            brand_id = result.split("/")[6]
            return brand_id

    # def get_idc_id(self, api=None):
    #     if api:
    #         self.api_url = api
    #     idc_id = ""
    #     all_device_data = self.get_all_item()
    #     idc_name = self.items.get("设备所在机房")
    #     for item in all_device_data:
    #         if item["name"] == idc_name:
    #             idc_id = item["id"]
    #             return idc_id
    #     if idc_id:
    #         return idc_id
    #     else:
    #         msg_dict = {"name": idc_name}
    #         response_data = requests.post(
    #             self.api_url, data=json.dumps(msg_dict), headers=self.header
    #         )
    #         return_data = response_data.json()["data"]
    #         print(response_data.json(), "IIIIIIIIIIIIIIIDD")
    #         result = str(return_data["Location"])
    #         idc_id = result.split("/")[6]
    #         return idc_id

    # def get_cabinet_id(self, idc_id):
    #     all_device_data = self.get_all_item()
    #     cabinet_name = self.items.get("设备所在机柜")
    #     cabinet_location = cabinet_name
    #     idc_name = self.items.get("设备所在机房")
    #     idc_id = idc_id
    #     # idc_id = self.get_idc_id(api="http://zeus.cnnic.cn/api/v1.0/device_types/idc/")
    #     # idc_id = 2
    #     for item in all_device_data:
    #         if item["name"] == cabinet_name and item["idc"] == idc_name:
    #             cabinet_id = item["id"]
    #             return cabinet_id

    #     # 添加机柜id接口有问题
    #     msg_dict = {
    #         "name": cabinet_name,
    #         "idc_id": idc_id,
    #         "layer": 48,
    #         "location": cabinet_location,
    #     }
    #     response_data = requests.post(
    #         self.api_url, data=json.dumps(msg_dict), headers=self.header
    #     )
    #     print(response_data.json())
    #     return_data = response_data.json()["data"]
    #     if return_data:
    #         result = str(return_data["Location"])
    #         cabinet_id = result.split("/")[6]
    #         return cabinet_id

    # def get_department_id(self):
    #     all_device_data = self.get_all_item()
    #     department_name = self.items.get("所属部门")
    #     department_id = 11
    #     for item in all_device_data:
    #         if item["name"] == department_name:
    #             brand_id = item["id"]
    #             return brand_id

    #     msg_dict = {"name": department_name}
    #     response_data = requests.post(
    #         self.api_url, data=json.dumps(msg_dict), headers=self.header
    #     )
    #     print(response_data.json())

    #     return_data = response_data.json()["data"]
    #     if return_data:
    #         result = str(return_data["Location"])
    #         department_id = result.split("/")[6]
    #         return department_id

    # def get_device_type_id(self):
    #     all_device_data = self.get_all_item()
    #     device_type = self.items.get("设备类型")
    #     type_id = 1
    #     for item in all_device_data:
    #         if item["name"] == device_type:
    #             type_id = item["id"]
    #             return type_id
    #     msg_dict = {"name": device_type}
    #     response_data = requests.post(
    #         self.api_url, data=json.dumps(msg_dict), headers=self.header
    #     )
    #     print(response_data.json())
    #     return_data = response_data.json()["data"]
    #     if return_data:
    #         result = str(return_data["Location"])
    #         type_id = result.split("/")[6]
    #         return type_id

    # def get_status_id(self):
    #     all_device_data = self.get_all_item()
    #     device_status = self.items.get("设备状态")
    #     status_id = "1"  # 默认为库存状态
    #     for item in all_device_data:
    #         if item["status_name"] == device_status:
    #             status_id = item["id"]
    #     return status_id

    def get_token(self):
        response = requests.post(self.cmdb_token_api, data=json.dumps({"email":self.email, "password": self.passwd}))
        token = response.json()["data"].get("token", "")
        print(token)
        return token

def format_ansible_response_device_data(device_data):
    ansible_hardware_data = device_data["status"]
    ansible_hardware_data = json.loads(ansible_hardware_data)
    ansible_hardware_data_success = ansible_hardware_data.get(
        "success", "")
    new_update_data_dict = {}
    if ansible_hardware_data_success:
        for host in ansible_hardware_data_success:
            """
            host = {"success": {"192.168.204.132": {"invocation": {"module_args": {"filter": "*", "gather_subset": ["hardware"],
                "fact_path": "/etc/ansible/facts.d", "gather_timeout": 10}}, 
                "ansible_facts": {"ansible_product_serial": "6CU3240C5M", "ansible_form_factor": "Rack Mount Chassis"
            """
            hardware_data = ansible_hardware_data_success[host]["ansible_facts"]
            device_size_total = 0
            ansible_devices = hardware_data['ansible_devices']
            # 获取磁盘总大小：G
            for device in ansible_devices:
                if device.startswith('sd'):
                    if "GB" in ansible_devices[device]["size"]:
                        device_size = float(
                            ansible_devices[device]["size"].replace("GB", ""))

                    elif "TB" in ansible_devices[device]["size"]:
                        print(ansible_devices[device]["size"], "BBBBBBBBBBBBBB")
                        device_size = 1024 * float(
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
            new_update_data_dict["disk_size"] = int(float(device_size_total)+0.5)
            new_update_data_dict["memory_size"] = int(float(total_memory)+0.5)
            new_update_data_dict["cpu_number"] = cpu_count
            new_update_data_dict["os_name"] = os_name
            new_update_data_dict["os_version_bit"] = os_version_bit
            new_update_data_dict["virtualization_type"] = virtualization_type
            new_update_data_dict["ansible_system_vendor"] = ansible_system_vendor
            new_update_data_dict["ansible_product_name"] = ansible_product_name
            new_update_data_dict["ansible_product_serial"] = ansible_product_serial
            new_update_data_dict["ansible_hostname"] = ansible_hostname
            new_update_data_dict["ansible_all_ipv4_addresses"] = ansible_all_ipv4_addresses
            new_update_data_dict["ansible_all_ipv6_addresses"] = ansible_all_ipv6_addresses
            device_data_from_es = get_all_device_data_from_cmdb_es(serial_number=ansible_product_serial)
            print(device_data_from_es,"EEEEEEEEEEEE")
            if device_data_from_es:
                new_update_data_dict["device_id"] = device_data_from_es["id"]
                redis.set("zeus_cmdb_device_info:%s"%(device_data_from_es["id"]), json.dumps(new_update_data_dict))
            else:
                # 如果设备序列号无法在es中查到，说明cmdb没有录入该设备，需要提示设备管理员
                pass
    else:
        new_update_data_dict = ansible_hardware_data
    return new_update_data_dict
