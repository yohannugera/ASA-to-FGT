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
def get_all_addrgrp():
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
def get_all_servicegrp():
    print("Not Coded Yet")

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
        
        mapped = False
        for index_fmg in df_addr_fmg.index:
            if df_addr_fmg['subnet'][index_fmg] == subnet_pair:
                print(addr_file['name'][index_new]," in ASA is present in FMG as ",df_addr_fmg['name'][index_fmg])
                mapped = True
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
