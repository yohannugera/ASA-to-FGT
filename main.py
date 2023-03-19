import re
from ipaddress import IPv4Network
import pandas as pd

indentation_length = ' '

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
            tmp_out = {}
            tmp_obj = line.split(' ')
            tmp_obj_value = ''
            tmp_obj_description = ''
            try:
                for x in config_tree[line].keys():
                    if re.match("^host.*",x):
                        tmp_obj_value = x.split(' ')[-1]+'/32'
                    elif re.match("^description.*",x):
                        tmp_obj_description = x[12:]
                    elif re.match("^subnet",x):
                        tmp_line = x.split(' ')
                        tmp_obj_value = tmp_line[1]+'/'+str(IPv4Network('0.0.0.0/' + tmp_line[2]).prefixlen)
                    else:
                        raise ValueError

                tmp_out['name'] = tmp_obj[-1]
                tmp_out['subnet'] = str(tmp_obj_value)
                tmp_out['description'] = tmp_obj_description
                addresses.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Addresses): ",line)
        # Identify and collect configurations for all configured object groups
        if re.match("^object-group network.*",line):
            tmp_out = {}
            tmp_obj = line.split(' ')
            tmp_obj_members = []
            tmp_obj_description = ''
            try:
                for x in config_tree[line].keys():
                    if re.match("^network-object host .*", x):
                        tmp = x.split(' ')[-1]
                        addresses.append({'name':'h-'+tmp,'subnet':tmp+'/32'})
                        tmp_obj_members.append('h-'+tmp)
                    elif re.match("^network-object object.*",x):
                        tmp = x.split(' ')[-1]
                        tmp_obj_members.append(tmp)
                    elif re.match("^network-object.*",x):
                        tmp = x.split(' ')
                        addresses.append({'name':"net-"+tmp[-2]+"n"+str(IPv4Network('0.0.0.0/'+tmp[-1]).prefixlen),'subnet':tmp[-2] + "/" + str(IPv4Network('0.0.0.0/'+tmp[-1]).prefixlen)})
                        tmp_obj_members.append("net-"+tmp[-2]+"n"+str(IPv4Network('0.0.0.0/'+tmp[-1]).prefixlen))
                    elif re.match("^group-object.*",x):
                        tmp = x.split(' ')[-1]
                        tmp_obj_members.append(tmp)
                    elif re.match("^description.*", x):
                        tmp_obj_description = x[12:]
                    else:
                        raise ValueError

                tmp_out['name'] = tmp_obj[-1]
                tmp_out['members'] = tmp_obj_members
                tmp_out['description'] = tmp_obj_description
                addrgrps.append(tmp_out)
                unparsed_tree.pop(line)

            except:
                print("Error in parsing line (Object Groups): ", line)
        # Identify and collect configurations for all configured services
        if re.match("^object service.*",line):
            tmp_out = {}
            tmp_out['name'] = line.split(' ')[-1]
            tmp_obj_type = ''
            tmp_obj_value = ''
            tmp_obj_direction = ''
            tmp_obj_description = ''
            try:
                for x in config_tree[line].keys():
                    if re.match("^service.*",x):
                        tmp_obj_type = x.split(' ')[1]
                        tmp_obj_direction = x.split(' ')[2]
                        if x.split(' ')[3] == "eq":
                            tmp_obj_value = x.split(' ')[4]
                        else:
                            raise ValueError
                    elif re.match("^description.*",x):
                        tmp_obj_description = x[12:]
                    else:
                        raise ValueError

                tmp_out['type'] = tmp_obj_type
                tmp_out['value'] = tmp_obj_value
                tmp_out['description'] = tmp_obj_description
                tmp_out['direction'] = tmp_obj_direction
                services.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Services): ",line)
        # Identify and collect configurations for all configured service objects
        if re.match("^object-group service.*tcp",line):
            try:
                tmp_out = {}
                tmp_out['name'] = line.split(' ')[2]
                tmp_obj_members = []
                tmp_obj_description = ''
                tmp_obj_type = line.split(' ')[3]
                for x in config_tree[line].keys():
                    if re.match("^port-object.*", x):
                        if x.split(' ')[1] == "eq":
                            tmp_obj_members.append(x.split(' ')[2])
                            services.append({'name':x.split(" ")[2],'type':tmp_obj_type,'value':x.split(" ")[2],'direction':'destination','description':''})
                        else:
                            raise ValueError
                    elif re.match("^description.*", x):
                        tmp_obj_description = x[12:]
                    else:
                        raise ValueError

                tmp_out['members'] = tmp_obj_members
                tmp_out['description'] = tmp_obj_description
                servicegrps.append(tmp_out)
                unparsed_tree.pop(line)
            except:
                print("Error in parsing line (Service Groups): ", line)

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
  main()