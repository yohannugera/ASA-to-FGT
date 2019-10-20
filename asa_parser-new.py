import sys
import datetime
import re
import ipaddress
from ciscoconfparse import CiscoConfParse
import ipcalc
from socket import getservbyname
import netaddr
import operator
import xlwt

# Excel Integration
def excel_output(filename, sheet, list1, list2, x, y, z):
    book = xlwt.Workbook()
    sh = book.add_sheet(sheet)

    variables = [x, y, z]
    x_desc = 'Display'
    y_desc = 'Dominance'
    z_desc = 'Test'
    desc = [x_desc, y_desc, z_desc]

    col1_name = 'Stimulus Time'
    col2_name = 'Reaction Time'

    #You may need to group the variables together
    #for n, (v_desc, v) in enumerate(zip(desc, variables)):
    for n, v_desc, v in enumerate(zip(desc, variables)):
        sh.write(n, 0, v_desc)
        sh.write(n, 1, v)

    n+=1

    sh.write(n, 0, col1_name)
    sh.write(n, 1, col2_name)

    for m, e1 in enumerate(list1, n+1):
        sh.write(m, 0, e1)

    for m, e2 in enumerate(list2, n+1):
        sh.write(m, 1, e2)

    book.save(filename)

# Check for numbers in a string
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
        return False

# Function to parse the full configuration into dictionaries/lists that we will later use for analysis. Returns a bunch of lists and dictionaries.
def parse_asa_configuration(input_raw,input_parse):
    # Set up lists and dictionaries for return purposes
    names = []
    objects = {}
    object_groups = {}
    access_lists = []
    object_nat = {}
    static_nat = []
    object_services = {}
    other_services = {}
    # Read each line of the config, looking for configuratio components that we care about
    for line in input_raw:
        # Identify all staticallly configured name/IPAddress translations
        if re.match("^name (([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]).*",line):
            names.append(line)

        # Identify and collect configurations for all configured objects
        if 'object network' in line:
            obj = input_parse.find_children_w_parents(line,'^(?! nat ?.*)')
            obj_name = (line.split()).pop(2)
            if not obj_name in objects and obj:
                objects[obj_name] = (obj)

        # Identify and collect configurations for all configured object groups
        if 'object-group network' in line:
            obj_group = input_parse.find_children_w_parents(line,'.*')
            obj_group_name = (line.split()).pop(2)
            if not obj_group_name in object_groups and obj_group:
                object_groups[obj_group_name] = (obj_group)

        # Identify and collect configurations for all configured access lists
        if re.match("^access-list .*",line):
            access_lists.append(line)

        # Identify and collect configurations for all configured object NATs
        if 'object network' in line:
            obj_nat = input_parse.find_children_w_parents(line,'^ nat .*')
            obj_nat_name = (line.split()).pop(2)
            if not obj_nat_name in object_nat and obj_nat:
                object_nat[obj_nat_name] = (obj_nat)

        # Identify and collect configurations for all configured static NATs
        if re.match("^nat .*",line):
            static_nat.append(line)

        # Identify and collect configurations for all configured service objects
        if 'object-group service' in line:
            obj_service = input_parse.find_children_w_parents(line,'.*')
            obj_service_name = (line.split()).pop(2)
            if not obj_service_name in object_services and obj_service:
                object_services[obj_service_name] = (obj_service)

        # Identify and collect configurations for all configured misc service objects
        if 'object service' in line:
            other_obj = input_parse.find_children_w_parents(line,'.*')
            other_obj_name = (line.split()).pop(2)
            if not other_obj_name in other_services and other_obj:
                other_services[other_obj_name] = (other_obj)
        
    # Return all these things. At this point we aren't being discriminate. These are a raw collections of all items.
    return(names,objects,object_groups,access_lists,object_nat,static_nat,object_services,other_services)


