import pandas as pd
import numpy as np
from ipaddress import *
import csv
import re

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
        print("Error in finding best route for ",x)
        raise

## Reading Excel Configuration
config_file = pd.ExcelFile('configs_FGT-NS-DR_exported.xlsx')
#interfaces_file = pd.read_excel(config_file,'Interfaces')
routes_file = pd.read_excel(config_file,'Routes')
addr_file = pd.read_excel(config_file,'Addresses')
iprange_file = pd.read_excel(config_file,'IPranges')
addrgrp_file = pd.read_excel(config_file,'Addrgrps')
service_file = pd.read_excel(config_file,'Services')
servicegrp_file = pd.read_excel(config_file,'Servicegrps')
#user_file = pd.read_excel(config_file,'Users')
fqdn_file = pd.read_excel(config_file,'FQDNs')
policy_file = pd.read_excel(config_file,'Policies')

## Routes...
intf_assoc = {}
for x in routes_file.to_dict(orient='records'):
    tmp = x['dst'].split()
    ip_sub = '/'.join(tmp)
    intf_assoc[ip_sub] = x['device']

## Address Objects...
addr_obj = {}
for x in addr_file.to_dict(orient='records'):
    try:
        addr_obj[x['name']] = x['subnet']
    except:
        print("Error in importing ",x," to addr_obj")

## IP Ranges...
ip_rngs = {}
for x in iprange_file.to_dict(orient='records'):
    ip_rngs[x['name']] = x['start-ip']+"-"+x['end-ip']

#### Users...
##users = {}
##for x in user_file.to_dict(orient='records'):
##    users[x['name']] = x['Users'].split('|')

## FQDNs...
fqdns = {}
for x in fqdn_file.to_dict(orient='records'):
    fqdns[x['name']] = x['URL']

## Address Groups...
addr_grps = {}
for index, row in addrgrp_file.iterrows():
    try:
        addr_grps[row['name']] = [tmp['name'] for tmp in eval(row['member'])]
    except:
        print("Error in importing ",row['member']," to addr_grps")

default_route_intf = 'DC-Core.300'
obj_route = {}
for x in list(addr_obj.keys()):
    tmp = ' '.join(route_calculate('/'.join(addr_obj[x].split()),intf_assoc,default_route_intf))
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

## fqdns...
for x in fqdn_file.to_dict(orient='records'):
    obj_route[x['name']] = 'DC-Core.300'

df = pd.DataFrame(list(obj_route.items()),columns = ['Address','Routed Interface'])
df.to_csv('obj_route.csv')

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

##for x in grps_with_no_route:
##    routes = []
##    for y in addr_grps[x]:
##        if y in obj_route.keys():
##            routes = routes + obj_route[y].split(' ')
##        elif y in grp_route.keys():
##            routes = routes + grp_route[y].split(' ')
##        else:
##            print("Error in finding best route for ",x," : ",y)
##
##    if ('' in routes) and (len(set(routes))>1):
##        tmpx = set(routes)
##        tmpx.remove('')
##        tmpy = ' '.join(list(tmpx))
##        tmpy.strip()
##        grp_route[x] = re.sub(' +',' ',tmpy)
##    if ('' in routes) and (len(set(routes))==1):
##        grp_route[x] = ''
##    else:
##        tmp = ' '.join(list(set(routes)))
##        tmp.strip()
##        grp_route[x] = tmp
##
df = pd.DataFrame(list(grp_route.items()),columns = ['AddrGrp','Routed Interface'])
df.to_csv('grp_route.csv')

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
srcintf_col = []
dstintf_col = []
## Policies...
for index, row in policy_file.iterrows():
    try:
        srcintf = []
        dstintf = []
        for x in eval(row['srcaddr']):
            srcintf = srcintf + obj_route[x['name']].split()
        for x in eval(row['dstaddr']):
            dstintf = dstintf + obj_route[x['name']].split()
        srcintf_col.append(' '.join(list(set(srcintf))))
        dstintf_col.append(' '.join(list(set(dstintf))))
    except:
        print("Error in : ",row)
        raise
policy_file.insert(0, "srcintf", srcintf_col, True)
policy_file.insert(1, "dstintf", dstintf_col, True)
policy_file.dropna(how='all')
policy_file.drop(policy_file[policy_file['srcintf']==''].index, inplace=True)
policy_file.drop(policy_file[policy_file['dstintf']==''].index, inplace=True)
##policy_file.drop(policy_file[policy_file['src_negate']=='enable'].index, inplace=True)
##policy_file.drop(policy_file[policy_file['dst_negate']=='enable'].index, inplace=True)

writer = pd.ExcelWriter('config_new.xlsx')
policy_file.to_excel(writer,'Policies')
routes_file.to_excel(writer,'Routes')
addr_file.to_excel(writer,'Addresses')
iprange_file.to_excel(writer,'IPRanges')
addrgrp_file.to_excel(writer,'Addrgrps')
service_file.to_excel(writer,'Services')
servicegrp_file.to_excel(writer,'Servicegrps')
fqdn_file.to_excel(writer,'FQDNs')
writer.save()

