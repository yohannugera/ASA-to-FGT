import re
from ipaddress import IPv4Network
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
    'udp':'17'
}
default_ports = {
    'aol':['TCP','5190'],
    'bgp':['TCP','179'],
    'biff':['UDP','512'],
    'bootpc':['UDP','68'],
    'bootps':['UDP','67'],
    'chargen':['TCP','19'],
    'cifs':['TCP-UDP','3020'],
    'citrix-ica':['TCP','1494'],
    'cmd':['TCP','514'],
    'ctiqbe':['TCP','2748'],
    'daytime':['TCP','13'],
    'discard':['TCP-UDP','9'],
    'dnsix':['UDP','195'],
    'domain':['TCP-UDP','53'],
    'echo':['TCP-UDP','7'],
    'exec':['TCP','512'],
    'finger':['TCP','79'],
    'ftp':['TCP','21'],
    'ftp-data':['TCP','20'],
    'gopher':['TCP','70'],
    'h323':['TCP','1720'],
    'hostname':['TCP','101'],
    'http':['TCP-UDP','80'],
    'https':['TCP','443'],
    'ident':['TCP','113'],
    'imap4':['TCP','143'],
    'irc':['TCP','194'],
    'isakmp':['UDP','500'],
    'kerberos':['TCP-UDP','750'],
    'klogin':['TCP','543'],
    'kshell':['TCP','544'],
    'ldap':['TCP','389'],
    'ldaps':['TCP','636'],
    'login':['TCP','513'],
    'lotusnotes':['TCP','1352'],
    'lpd':['TCP','515'],
    'mobile-ip':['UDP','434'],
    'nameserver':['UDP','42'],
    'netbios-dgm':['UDP','138'],
    'netbios-ns':['UDP','137'],
    'netbios-ssn':['TCP','139'],
    'nfs':['TCP-UDP','2049'],
    'nntp':['TCP','119'],
    'ntp':['UDP','123'],
    'pcanywhere-data':['TCP','5631'],
    'pcanywhere-status':['UDP','5632'],
    'pim-auto-rp':['TCP-UDP','496'],
    'pop2':['TCP','109'],
    'pop3':['TCP','110'],
    'pptp':['TCP','1723'],
    'radius':['UDP','1645'],
    'radius-acct':['UDP','1646'],
    'rip':['UDP','520'],
    'rsh':['TCP','514'],
    'rtsp':['TCP','554'],
    'secureid-udp':['UDP','5510'],
    'sip':['TCP-UDP','5060'],
    'smtp':['TCP','25'],
    'snmp':['UDP','161'],
    'snmptrap':['UDP','162'],
    'sqlnet':['TCP','1521'],
    'ssh':['TCP','22'],
    'sunrpc':['TCP-UDP','111'],
    'syslog':['UDP','514'],
    'tacacs':['TCP, UDP','49'],
    'talk':['TCP-UDP','517'],
    'telnet':['TCP','23'],
    'tftp':['UDP','69'],
    'time':['UDP','37'],
    'uucp':['TCP','540'],
    'vxlan':['UDP','4789'],
    'who':['UDP','513'],
    'whois':['TCP','43'],
    'www':['TCP-UDP','80'],
    'xdmcp':['UDP','177']
}

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
    names = []
    addresses = []
    addrgrps = []
    services = []
    servicegrps = []
    acls = []
    unparsed_tree = config_tree.copy()
    # Read each line of the config, looking for configuration components that we care about
    for line in config_tree.keys():
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
        # Identify and collect configurations for all configured services
        if re.match("^object service.*",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[-1]
                tmp_out_type = ''
                tmp_out['value'] = ''
                tmp_out['direction'] = ''
                tmp_out['comment'] = ''
                for x in config_tree[line].keys():
                    if re.match("^service.*",x):
                        tmp_out_type = x.split(' ')[1]
                        tmp_out['direction'] = x.split(' ')[2]
                        if x.split(' ')[3] == "eq":
                            tmp_out['value'] = x.split(' ')[4]
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
                        if x.split(' ')[1] == "eq":
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
        elif re.match("^object-group service.* udp$",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[2]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                tmp_out_type = line.split(' ')[3]
                for x in config_tree[line].keys():
                    if re.match("^port-object.*", x):
                        if x.split(' ')[1] == "eq":
                            tmp_out['members'].append(tmp_out_type+'-'+x.split(' ')[2])
                            services.append({'name':tmp_out_type+'-'+x.split(" ")[2],
                                             'type':tmp_out_type,
                                             'value':x.split(" ")[2],
                                             'direction':'destination',
                                             'comment':''})
                        elif x.split(' ')[1] == "range":
                            tmp_out['members'].append(tmp_out_type+'-'+tmp_out_type+'-'+x.split(' ')[2]+'-'+x.split(' ')[3])
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
        elif re.match("^object-group service.* tcp-udp$",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[2]
                tmp_out['members'] = []
                tmp_out['comment'] = ''
                tmp_out_type = line.split(' ')[3]
                for x in config_tree[line].keys():
                    if re.match("^port-object.*", x):
                        if x.split(' ')[1] == "eq":
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
                                             'value': x.split(' ')[2]+x.split(' ')[3],
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

#        # Identify and collect configurations for all configured access lists
#        if re.match("^access-list .*", line):
#            access_lists.append(line)
#
#        # Identify and collect configurations for all configured static NATs
#        if re.match("^nat .*", line):
#            static_nat.append(line)


    # Return all these things. At this point we aren't being discriminate. These are a raw collections of all items.
    return (names, addresses, addrgrps, services, servicegrps, acls, unparsed_tree)

def main():
    # Setting up config-file
    user_source_file = "src/running-config.cfg"

    # Open the source configuration file for reading and import/parse it.
    x = open(user_source_file,'r')
    config_raw = x.readlines()
    x.close()

    config_level = indent_level(config_raw)
    config_tree = ttree_to_json(config_level)
    ret_names, ret_addresses, ret_addrgrps, ret_services, ret_servicegrps, ret_acls, ret_unparsed = parse_asa_config(config_tree)

    df_names = pd.DataFrame(data=ret_names)
    df_addresses = pd.DataFrame(data=ret_addresses)
    df_addrgrps = pd.DataFrame(data=ret_addrgrps)
    df_services = pd.DataFrame(data=ret_services)
    df_servicegrps = pd.DataFrame(data=ret_servicegrps)
    df_acls = pd.DataFrame(data=ret_acls)

    with pd.ExcelWriter('output.xlsx') as writer:
        df_names.to_excel(writer, sheet_name='LocalDNS')
        df_addresses.to_excel(writer, sheet_name='Addresses')
        df_addrgrps.to_excel(writer,sheet_name='AddrGrps')
        df_services.to_excel(writer,sheet_name='Services')
        df_servicegrps.to_excel(writer,sheet_name='ServiceGrps')
        df_acls.to_excel(writer,sheet_name='ACLs')

    x = open('output.unparsed', 'w')
    for y in ret_unparsed:
        x.write(y+'\n')
        if config_tree[y] != 0:
            for z in config_tree[y]:
                x.write(' '+str(z)+'\n')
    x.close()

if __name__ == '__main__':
  typer.run(main)