def main():
    user_source_file = "running-config.cfg"

    # Open the source configuration file for reading and import/parse it.
    x = open(user_source_file,'r')
    config_raw = x.readlines()
    config_parse = CiscoConfParse(config_raw) 
    x.close()

    # Send configuration off to get split up into different lists/dictionaries for reference
    ret_names, ret_objects, ret_object_groups, ret_access_lists, ret_object_nat, ret_static_nat, ret_service_objects, ret_custom_objects = parse_asa_configuration(config_raw,config_parse)

    # Fine tune Lists and Dictionaries
    network_objects = {}
    object_groups = {}
    network_services = {}
    service_objects = {}
    
    # Names
    for x in ret_names:
        tmp = x.split(' ')
        network_objects[tmp[-1][:-1]] = tmp[1]+"/32"

    # Objects
    for x in ret_objects:
        if ret_objects[x][0].lstrip().split(" ")[0] == "host":
            network_objects[x] = ret_objects[x][0].lstrip().split(" ")[1][:-1]+"/32"
        else:
            netmask = netaddr.IPAddress(ret_objects[x][0].lstrip().split(" ")[-1][:-1]).netmask_bits()
            network_objects[x] = ret_objects[x][0].lstrip().split(" ")[1]+"/"+str(netmask)

    # Object Groups
    for x in ret_object_groups:
        object_groups[x] = []
        for y in ret_object_groups[x]:
            if y.lstrip().split(" ")[0] == "network-object" and y.lstrip().split(" ")[1] == "host":
                object_groups[x].append(y.lstrip().split(" ")[-1][:-1]+"/32")
            elif y.lstrip().split(" ")[0] == "network-object" and y.lstrip().split(" ")[1] == "object":
                object_groups[x].append(y.lstrip().split(" ")[-1][:-1])
            elif y.lstrip().split(" ")[0] == "network-object":
                object_groups[x].append(y.lstrip().split(" ")[1]+"/"+str(netaddr.IPAddress(y.lstrip().split(" ")[-1][:-1]).netmask_bits()))
            elif y.lstrip().split(" ")[0] == "group-object":
                object_groups[x].append(y.lstrip().split(" ")[-1][:-1])
            else:
                print "error occured during Object Groups"

    # Services
    for x in ret_custom_objects:
        tmp = ret_custom_objects[x][0].strip().split(" ")
        if not is_number(tmp[-1]):
            network_services[x] = tmp[1]+"/"+str(getservbyname(tmp[-1]))
        else:
            network_services[x] = tmp[1]+"/"+tmp[-1]

    # Service Objects
##    for x in ret_service_objects:
##        service_objects[x] = []
##        for y in ret_service_objects[x]:
##            tmp = y.lstrip().split(" ")
##            if tmp[0] == "port-object" and tmp[1] == "eq":
##                if not is_number(tmp[-1]):
##                    service_objects[x].append("tcp/"+str(getservbyname(tmp[-1][:-1])))
##                else:
##                    service_objects[x].append("tcp/"+tmp[-1][:-1])
##            elif tmp[0] == "port-object" and tmp[1] == "range":
##                service_objects[x].append("tcp/"+tmp[-2]+"-"+tmp[1][:-1])
##            elif tmp[0] == "group-object":
##                service_objects[x].append(tmp[-1][:-1])
##            elif tmp[0] == "service-object" and tmp[1] == "tcp":
##                if not is_number(tmp[-1]):
##                    service_objects[x].append("tcp/"+str(getservbyname(tmp[-1][:-1])))
##                else:
##                    service_objects[x].append("tcp/"+tmp[-1][:-1])

    for x in ret_access_lists:
        

##    # Convert service objects to FGT
##    fs.write("config firewall service group\n")
##    for x in ret_service_objects:
##        fs.write(" edit "+x+"\n")
##        fg.write("  set member ")
##        for y in ret_service_objects[x]:
##            tmp = y.lstrip().split(" ")
##            if tmp[1] == "eq":
##                if not is_number(tmp[-1][:-1]):
##                    fs.write("\""+tmp[-1][:-1].upper()+"\" ")
##                else:
##                    fc.write(" edit Port-"+tmp[-1])
##                    fc.write("  set protocol TCP/UDP/SCTP\n")
##                    fc.write("  set tcp-portrange "+tmp[-1])
##                    fc.write(" next\n")
##                    fs.write("\"Port-"+tmp[-1][:-1]+"\" ")
##            elif tmp[1] == "range":
##                fc.write(" edit Port-"+tmp[-2]+"-"+tmp[-1])
##                fc.write("  set protocol TCP/UDP/SCTP\n")
##                fc.write("  set tcp-portrange "+tmp[-2]+"-"+tmp[-1])
##                fc.write(" next\n")
##                fs.write("\"Port-"+tmp[-2]+"-"+tmp[-1][:-1]+"\" ")
##
####config firewall service group
#### edit "Cas_Publishing_Udp"
####  set member "DNS" "UDP-80" "UDP-443" 
#### next
##        
##
##
##    #ret_object_nat, ret_static_nat, ret_service_objects
##
##    # Closing FGT Config Files
##    fn.write("end")
##    fn.close()
##    fg.write("end")
##    fg.close()
##    fc.write("end")
##    fc.close()
##    fs.write("end")
##    fs.close()
if __name__ == '__main__':
  main()
