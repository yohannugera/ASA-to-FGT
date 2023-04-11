import re
from ipaddress import *
import pandas as pd
import typer

indentation_length = ' '

# https://www.cisco.com/c/en/us/td/docs/security/asa/asa98/configuration/general/asa-98-general-config/ref-ports.html
default_protocols = {
    'ah':'51',
    'eigrp':'88',
    'esp':'50',
    'gre':'47',
    'icmp':'1',
    'icmp6':'58',
    'igmp':'2',
    'igrp':'9',
    'ip':'0',
    'ipinip':'4',
    'ipsec':'50',
    'nos':'94',
    'ospf':'89',
    'pcp':'108',
    'pim':'103',
    'pptp':'47',
    'snp':'109',
    'tcp':'6',
    'udp':'17'}
default_ports = {
    'aol':['tcp','5190'],
    'bgp':['tcp','179'],
    'biff':['udp','512'],
    'bootpc':['udp','68'],
    'bootps':['udp','67'],
    'chargen':['tcp','19'],
    'cifs':['tcp-udp','3020'],
    'citrix-ica':['tcp','1494'],
    'cmd':['tcp','514'],
    'ctiqbe':['tcp','2748'],
    'daytime':['tcp','13'],
    'discard':['tcp-udp','9'],
    'dnsix':['udp','195'],
    'domain':['tcp-udp','53'],
    'echo':['tcp-udp','7'],
    'exec':['tcp','512'],
    'finger':['tcp','79'],
    'ftp':['tcp','21'],
    'ftp-data':['tcp','20'],
    'gopher':['tcp','70'],
    'h323':['tcp','1720'],
    'hostname':['tcp','101'],
    'http':['tcp-udp','80'],
    'https':['tcp','443'],
    'ident':['tcp','113'],
    'imap4':['tcp','143'],
    'irc':['tcp','194'],
    'isakmp':['udp','500'],
    'kerberos':['tcp-udp','750'],
    'klogin':['tcp','543'],
    'kshell':['tcp','544'],
    'ldap':['tcp','389'],
    'ldaps':['tcp','636'],
    'login':['tcp','513'],
    'lotusnotes':['tcp','1352'],
    'lpd':['tcp','515'],
    'mobile-ip':['udp','434'],
    'nameserver':['udp','42'],
    'netbios-dgm':['udp','138'],
    'netbios-ns':['udp','137'],
    'netbios-ssn':['tcp','139'],
    'nfs':['tcp-udp','2049'],
    'nntp':['tcp','119'],
    'ntp':['udp','123'],
    'pcanywhere-data':['tcp','5631'],
    'pcanywhere-status':['udp','5632'],
    'pim-auto-rp':['tcp-udp','496'],
    'pop2':['tcp','109'],
    'pop3':['tcp','110'],
    'pptp':['tcp','1723'],
    'radius':['udp','1645'],
    'radius-acct':['udp','1646'],
    'rip':['udp','520'],
    'rsh':['tcp','514'],
    'rtsp':['tcp','554'],
    'secureid-udp':['udp','5510'],
    'sip':['tcp-udp','5060'],
    'smtp':['tcp','25'],
    'snmp':['udp','161'],
    'snmptrap':['udp','162'],
    'sqlnet':['tcp','1521'],
    'ssh':['tcp','22'],
    'sunrpc':['tcp-udp','111'],
    'syslog':['udp','514'],
    'tacacs':['tcp, udp','49'],
    'talk':['tcp-udp','517'],
    'telnet':['tcp','23'],
    'tftp':['udp','69'],
    'time':['udp','37'],
    'uucp':['tcp','540'],
    'vxlan':['udp','4789'],
    'who':['udp','513'],
    'whois':['tcp','43'],
    'www':['tcp-udp','80'],
    'xdmcp':['udp','177']}

def tab_level(line):
    return(len(line)-len(line.lstrip(indentation_length)))
def indent_level(lines):
    line_levels = []

    for line in lines:
        temp = {}
        temp['line'] = line[:-1].lstrip()
        temp['level'] = tab_level(line)
        line_levels.append(temp)

    return line_levels
def dict_insert_or_append(adict,key,val):
    if key in adict:
        if type(adict[key]) != list:
            adict[key] = [adict[key]]
        adict[key].append(val)
    else:
        adict[key] = val
