###########################################################################
# Name      : asa_parser.py
# Function  : Accepts ASA running-config and creates FortiGate Config
# Comment   : run in cmd "python asa_parser.py <config_file>         
###########################################################################

import sys
import datetime
import re
import ipaddress
from ciscoconfparse import CiscoConfParse
import netaddr

# Function to parse the full configuration into dictionaries/lists that we will later use for analysis. Returns a bunch of lists and dictionaries.
def parse_asa_configuration(input_raw,input_parse):
    # Set up lists and dictionaries for return purposes
    names = []
    objects = {}
    object_groups = {}
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
    
    return(names,objects,object_groups)


def main(config_file):
    user_source_file = config_file

    # Open the source configuration file for reading and import/parse it.
    x = open(user_source_file,'r')
    config_raw = x.readlines()
    config_parse = CiscoConfParse(config_raw) 
    x.close()

    # Send configuration off to get split up into different lists/dictionaries for reference
    ret_names, ret_objects, ret_object_groups = parse_asa_configuration(config_raw,config_parse)

    # Fine tune Lists and Dictionaries
    network_objects = {}
    object_groups = {}

    # Create new files to put FGT Configs
    fn = open("config-firewall-address.txt", "w")
    fg = open("config-firewall-addrgrp.txt", "w")
    fn.write("config firewall address\n")
    fg.write("config firewall addrgrp\n")
    
    # Names
    for x in ret_names:
        tmp = x.split(' ')
        network_objects[tmp[-1][:-1]] = tmp[1]+"/32"
        fn.write(" edit "+tmp[-1])
        fn.write("  set subnet "+tmp[1]+" 255.255.255.255\n")
        fn.write(" next\n")

    # Objects
    for x in ret_objects:
        fn.write(" edit "+x+"\n")
        if ret_objects[x][0].lstrip().split(" ")[0] == "host":
            network_objects[x] = ret_objects[x][0].lstrip().split(" ")[1][:-1]+"/32"
            fn.write("  set subnet "+ret_objects[x][0].lstrip().split(" ")[1][:-1]+" 255.255.255.255\n")
            fn.write(" next\n")
            
        else:
            netmask = netaddr.IPAddress(ret_objects[x][0].lstrip().split(" ")[-1][:-1]).netmask_bits()
            network_objects[x] = ret_objects[x][0].lstrip().split(" ")[1]+"/"+str(netmask)
            fn.write("  set "+ret_objects[x][0].lstrip())
            fn.write(" next\n")

    # Object Groups
    for x in ret_object_groups:
        object_groups[x] = []
        fg.write(" edit "+x+"\n")
        fg.write("  set member ")
        for y in ret_object_groups[x]:
            if y.lstrip().split(" ")[0] == "network-object" and y.lstrip().split(" ")[1] == "host":
                object_groups[x].append(y.lstrip().split(" ")[-1][:-1]+"/32")
                fn.write(" edit h-"+y.lstrip().split(" ")[-1])
                fn.write("  set subnet "+y.lstrip().split(" ")[-1][:-1]+" 255.255.255.255\n")
                fn.write(" next\n")
                fg.write("\"h-"+y.lstrip().split(" ")[-1][:-1]+"\" ")
                
            elif y.lstrip().split(" ")[0] == "network-object" and y.lstrip().split(" ")[1] == "object":
                object_groups[x].append(y.lstrip().split(" ")[-1][:-1])
                fg.write("\""+y.lstrip().split(" ")[-1][:-1]+"\" ")
                
            elif y.lstrip().split(" ")[0] == "network-object":
                object_groups[x].append(y.lstrip().split(" ")[1]+"/"+str(netaddr.IPAddress(y.lstrip().split(" ")[-1][:-1]).netmask_bits()))
                tmp = y.lstrip().split(" ")
                fn.write(" edit n-"+tmp[1]+"/"+str(netaddr.IPAddress(y.lstrip().split(" ")[-1][:-1]).netmask_bits())+"\n")
                fn.write("  set subnet "+tmp[1]+" "+tmp[2])
                fn.write(" next\n")
                fg.write("\"n-"+tmp[1]+"/"+str(netaddr.IPAddress(y.lstrip().split(" ")[-1][:-1]).netmask_bits())+"\" ")
                
            elif y.lstrip().split(" ")[0] == "group-object":
                object_groups[x].append(y.lstrip().split(" ")[-1][:-1])
                fg.write("\""+y.lstrip().split(" ")[-1][:-1]+"\" ")
                
            else:
                print "error occured during Object Groups"
        fg.write("\n next\n")

    # Closing FGT Config Files
    fn.write("end")
    fn.close()
    fg.write("end")
    fg.close()

if __name__ == '__main__':
    fileout=sys.stdout
    from sys import argv, stdin
    if len(argv) == 2:
        config_file = argv[1]
        main(config_file)

    else:
        print 'Please provide ASA configuration files...'
