# This is where I'll configure rule-consolidation and route-checkup
import pandas as pd
import typer

def main(config_file: str):
    ## Reading Excel Configuration
    file = pd.ExcelFile(config_file)
    
    # Read Address Groups from Excel
    policies_file = pd.read_excel(file,'ACLs')
    
    new_policies_file = [dict(policies_file.iloc[0])]
    
    for x in range(1,len(policies_file)):
        tmp_entry = dict(policies_file.iloc[x])
        
        tmp_srcintf = ('srcintf',tmp_entry['srcintf'])
        tmp_dstintf = ('dstintf',tmp_entry['dstintf'])
        tmp_srcaddr = ('srcaddr',tmp_entry['srcaddr'])
        tmp_dstaddr = ('dstaddr',tmp_entry['dstaddr'])
        tmp_service = ('service',tmp_entry['service'])
        
        tmp_set = set([tmp_srcintf,tmp_dstintf,tmp_srcaddr,tmp_dstaddr,tmp_service])
        
        cmp_entry = new_policies_file[-1]
        
        cmp_srcintf = ('srcintf',tuple(cmp_entry['srcintf'])) if isinstance(cmp_entry['srcintf'],list) else ('srcintf',cmp_entry['srcintf'])
        cmp_dstintf = ('dstintf',tuple(cmp_entry['dstintf'])) if isinstance(cmp_entry['dstintf'],list) else ('dstintf',cmp_entry['dstintf'])
        cmp_srcaddr = ('srcaddr',tuple(cmp_entry['srcaddr'])) if isinstance(cmp_entry['srcaddr'],list) else ('srcaddr',cmp_entry['srcaddr'])
        cmp_dstaddr = ('dstaddr',tuple(cmp_entry['dstaddr'])) if isinstance(cmp_entry['dstaddr'],list) else ('dstaddr',cmp_entry['dstaddr'])
        cmp_service = ('service',tuple(cmp_entry['service'])) if isinstance(cmp_entry['service'],list) else ('service',cmp_entry['service'])
        
        cmp_set = set([cmp_srcintf,cmp_dstintf,cmp_srcaddr,cmp_dstaddr,cmp_service])
        
        fin_set = list(tmp_set-cmp_set)
        
        if len(fin_set) == 1:
            if isinstance(cmp_entry[fin_set[0][0]],list):
                new_policies_file[-1][fin_set[0][0]].append(tmp_entry[fin_set[0][0]])
            else:
                new_policies_file[-1][fin_set[0][0]] = [cmp_entry[fin_set[0][0]],tmp_entry[fin_set[0][0]]]
        elif len(fin_set) == 0:
            pass
        else:
            new_policies_file.append(dict(policies_file.iloc[x]))
        
    df_new_policies_file = pd.DataFrame(new_policies_file)

    with pd.ExcelWriter(config_file, mode='a') as writer:
        df_new_policies_file.to_excel(writer,sheet_name='ACLs-policy_optimize')

if __name__=="__main__":
    typer.run(main)