def ttree_to_json(ttree,level=0):
    result = {}
    for i in range(0,len(ttree)):
        cn = ttree[i]
        try:
            nn  = ttree[i+1]
        except:
            nn = {'level':-1}

        # Edge cases
        if cn['level']>level:
            continue
        if cn['level']<level:
            return result

        # Recursion
        if nn['level']==level:
            dict_insert_or_append(result,cn['line'],0)
        elif nn['level']>level:
            rr = ttree_to_json(ttree[i+1:], level=nn['level'])
            dict_insert_or_append(result,cn['line'],rr)
        else:
            dict_insert_or_append(result,cn['line'],0)
            return result
    return result
def parse_asa_config(config_tree):
    # Set up lists and dictionaries for return purposes
    interfaces = []
    routes = []
    names = []
    addresses = []
    addrgrps = []
    services = []
    servicegrps = []
    acls = []
    
    misc_settings = []
    unparsed_tree = config_tree.copy()
    acl_remark = ''     # This is because ACLs are coming with remarks
    acl_map = {}
    
    # Populate services with ASA default values
    for entry in default_ports.keys():
        services.append({'name':entry,'type':default_ports[entry][0],
            'value':default_ports[entry][1],
            'direction':'destination',
            'comment':'Created by Parser: ASA Default Ports'})
    # Populate protocols with ASA default values
    for entry in default_protocols.keys():
        services.append({'name':entry,'type':'protocol',
            'value':default_protocols[entry],
            'direction':'',
            'comment':'Created by Parser: ASA Default Ports'})  
    
    # Read each line of the config, looking for configuration components that we care about
    for line in config_tree.keys():
        # Identify all the interfaces
        if re.match("^interface .*",line):
            tmp_out = {}
            tmp_out['status'] = ''
            tmp_out['interface'] = line.split(' ')[1]
            tmp_out['alias'] = ''
            tmp_out['comment'] = ''
            tmp_out['ip'] = ''
            tmp_out['vlan'] = ''
            tmp_out['member-interface'] = ''
            for x in config_tree[line].keys():
                try:
                    tmp_split = x.split(' ')
                    if tmp_split[0] == 'shutdown':
                        tmp_out['status'] = 'disable'
                    elif tmp_split[0] == 'nameif':
                        tmp_out['alias'] = tmp_split[1]
                    elif tmp_split[0] == 'description':
                        tmp_out['comment'] = ' '.join(tmp_split[1:])
                    elif tmp_split[0] == 'ip':
                        tmp_out['ip'] = tmp_split[2]+"/"+str(IPv4Network('0.0.0.0/'+tmp_split[3]).prefixlen)
                        routes.append({'dst':str(ip_interface(tmp_out['ip']).network),'device':tmp_out['interface'],'gateway':'0.0.0.0'})
                    elif tmp_split[0] == 'vlan':
                        tmp_out['vlan'] = tmp_split[1]
                    elif tmp_split[0] == 'member-interface':
                        tmp_out['member-interface'] = tmp_out['member-interface']+','+tmp_split[1]
                    elif tmp_split[0] == 'no':
                        pass
                    elif tmp_split[0] == 'security-level':
                        pass
                    elif tmp_split[0] == 'management-only':
                        pass
                    else:
                        raise ValueError
                except:
                    print("Error in parsing line (Interfaces): ", line.split(' ')[1], x)
                    a = input('Error occured. Please enter to continue...')
            interfaces.append(tmp_out)
            unparsed_tree.pop(line)
        if re.match("^access-group .*",line):
            tmp_split = line.split(' ')
            acl_map[tmp_split[1]] = tmp_split[4]
            unparsed_tree.pop(line)
        # Identify all the routes
        if re.match("^route .*",line):
            x = line.split(' ')
            routes.append({'dst':ip_interface(x[2]+'/'+x[3]).network,'gateway':x[4],'device':x[1]})
            unparsed_tree.pop(line)
        # Identify all staticallly configured name/IPAddress translations
        if re.match("^name (([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]).*", line):
            tmp = line.split(' ')
            tmp_out = {}
            tmp_out['name'] = tmp[2]
            tmp_out['value'] = tmp[1]
            names.append(tmp_out)
            unparsed_tree.pop(line)
        # Identify and collect configurations for all configured objects
        if re.match("^object network.*",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[-1]
                tmp_out['subnet'] = ''
                tmp_out['comment'] = ''
                for x in config_tree[line].keys():
                    if re.match("^host.*",x):
                        tmp_out['subnet'] = x.split(' ')[-1]+'/32'
                    elif re.match("^description.*",x):
                        tmp_out['comment'] = x[12:]
                    elif re.match("^subnet",x):
                        tmp_line = x.split(' ')
                        tmp_out['subnet'] = tmp_line[1]+'/'+str(IPv4Network('0.0.0.0/' + tmp_line[2]).prefixlen)
                    else:
                        raise ValueError

                addresses.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Addresses): ",line)
                a = input('Error occured. Please enter to continue...')
        # Identify and collect configurations for all configured object groups
        if re.match("^object-group network.*",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[-1]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                for x in config_tree[line].keys():
                    if re.match("^network-object host .*", x):
                        tmp = x.split(' ')[-1]
                        addresses.append({
                            'name':'h-'+tmp,
                            'subnet':tmp+'/32'})
                        tmp_out['members'].append('h-'+tmp)
                    elif re.match("^network-object object.*",x):
                        tmp = x.split(' ')[-1]
                        tmp_out['members'].append(tmp)
                    elif re.match("^network-object.*",x):
                        tmp = x.split(' ')
                        addresses.append({
                            'name':"net-"+tmp[-2]+"n"+str(IPv4Network('0.0.0.0/'+tmp[-1]).prefixlen),
                            'subnet':tmp[-2] + "/" + str(IPv4Network('0.0.0.0/'+tmp[-1]).prefixlen)})
                        tmp_out['members'].append("net-"+tmp[-2]+"n"+str(IPv4Network('0.0.0.0/'+tmp[-1]).prefixlen))
                    elif re.match("^group-object.*",x):
                        tmp_out['members'].append(x.split(' ')[-1])
                    elif re.match("^description.*", x):
                        tmp_out['comment'] = x[12:]
                    else:
                        raise ValueError

                addrgrps.append(tmp_out)
                unparsed_tree.pop(line)

            except:
                print("Error in parsing line (Object Groups): ", line)
                a = input('Error occured. Please enter to continue...')
        # Identify and collect configurations for all configured services
        if re.match("^object service.*",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[-1]
                tmp_out['type'] = ''
                tmp_out['value'] = ''
                tmp_out['direction'] = ''
                tmp_out['comment'] = ''
                for x in config_tree[line].keys():
                    if re.match("^service.*",x):
                        tmp_out['type'] = x.split(' ')[1]
                        tmp_out['direction'] = x.split(' ')[2]
                        if x.split(' ')[3] == "eq":
                            tmp = x.split(' ')[4]
                            if tmp in default_ports.keys():
                                tmp_out['value'] = default_ports[tmp][1]
                            else:
                                tmp_out['value'] = tmp
                        elif x.split(' ')[3] == "range":
                            tmp_out['value'] = x.split(' ')[4]+'-'+x.split(' ')[5]
                        else:
                            raise ValueError
                    elif re.match("^description.*",x):
                        tmp_out['comment'] = x[12:]
                    else:
                        raise ValueError

                services.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Services): ",line)
                a = input('Error occured. Please enter to continue...')
        # Identify and collect configurations for all configured service groups
        if re.match("^object-group service.* tcp$",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[2]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                tmp_out_type = line.split(' ')[3]
                for x in config_tree[line].keys():
                    if re.match("^port-object.*", x):
                        tmp = x.split(' ')
                        if tmp[1] == "eq":
                            if tmp[2] in default_ports.keys():
                                tmp_out['members'].append(tmp[2])
                            else:
                                tmp_out['members'].append(tmp_out_type+'-'+x.split(' ')[2])
                                services.append({'name':tmp_out_type+'-'+x.split(" ")[2],
                                                'type':tmp_out_type,
                                                'value':x.split(" ")[2],
                                                'direction':'destination',
                                                'comment':''})
                        elif x.split(' ')[1] == "range":
                            tmp_out['members'].append(tmp_out_type+'-'+x.split(' ')[2]+'-'+x.split(' ')[3])
                            services.append({'name': tmp_out_type+'-'+x.split(' ')[2]+'-'+x.split(' ')[3],
                                             'type': tmp_out_type,
                                             'value': x.split(' ')[2]+'-'+x.split(' ')[3],
                                             'direction': 'destination',
                                             'comment': ''})
                        else:
                            raise ValueError
                    elif re.match("^group-object.*", x):
                        tmp_out['members'].append(x.split(' ')[1])
                    elif re.match("^description.*", x):
                        tmp_out['comment'] = x[12:]
                    else:
                        raise ValueError

                servicegrps.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Service Groups / TCP): ", line)
                a = input('Error occured. Please enter to continue...')
        elif re.match("^object-group service.* udp$",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[2]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                tmp_out_type = line.split(' ')[3]
                for x in config_tree[line].keys():
                    if re.match("^port-object.*", x):
                        tmp = x.split(' ')
                        if tmp[1] == "eq":
                            if tmp[2] in default_ports.keys():
                                tmp_out['members'].append(tmp[2])
                            else:
                                tmp_out['members'].append(tmp_out_type+'-'+x.split(' ')[2])
                                services.append({'name':tmp_out_type+'-'+x.split(" ")[2],
                                                'type':tmp_out_type,
                                                'value':x.split(" ")[2],
                                                'direction':'destination',
                                                'comment':''})
                        elif x.split(' ')[1] == "range":
                            tmp_out['members'].append(tmp_out_type+'-'+x.split(' ')[2]+'-'+x.split(' ')[3])
                            services.append({'name': tmp_out_type+'-'+x.split(' ')[2]+'-'+x.split(' ')[3],
                                             'type': tmp_out_type,
                                             'value': x.split(' ')[2]+'-'+x.split(' ')[3],
                                             'direction': 'destination',
                                             'comment': ''})
                        else:
                            raise ValueError
                    elif re.match("^group-object.*", x):
                        tmp_out['members'].append(x.split(' ')[1])
                    elif re.match("^description.*", x):
                        tmp_out['comment'] = x[12:]
                    else:
                        raise ValueError

                servicegrps.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Service Groups / UDP): ", line)
                a = input('Error occured. Please enter to continue...')
        elif re.match("^object-group service.* tcp-udp$",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[2]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                tmp_out_type = line.split(' ')[3]
                for x in config_tree[line].keys():
                    if re.match("^port-object.*", x):
                        tmp = x.split(' ')
                        if tmp[1] == "eq":
                            if tmp[2] in default_ports.keys():
                                tmp_out['members'].append(tmp[2])
                            else:
                                tmp_out['members'].append(tmp_out_type+'-'+x.split(' ')[2])
                                services.append({'name':tmp_out_type+'-'+x.split(" ")[2],
                                                'type':tmp_out_type,
                                                'value':x.split(" ")[2],
                                                'direction':'destination',
                                                'comment':''})
                        elif x.split(' ')[1] == "range":
                            tmp_out['members'].append(tmp_out_type+'-'+x.split(' ')[2]+'-'+x.split(' ')[3])
                            services.append({'name': tmp_out_type+'-'+x.split(' ')[2]+'-'+x.split(' ')[3],
                                             'type': tmp_out_type,
                                             'value': x.split(' ')[2]+'-'+x.split(' ')[3],
                                             'direction': 'destination',
                                             'comment': ''})
                        else:
                            raise ValueError
                    elif re.match("^group-object.*", x):
                        tmp_out['members'].append(x.split(' ')[1])
                    elif re.match("^description.*", x):
                        tmp_out['comment'] = x[12:]
                    else:
                        raise ValueError

                servicegrps.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Service Groups / TCP-UDP): ", line)
                a = input('Error occured. Please enter to continue...')
        elif re.match("^object-group service.*",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[2]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                tmp_out_type = ''
                for x in config_tree[line].keys():
                    if re.match("^service-object.*", x):
                        tmp_split = x.rstrip().split(' ')
                        if tmp_split[-2] == "eq":
                            if tmp_split[-1] in default_ports.keys():
                                tmp_out['members'].append(tmp_split[-1])
                            else:
                                tmp_out['members'].append(tmp_split[1]+'-'+tmp_split[-1])
                                services.append({
                                    'name':tmp_split[1]+'-'+tmp_split[-1],
                                    'type':tmp_split[1],
                                    'value':tmp_split[-1],
                                    'direction':'destination',
                                    'comment':''
                                    })
                        elif tmp_split[-2] == "range":
                            raise ValueError
                        elif tmp_split[1] == "object":
                            tmp_out['members'].append(tmp_split[-1])
                        else:
                            tmp_out['members'] = tmp_out['members'] + tmp_split[1:]
                    elif re.match("^group-object.*", x):
                        tmp_out['members'].append(x.split(' ')[1])
                    elif re.match("^description.*", x):
                        tmp_out['comment'] = x[12:]
                    else:
                        raise ValueError

                servicegrps.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Service Groups / Mixed): ", line)
                a = input('Error occured. Please enter to continue...')
        if re.match("^object-group protocol.*",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[-1]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                for x in config_tree[line].keys():
                    if re.match("^protocol-object.*", x):
                        tmp_out['members'].append(x.split(' ')[-1])
                    if re.match("^description.*", x):
                        tmp_out['description'] = x[12:]
                    
                servicegrps.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Service Groups / Protocols): ", line)
                a = input('Error occured. Please enter to continue...')
        # Identify and collect configurations for all configured access lists
        if re.match("^access-list .*", line):
            try:
                tmp_split = line.split(' ')
                tmp_out = {}
                tmp_out['direction'] = tmp_split[1]
                tmp_out['action'] = ''
                tmp_out['service'] = ''
                tmp_out['source'] = ''
                tmp_out['destination'] = ''
                tmp_out['log'] = ''
                
                while len(tmp_split) > 0:
                    while '' in tmp_split:
                        tmp_split.pop(tmp_split.index(''))
                    if tmp_split.pop(0) != 'access-list':
                        raise ValueError
                    else:
                        pass
                    tmp_out['direction'] = tmp_split.pop(0)
                    line_type = tmp_split.pop(0)
                    if line_type == 'remark':
                        acl_remark = acl_remark+' '.join(tmp_split)
                        tmp_split = []
                    elif line_type == 'extended':
                        tmp_out['action'] = tmp_split.pop(0)
                        if 'log' in tmp_split:
                            tmp_out['log'] = 'all'
                            tmp_pop = tmp_split.pop(tmp_split.index('log'))
                        else:
                            pass
                        srvs_verdict = tmp_split.pop(0)
                        if srvs_verdict == 'tcp' or srvs_verdict == 'udp':
                            if 'eq' in tmp_split:
                                tmp_index = tmp_split.index('eq')
                                srvsport = tmp_split[tmp_index+1]
                                if srvsport in default_ports.keys():
                                    tmp_out['service'] = srvsport
                                else:
                                    tmp_out['service'] = srvs_verdict+'-'+srvsport
                                    services.append({'name':tmp_out['service'],
                                                    'type':srvs_verdict,
                                                    'value':srvsport,
                                                    'direction':'destination',
                                                    'comment':'Created by parser'})
                                tmp_pop = tmp_split.pop(tmp_index)
                                tmp_pop = tmp_split.pop(tmp_index)
                                
                            elif 'range' in tmp_split:
                                tmp_index = tmp_split.index('range')
                                srvsport = tmp_split[tmp_index+1]+'-'+tmp_split[tmp_index+2]
                                tmp_out['service'] = srvs_verdict+'-'+srvsport
                                tmp_pop = tmp_split.pop(tmp_index)
                                tmp_pop = tmp_split.pop(tmp_index)
                                tmp_pop = tmp_split.pop(tmp_index)
                                services.append({'name':tmp_out['service'],
                                                'type':srvs_verdict,
                                                'value':srvsport,
                                                'direction':'destination',
                                                'comment':'Created by parser'})
                            else:
                                raise ValueError
                        elif srvs_verdict == 'ip':
                            tmp_out['service'] = "ALL"
                        elif srvs_verdict == 'object' or srvs_verdict == 'object-group':
                            tmp_out['service'] = tmp_split.pop(0)
                        elif srvs_verdict in default_ports.keys() or srvs_verdict in default_protocols.keys():
                            tmp_out['service'] = srvs_verdict
                        else:
                            raise ValueError
                            
                        src_verdict = tmp_split.pop(0)
                        if src_verdict == 'object' or src_verdict == 'object-group':
                            tmp_out['source'] = tmp_split.pop(0)
                        elif src_verdict == 'any' or src_verdict == 'any4':
                            tmp_out['source'] = 'all'
                        elif src_verdict == 'host':
                            tmp_pop = tmp_split.pop(0)
                            tmp_out['source'] = 'host-'+tmp_pop
                            addresses.append({
                                    'name': tmp_out['source'],
                                    'subnet': tmp_pop+'/32',
                                    'comment': 'Created by parser'
                                    })
                        elif src_verdict == 'network':
                            tmp_network = tmp_split.pop(0)
                            tmp_subnet = str(IPv4Network('0.0.0.0/' + tmp_split.pop(0)).prefixlen)
                            tmp_out['source'] = 'n-'+tmp_network+'n'+tmp_subnet
                            addresses.append({
                                    'name': tmp_out['source'],
                                    'subnet': tmp_network+'/'+tmp_subnet,
                                    'comment': 'Created by parser'
                                    })
                        else:
                            raise ValueError
                            
                        dst_verdict = tmp_split.pop(0)
                        if dst_verdict == 'object' or dst_verdict == 'object-group':
                            tmp_out['destination'] = tmp_split.pop(0)
                        elif dst_verdict == 'any' or dst_verdict == 'any4':
                            tmp_out['destination'] = 'all'
                        elif dst_verdict == 'host':
                            tmp_pop = tmp_split.pop(0)
                            tmp_out['destination'] = 'host-'+tmp_pop
                            addresses.append({
                                    'name': tmp_out['destination'],
                                    'subnet': tmp_pop+'/32',
                                    'comment': 'Created by parser'
                                    })
                        elif dst_verdict == 'network':
                            tmp_network = tmp_split.pop(0)
                            tmp_subnet = str(IPv4Network('0.0.0.0/' + tmp_split.pop(0)).prefixlen)
                            tmp_out['destination'] = 'n-'+tmp_network+'n'+tmp_subnet
                            addresses.append({
                                    'name': tmp_out['destination'],
                                    'subnet': tmp_network+'/'+tmp_subnet,
                                    'comment': 'Created by parser'
                                    })
                        else:
                            raise ValueError
                            
                        tmp_out['comment'] = acl_remark
                        acl_remark = ''
                        acls.append(tmp_out)
                        
                    else:
                        raise ValueError

                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (ACLs): ", line)
                print("Were able to parse: ",tmp_out)
                print("Left with:", tmp_split)
                a = input('Error occured. Please enter to continue...')
        # Identify local-in policies
        if re.match("^ssh .*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^http .*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^nat .*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^username .*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^dns server-group.*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^logging.*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^no logging.*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^aaa-server.*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^aaa .*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^snmp-server.*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)
        if re.match("^ntp .*",line):
            misc_settings.append(line)
            unparsed_tree.pop(line)  


    # Return all these things. At this point we aren't being discriminate. These are a raw collections of all items.
    return (interfaces, routes, names, addresses, addrgrps, services, servicegrps, acls, acl_map, misc_settings, unparsed_tree)

def main(config_file: str):
    # Open the source configuration file for reading and import/parse it.
    x = open(config_file,'r')
    config_raw = x.readlines()
    x.close()

    config_level = indent_level(config_raw)
    config_tree = ttree_to_json(config_level)
    ret_interfaces, ret_routes, ret_names, ret_addresses, ret_addrgrps, ret_services, ret_servicegrps, ret_acls, ret_acl_map, ret_misc_settings, ret_unparsed = parse_asa_config(config_tree)

    df_interfaces = pd.DataFrame(data=ret_interfaces)
    df_routes = pd.DataFrame(data=ret_routes)
    df_names = pd.DataFrame(data=ret_names)
    df_addresses = pd.DataFrame(data=ret_addresses)
    df_addrgrps = pd.DataFrame(data=ret_addrgrps)
    df_services = pd.DataFrame(data=ret_services)
    df_servicegrps = pd.DataFrame(data=ret_servicegrps)
    df_acls = pd.DataFrame(data=ret_acls)
    df_acls['direction'].replace(ret_acl_map, inplace=True)
    df_acls.rename(columns={'direction':'srcintf'}, inplace=True)
    df_acls.insert(loc=df_acls.columns.get_loc('action'), column='dstintf', value=['any']*len(df_acls))
    df_misc_settings = pd.DataFrame(data=ret_misc_settings)

    with pd.ExcelWriter(config_file.split('.')[0]+'.xlsx') as writer:
        df_interfaces.to_excel(writer, sheet_name='Interfaces')
        df_routes.to_excel(writer, sheet_name='Routes')
        df_names.to_excel(writer, sheet_name='LocalDNS')
        df_addresses.to_excel(writer, sheet_name='Addresses')
        df_addrgrps.to_excel(writer,sheet_name='AddrGrps')
        df_services.to_excel(writer,sheet_name='Services')
        df_servicegrps.to_excel(writer,sheet_name='ServiceGrps')
        df_acls.to_excel(writer,sheet_name='ACLs')
        df_misc_settings.to_excel(writer,sheet_name='MiscSettings')

    x = open(config_file.split('.')[0]+'.unparsed', 'w')
    for y in ret_unparsed:
        x.write(y+'\n')
        if config_tree[y] != 0:
            for z in config_tree[y]:
                x.write(' '+str(z)+'\n')
    x.close()

if __name__ == '__main__':
  typer.run(main)
