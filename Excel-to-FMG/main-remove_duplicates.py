import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import re
import pandas as pd
import ipaddress

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

USERNAME = ''
PASSWORD = ''
IP = ''
SESSION = ''
ADOM = ''
REGION = ''
PACKAGE_NAME = ''
DEVICE = ''
    
def login():
    payload = json.dumps({
        "session": 1,
        "id": 1,
        "method": "exec",
        "params": [{
            "url": "sys/login/user",
            "data": [{
                "user": USERNAME,
                "passwd": PASSWORD}
            ]
        }]
    })
    headers = {
        'Content-Type':'application/json'
    }
    
    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def logout():
    payload = json.dumps({
        "session": SESSION,
        "id": 1,
        "method": "exec",
        "params": [{
            "url": "sys/logout"
        }]
    })
    headers = {
        'Content-Type':'application/json'
    }
    
    return requests.request("POST", URL, headers=headers, data=payload, verify=False)

def get_address(address):
    payload = json.dumps({
      "method": "get",
      "params": [
        {
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/address/"+address
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def add_address(name,subnet,comment):
    payload = json.dumps({
      "method": "add",
      "params": [
        {
          "data": [
            {
                "name": name,
                "subnet": subnet,
                "comment": comment
            }
          ],
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/address"
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def add_address_range(name,start_ip,end_ip,comment):
    payload = json.dumps({
      "method": "add",
      "params": [
        {
          "data": [
            {
                "name": name,
                "type": "iprange",
                "start-ip": start_ip,
                "end-ip": end_ip,
                "comment": comment
            }
          ],
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/address"
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def map_address(name,subnet,comment):
    print("Not Coded Yet")
def get_all_address():
    payload = json.dumps({
      "method": "get",
      "params": [
        {
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/address"
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)

def create_address(addr_file):
    unconfigured_counter = 0
    for x in addr_file.to_dict(orient='records'):
        address_name = x['name']
        address_subnet = x['subnet']
        address_comment = x['comment'] if isinstance(x['comment'],str) else ''
        
        pre_check = json.loads(get_address(address_name).text)
        
        if pre_check['result'][0]['status']['code'] == -3:
            print("Configuring Address Object:",address_name)
            resp = add_address(address_name,address_subnet,address_comment)
            print(resp.text)
        elif pre_check['result'][0]['status']['code'] == 0:
            if ipaddress.ip_network(x['subnet']) == ipaddress.ip_network(pre_check['result'][0]['data']['subnet'][0]+"/"+pre_check['result'][0]['data']['subnet'][1]):
                print("Address",address_name,"is already configured with correct value")
                pass
            else:
                print("Address",address_name,"is already configured but with a different value")
                unconfigured_counter = unconfigured_counter+1
        else:
            print("Unconfigured Address Object:",address_name)
            unconfigured_counter = unconfigured_counter+1
            
    print("Script didn't configure",unconfigured_counter,"entries out of",len(addr_file))
    input("Press enter to continue...")
def create_addrrng(addrrng_file):
    unconfigured_counter = 0
    for x in addrrng_file.to_dict(orient='records'):
        address_name = x['name']
        address_startip = x['start-ip']
        address_endip = x['end-ip']
        address_comment = x['comment'] if isinstance(x['comment'],str) else ''
        
        pre_check = json.loads(get_address(address_name).text)
        print(pre_check)
        
        if pre_check['result'][0]['status']['code'] == -3:
            print("Configuring Address Object:",address_name)
            resp = add_address_range(address_name,address_startip,address_endip,address_comment)
            print(resp.text)
        elif pre_check['result'][0]['status']['code'] == 0:
            print(pre_check['result'][0]['data']['start-ip'],pre_check['result'][0]['data']['end-ip'])
        else:
            print("Unconfigured Address Object:",address_name)
            unconfigured_counter = unconfigured_counter+1
            
    print("Script didn't configure",unconfigured_counter,"entries out of",len(addrrng_file))
    input("Press enter to continue...")

def get_addrgrp(addrgrp):
    payload = json.dumps({
      "method": "get",
      "params": [
        {
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/addrgrp/"+addrgrp
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def add_addrgrp(name,member,comment):
    payload = json.dumps({
      "method": "add",
      "params": [
        {
          "data": [
            {
                "name": name,
                "member": member,
                "comment": comment
            }
          ],
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/addrgrp"
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False) 
def map_addrgrp(name,member,comment):
    print("Not Coded Yet")

def create_addrgrp(addrgrp_file):
    unconfigured_counter = 0
    for x in addrgrp_file.to_dict(orient='records'):
        addrgrp_name = x['name'].replace('/','\\/')
        addrgrp_members = x['members']
        addrgrp_comment = x['comment'] if isinstance(x['comment'],str) else ''
        
        pre_check = json.loads(get_addrgrp(addrgrp_name).text)
        
        if pre_check['result'][0]['status']['code'] == -3:
            print("Configuring AddrGrp Object:",addrgrp_name)
            resp = add_addrgrp(addrgrp_name,eval(addrgrp_members),addrgrp_comment)
            print(resp.text)
        elif pre_check['result'][0]['status']['code'] == 0:
            pre_check_members = sorted(pre_check['result'][0]['data']['member'])
            addrgrp_members = sorted(eval(addrgrp_members))
            if addrgrp_members == pre_check_members:
                print("Address group",addrgrp_name,"is already configured with correct members")
                pass
            else:
                print("Address group",address_name,"is already configured but with a different members")
                unconfigured_counter = unconfigured_counter+1
        else:
            print("Unconfigured Address Group Object:",address_name)
            unconfigured_counter = unconfigured_counter+1

    print("Script didn't configure",unconfigured_counter,"entries out of",len(addrgrp_file))
    input("Press enter to continue...")

def get_all_services():
    payload = json.dumps({
      "method": "get",
      "params": [
        {
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/service/custom"
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def get_service(service):
    payload = json.dumps({
      "method": "get",
      "params": [
        {
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/service/custom/"+service
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def add_service(name,service_type,port,comment):
    if service_type=="tcp":
        payload = json.dumps({
          "method": "add",
          "params": [
            {
              "data": [
                {
                    "name": name,
                    "protocol":"TCP/UDP/SCTP",
                    "tcp-portrange": port,
                    "comment": comment
                }
              ],
              "url": "/pm/config/adom/"+ADOM+"/obj/firewall/service/custom"
            }
          ],
          "session": SESSION,
          "id": 1
        })
    elif service_type=="udp":
        payload = json.dumps({
          "method": "add",
          "params": [
            {
              "data": [
                {
                    "name": name,
                    "protocol":"TCP/UDP/SCTP",
                    "udp-portrange": port,
                    "comment": comment
                }
              ],
              "url": "/pm/config/adom/"+ADOM+"/obj/firewall/service/custom"
            }
          ],
          "session": SESSION,
          "id": 1
        })
    elif service_type=="tcp-udp":
        payload = json.dumps({
          "method": "add",
          "params": [
            {
              "data": [
                {
                    "name": name,
                    "protocol":"TCP/UDP/SCTP",
                    "tcp-portrange": port,
                    "udp-portrange": port,
                    "comment": comment
                }
              ],
              "url": "/pm/config/adom/"+ADOM+"/obj/firewall/service/custom"
            }
          ],
          "session": SESSION,
          "id": 1
        })
    else:
        print("Service",name,"not configured.")
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def map_service(name,service_type,port,comment):
    print("Not Coded Yet")

def create_service(srvs_file):
    unconfigured_counter = 0
    for x in srvs_file.to_dict(orient='records'):
        service_name = x['name']
        service_type = x['type']
        service_value = str(x['value'])
        service_comment = x['comment'] if isinstance(x['comment'],str) else ''
        
        pre_check = json.loads(get_service(service_name).text)
        
        if pre_check['result'][0]['status']['code'] == -3:
            print("Configuring Service Object:",service_name)
            resp = add_service(service_name,service_type,service_value,service_comment)
            print(resp.text)
        elif pre_check['result'][0]['status']['code'] == 0:
            if service_type == "tcp":
                if service_value in pre_check['result'][0]['data']['tcp-portrange']:
                    print("Service",service_name,"is already configured with correct value")
                else:
                    unconfigured_counter = unconfigured_counter+1
                    print("Service",service_name,"is already configured but with a different value")
            elif service_type == "udp":
                if service_value in pre_check['result'][0]['data']['udp-portrange']:
                    print("Service",service_name,"is already configured with correct value")
                else:
                    unconfigured_counter = unconfigured_counter+1
                    print("Service",service_name,"is already configured but with a different value")
            elif service_type == "tcp-udp":
                if (service_value in pre_check['result'][0]['data']['tcp-portrange']) and (service_value in pre_check['result'][0]['data']['udp-portrange']):
                    print("Service",service_name,"is already configured with correct value")
                else:
                    unconfigured_counter = unconfigured_counter+1
                    print("Service",service_name,"is already configured but with a different value")
            else:
                unconfigured_counter = unconfigured_counter+1
                print("Unknown Error in",service_name)
        else:
            print("Unconfigured Address Object:",address_name)
            unconfigured_counter = unconfigured_counter+1
            
    print("Script didn't configure",unconfigured_counter,"entries out of",len(srvs_file))
    input("Press enter to continue...")

def get_all_servicegrps():
    print("Not Coded Yet")
def get_servicegrp(servicegrp):
    payload = json.dumps({
      "method": "get",
      "params": [
        {
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/service/group/"+servicegrp
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def add_servicegrp(name,member,comment):
    payload = json.dumps({
      "method": "add",
      "params": [
        {
          "data": [
            {
                "name": name,
                "member": member,
                "comment": comment
            }
          ],
          "url": "/pm/config/adom/"+ADOM+"/obj/firewall/service/group"
        }
      ],
      "session": SESSION,
      "id": 1
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def map_servicegrp(name,member,comment):
    print("Not Coded Yet")

def create_servicegrp(srvgrps_file):
    unconfigured_counter = 0
    for x in srvgrps_file.to_dict(orient='records'):
        servicegrp_name = x['name']
        servicegrp_member = eval(x['members'])
        servicegrp_comment = x['comment'] if isinstance(x['comment'],str) else ''
        
        pre_check = json.loads(get_servicegrp(servicegrp_name).text)
        
        if pre_check['result'][0]['status']['code'] == -3:
            print("Configuring Service Object:",servicegrp_name)
            resp = add_servicegrp(servicegrp_name,servicegrp_member,servicegrp_comment)
            print(resp.text)
        elif pre_check['result'][0]['status']['code'] == 0:
            if servicegrp_member in pre_check['result'][0]['data']['member']:
                print("Members",servicegrp_member,"is already in",pre_check['result'][0]['data']['name'])
            else:
                unconfigured_counter = unconfigured_counter+1
                print("Service Group is already configured but with a different members")
        else:
            print("Unconfigured Address Object:",address_name)
            unconfigured_counter = unconfigured_counter+1
            
    print("Script didn't configure",unconfigured_counter,"entries out of",len(srvgrps_file))
    input("Press enter to continue...")

def create_policypackage():
    payload = json.dumps({
      "session": SESSION,
      "id": 1,
      "method": "add",
      "params": [
        {
          "data": [
            {
              "name": PACKAGE_NAME,
              "package settings": {
                "central-nat": 0,
                "consolidated-firewall-mode": 0,
                "fwpolicy-implicit-log": 0,
                "fwpolicy6-implicit-log": 0,
                "hitc-taskid": 0,
                "hitc-timestamp": 0,
                "ngfw-mode": 0,
                "policy-offload-level": 0
              },
              "type": "pkg"
            }
          ],
          "url": "/pm/pkg/adom/"+ADOM+"/"+REGION+"/"
        }
      ]
    })
    headers = {
      'Content-Type': 'application/json'
    }

    return requests.request("POST", URL, headers=headers, data=payload, verify=False)
def create_policy(name,srcintf,dstintf,srcaddr,dstaddr,service,action,log,comment):
    payload = json.dumps({
      "params": [
        {
          "url": "/pm/config/adom/"+ADOM+"/pkg/"+REGION+"/"+PACKAGE_NAME+"/firewall/policy",
          "data": [
            {
              "name": name,
              "srcintf": srcintf,
              "dstintf": dstintf,
              "srcaddr": srcaddr,
              "dstaddr": dstaddr,
              "service": service,
              "logtraffic": log,
              "action": action,
              "schedule": "always",
              "status": "enable",
              "comments": comment,
            }
          ]
        }
      ],
      "method": "add",
      "id": 1,
      "session": SESSION
    })
    headers = {
      'Content-Type': 'application/json'
    }
    return requests.request("POST", URL, headers=headers, data=payload, verify=False)

def create_policies(acl_file):
    counter = 1
    for x in acl_file.to_dict(orient='records'):
        name = "Policy-"+str(counter)
        srcaddr = eval(x['srcaddr'])
        dstaddr = eval(x['dstaddr'])
        service = eval(x['service'])
        srcintf = eval(x['srcintf'])
        dstintf = eval(x['dstintf'])
        action = x['action']
        log = x['log']
        comment = x['comment'] if isinstance(x['comment'],str) else ''
        
        print("Configuring policy",counter)
        counter = counter+1
        resp = create_policy(name,srcintf,dstintf,srcaddr,dstaddr,service,action,log,comment)
        print(resp.text)
        
    input("Press enter to continue...")

def main():
    env_data = {}

    # Read environmental settings from a file...
    with open('environment.cfg','r') as env:
        env_data = json.load(env)

    try:
        global IP, USERNAME, PASSWORD, ADOM, REGION, PACKAGE_NAME, URL, DEVICE
        
        IP = env_data['ip']
        USERNAME = env_data['username']
        PASSWORD = env_data['password']
        ADOM = env_data['adom']
        REGION = env_data['region']
        PACKAGE_NAME = env_data['package_name']
        URL = 'https://'+IP+'/jsonrpc'
        DEVICE = env_data['device']
        CONFIG_FILE = env_data['config_file']
        
    except:
        print("Environment Settings read error occured. Please check and run again...")

    # Login to the FortiManager and get the session
    global SESSION
    SESSION = json.loads(login().text)['session']
    
    ## Reading Excel Configuration
    config_file = pd.ExcelFile(CONFIG_FILE)
    
    # Read Addresses from Excel
    addr_file = pd.read_excel(config_file,'Addresses')
    
    # Read IP ranges from Excel
    addrrng_file = pd.read_excel(config_file,'Addrrngs')
    
    # Read Address Groups from Excel
    addrgrp_file = pd.read_excel(config_file,'AddrGrps')
    
    # Read Services from Excel
    srvs_file = pd.read_excel(config_file,'Services')
    
	# Read Services from Excel
    srvgrps_file = pd.read_excel(config_file,'ServiceGrps')
    
    # Check Address Objects
    addr_fmg = get_all_address().json()["result"][0]["data"]
    df_addr_fmg = pd.DataFrame.from_dict(addr_fmg, orient='columns')
    
    counter = 0
    for index_new in addr_file.index:
        tmp_subnet = addr_file['subnet'][index_new]
        tmp_subnet_pair = tmp_subnet.split('/')
        subnet_pair = [tmp_subnet_pair[0], str(ipaddress.ip_network(tmp_subnet).netmask)]
        
        for index_fmg in df_addr_fmg.index:
            if df_addr_fmg['subnet'][index_fmg] == subnet_pair:
                print(addr_file['name'][index_new]," in ASA is present in FMG as ",df_addr_fmg['name'][index_fmg])
                counter = counter + 1
                break
            else:
                pass
                
    print(counter)
    print(len(addr_file))
    
    # Check Address Ranges
    counter = 0
    for index_new in addrrng_file.index:
        tmp_startip = addrrng_file['start-ip'][index_new]
        tmp_endip = addrrng_file['end-ip'][index_new]
        
        for index_fmg in df_addr_fmg.index:
            if df_addr_fmg['subnet'][index_fmg] == subnet_pair:
                print(addr_file['name'][index_new]," in ASA is present in FMG as ",df_addr_fmg['name'][index_fmg])
                counter = counter + 1
                break
            else:
                pass
                
    print(counter)
    print(len(addr_file))
   
    # logout
    logout()

if __name__=="__main__":
    main()
