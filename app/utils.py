# encoding: utf-8

import json
from app import redis
import elasticsearch
from elasticsearch import helpers
import requests
from flask import current_app


# 从redis获取所有的ansible资产硬件数据
def get_device_data_from_redis():
    prefix = current_app.config.get("ES_KEY_PREFIX", "zeus_cmdb_device_info:")
    device_data_keys = redis.keys(prefix + "*")
    for key in device_data_keys:
        device_data = redis.get(key)
        yield device_data

# 根据序列号或者资产编号从es搜索数据
def get_all_device_data_from_cmdb_es(serial_number=None, nic_id=None, es_index=""):
    es_host = current_app.config.get("ES_HOST", "")
    es_port = current_app.config.get("ES_PORT", "")
    es = elasticsearch.Elasticsearch([{"host": es_host, "port": es_port}])
    try:
        qbody = {"query": {"match_all": {}}}
        if serial_number:
            qbody = {"query": {"match": {"serial_number": serial_number}}}
        if nic_id:
            qbody = {"query": {"match": {"nic_id": nic_id}}}

        res = helpers.scan(
            client=es,
            query=qbody,
            scroll="5m",
            index=es_index,
            doc_type="all",
            timeout="1m"
        )
        return res
    except Exception as e:
        print(e)
        return []

    
class UpdateCmdbMeta(object):
    def __init__(self):
        self.email = current_app.config.get("UPDATE_CMDB_EMAIL", "")
        self.passwd = current_app.config.get("UPDATE_CMDB_PASS", "")
        self.cmdb_token_api = current_app.config.get("UPDATE_CMDB_TOKEN_API", "")
        self.update_cmdb_os_url = current_app.config.get("UPDATE_CMDB_OS_API", "")

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Authorization": self.get_token(), 
        }

    def get_all_item(self, api_url):
        response_data = requests.get(api_url, headers=self.get_headers())
        data_list = response_data.json()["data"]
        return data_list

    def get_token(self):
        response = requests.post(self.cmdb_token_api, data=json.dumps({"email":self.email, "password": self.passwd}))
        token = response.json()["data"].get("token", "")
        return token

    def get_all_os(self):
        """
        从es获取所有操作系统
        """
        os_data_from_es = list(get_all_device_data_from_cmdb_es(es_index="cmdb_os"))
        return os_data_from_es

    def get_os_id(self, os_name="", os_version_bit=""):
        """
        从es获取操作系统id
        """
        os_data_list = self.get_all_os()
        os_id = ""
        if os_data_list:
            for data in os_data_list:
                if data["_source"].get("os_name", "") == os_name and data["_source"].get("os_version", "") == os_version_bit:
                    os_id = data["_source"].get("id", "")
                    return os_id
            try:
                # cmdb接口字段名为os_version
                os_msg_dict = {"os_name": os_name, "os_version": os_version_bit}
                response_data = requests.post(self.update_cmdb_os_url, data=os_msg_dict, headers=self.get_headers())
                return_data = response_data.json()["data"]
                result = str(return_data["Location"])
                os_id = result.split('/')[6]
            except Exception as e:
                print(e)
        return os_id

    def get_ip_id(self, ip=""):
        """
        从cmdb获取操作系统id
        """
        ip_id = -1
        res = requests.get()
        if os_data_list:
            for data in os_data_list:
                if data["_source"].get("os_name", "") == os_name and data["_source"].get("os_version", "") == os_version_bit:
                    os_id = data["_source"].get("id", "")
                    return os_id
            try:
                # cmdb接口字段名为os_version
                os_msg_dict = {"os_name": os_name, "os_version": os_version_bit}
                response_data = requests.post(self.update_cmdb_os_url, data=os_msg_dict, headers=self.get_headers())
                return_data = response_data.json()["data"]
                result = str(return_data["Location"])
                os_id = result.split('/')[6]
            except Exception as e:
                print(e)
        return os_id

def format_ansible_response_device_data(device_data):
    ansible_hardware_data = device_data["status"]
    ansible_hardware_data = json.loads(ansible_hardware_data)
    ansible_hardware_data_success = ansible_hardware_data.get("success", "")
    new_update_data_dict = {}
    if ansible_hardware_data_success:
        for host in ansible_hardware_data_success:
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
            # 获取os_id
            if os_name and os_version_bit:
                update_cmdb_meta = UpdateCmdbMeta()
                os_id = update_cmdb_meta.get_os_id(os_name, os_version_bit)
            # 获取ip地址id


            new_update_data_dict["ip"] = host
            new_update_data_dict["disk_size"] = int(float(device_size_total)+0.5)
            new_update_data_dict["memory_size"] = int(float(total_memory)+0.5)
            new_update_data_dict["cpu_number"] = cpu_count
            new_update_data_dict["os_name"] = os_name
            new_update_data_dict["os_version"] = os_version_bit
            new_update_data_dict["os_id"] = os_id
            new_update_data_dict["virtualization_type"] = virtualization_type
            new_update_data_dict["ansible_system_vendor"] = ansible_system_vendor
            new_update_data_dict["ansible_product_name"] = ansible_product_name
            new_update_data_dict["ansible_product_serial"] = ansible_product_serial
            new_update_data_dict["ansible_hostname"] = ansible_hostname
            new_update_data_dict["ansible_all_ipv4_addresses"] = ansible_all_ipv4_addresses
            new_update_data_dict["ansible_all_ipv6_addresses"] = ansible_all_ipv6_addresses
            device_data_from_es = list(get_all_device_data_from_cmdb_es(serial_number=ansible_product_serial, es_index="devices"))
            
            # 将硬件数据存到redis
            if device_data_from_es:
                device_data_from_es_item = device_data_from_es[0]["_source"]
                if device_data_from_es_item:
                    new_update_data_dict["device_id"] = device_data_from_es_item["id"]
                    redis.set("zeus_cmdb_device_info:%s"%(device_data_from_es_item["id"]), json.dumps(new_update_data_dict))
                else:
                    # 如果设备序列号无法在es中查到，说明cmdb没有录入该设备，需要提示设备管理员
                    pass
    else:
        new_update_data_dict = ansible_hardware_data
    return new_update_data_dict
