import pandas as pd
import numpy as np
from ipaddress import *
import csv
import re
import typer

def route_calculate(address,routes,default_routed_interface):
    try:
        routed_interfaces = []
        setaddr_obj = set()
        setaddr_obj.add(address)
        while len(setaddr_obj):
            y = setaddr_obj.pop()
            for r in routes.keys():
                if IPv4Network(y).subnet_of(IPv4Network(r)):
                    routed_interfaces.append(intf_assoc[r])
                    break
                elif IPv4Network(r).subnet_of(IPv4Network(y)):
                    routed_interfaces.append(intf_assoc[r])
                    setaddr_obj = setaddr_obj.union(set([str(ip) for ip in IPv4Network(y).address_exclude(IPv4Network(r))]))
            if len(routed_interfaces)==0:
                routed_interfaces.append(default_routed_interface)

        return(list(set(routed_interfaces)))
    except:
        print("Error in finding best route for ",address)
        a = input('Press ENTER to continue...')

def main(config_file: str):
    ## Reading Excel Configuration
    file = pd.ExcelFile(config_file)
    #interfaces_file = pd.read_excel(config_file,'Interfaces')
    routes_file = pd.read_excel(file,'Routes')
    addr_file = pd.read_excel(file,'Addresses')
    #iprange_file = pd.read_excel(config_file,'IPranges')
    #fqdn_file = pd.read_excel(config_file,'FQDNs')
    addrgrp_file = pd.read_excel(file,'AddrGrps')
    service_file = pd.read_excel(file,'Services')
    servicegrp_file = pd.read_excel(file,'ServiceGrps')
    policy_file = pd.read_excel(file,'ACLs')

    ## Routes...
    global intf_assoc
    intf_assoc = {}
    for x in routes_file.to_dict(orient='records'):
        if x['dst'] != '0.0.0.0/0':
            intf_assoc[x['dst']] = x['device']
        else:
            global default_route_intf
            default_route_intf = x['device']

    ## Address Objects...
    addr_obj = {}
    addr_obj['all'] = '0.0.0.0/0'
    for x in addr_file.to_dict(orient='records'):
        try:
            addr_obj[x['name']] = x['subnet']
        except:
            print("Error in importing ",x," to addr_obj")

    ## IP Ranges...
    ip_rngs = {}
    ##for x in iprange_file.to_dict(orient='records'):
    ##    ip_rngs[x['name']] = x['start-ip']+"-"+x['end-ip']

    ## Users...
    users = {}
    ##for x in user_file.to_dict(orient='records'):
    ##    users[x['name']] = x['Users'].split('|')

    ## FQDNs...
    fqdns = {}
    ##for x in fqdn_file.to_dict(orient='records'):
    ##    fqdns[x['name']] = x['URL']

    ## Address Groups...
    addr_grps = {}
    for x in addrgrp_file.to_dict(orient='records'):
        try:
            addr_grps[x['name']] = eval(x['members'])
        except:
            print("Error in importing ",x['members']," to addr_grp",x['name'])
            a = input("Press ENTER to continue with errors...")

    global obj_route
    obj_route = {}
    for x in list(addr_obj.keys()):
        tmp = ' '.join(route_calculate(addr_obj[x],intf_assoc,default_route_intf))
        print("Best route for ",x,tmp)
        obj_route[x] = re.sub(' +',' ',tmp)

    for x in list(ip_rngs.keys()):
        try:
            tmp = ip_rngs[x].split('-')
            routes = []
            for z in summarize_address_range(IPv4Address(tmp[0]),IPv4Address(tmp[1])):
                for y in intf_assoc.keys():
                    if z.overlaps(IPv4Network(y)):
                        routes.append(intf_assoc[y])
            tmp = ' '.join(list(set(routes)))
            obj_route[x] = re.sub(' +',' ',tmp)
        except:
            print("Error in finding best route for ",x)

    #### fqdns...
    ##for x in fqdn_file.to_dict(orient='records'):
    ##    obj_route[x['name']] = default_route_intf

    df = pd.DataFrame(list(obj_route.items()),columns = ['Address','Routed Interface'])
    df.to_csv(config_file+'-address_check.csv')

    global grp_route
    grp_route = {}
    grps_with_no_route = []
    objs_with_no_route = []
    for x in list(addr_grps.keys()):
        routes = []
        for y in addr_grps[x]:
            if y in obj_route.keys():
                routes = routes + obj_route[y].split(' ')
            elif y in grp_route.keys():
                routes = routes + grp_route[y].split(' ')
            else:
                grps_with_no_route.append(x)
                objs_with_no_route.append(y)

        if ('' in routes) and (len(set(routes))>1):
            tmpx = set(routes)
            tmpx.remove('')
            tmpy = ' '.join(list(tmpx))
            tmpy.strip()
            grp_route[x] = re.sub(' +',' ',tmpy)
        if ('' in routes) and (len(set(routes))==1):
            grp_route[x] = ''
        else:
            tmp = ' '.join(list(set(routes)))
            tmp.strip()
            grp_route[x] = tmp
    
    df = pd.DataFrame(list(grp_route.items()),columns = ['AddrGrp','Routed Interface'])
    df.to_csv(config_file+'-addrgrp_check.csv')

    obj_route.update(grp_route)

    #### users...
    ##for x in user_file.to_dict(orient='records'):
    ##    obj_route[x['name']] = ''
    ##
    #### There're some whitespaces in Routed Interfaces. I tried to remove them as you can see,
    #### but for some reason, those are still there. Bit stubborn I guess. So, I entered another layer of
    #### validation. If you see what caused this, hooray :D
    ##
    ##for x in obj_route.keys():
    ##    tmp = obj_route[x]
    ##    tmpx = tmp.strip()
    ##    obj_route[x] = re.sub(' +',' ',tmpx)
    ##

    dstintf_col = []
    ## Policies...
    for x in policy_file.to_dict(orient='records'):
        try:
            dstintf_col.append(str(obj_route[x['dstaddr']].split(' ')))
        except:
            print("Error in: ",x)
            a = input('Press ENTER to continue...')

    policy_file.insert(0, "dstintf-new", dstintf_col, True)
    ##policy_file.drop(policy_file[policy_file['src_negate']=='enable'].index, inplace=True)
    ##policy_file.drop(policy_file[policy_file['dst_negate']=='enable'].index, inplace=True)
    
    with pd.ExcelWriter(config_file, mode='a') as writer:
        policy_file.to_excel(writer,sheet_name='ACLs-route_check')

if __name__ == '__main__':
  typer.run(main)
