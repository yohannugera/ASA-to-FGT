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
        
        tmp_srcintf = ('srcintf',tuple(eval(tmp_entry['srcintf'])))
        tmp_dstintf = ('dstintf',tuple(eval(tmp_entry['dstintf'])))
        tmp_srcaddr = ('srcaddr',tuple(eval(tmp_entry['srcaddr'])))
        tmp_dstaddr = ('dstaddr',tuple(eval(tmp_entry['dstaddr'])))
        tmp_service = ('service',tuple(eval(tmp_entry['service'])))
        
        tmp_set = set([tmp_srcintf,tmp_dstintf,tmp_srcaddr,tmp_dstaddr,tmp_service])
        
        cmp_entry = new_policies_file[-1]
        
        cmp_srcintf = ('srcintf',tuple(eval(cmp_entry['srcintf'])))
        cmp_dstintf = ('dstintf',tuple(eval(cmp_entry['dstintf'])))
        cmp_srcaddr = ('srcaddr',tuple(eval(cmp_entry['srcaddr'])))
        cmp_dstaddr = ('dstaddr',tuple(eval(cmp_entry['dstaddr'])))
        cmp_service = ('service',tuple(eval(cmp_entry['service'])))
        
        cmp_set = set([cmp_srcintf,cmp_dstintf,cmp_srcaddr,cmp_dstaddr,cmp_service])
        
        fin_set = list(tmp_set-cmp_set)
        
        if len(fin_set) == 1:
            new_policies_file[-1][fin_set[0][0]] = str(eval(new_policies_file[-1][fin_set[0][0]]) + eval(tmp_entry[fin_set[0][0]]))
        elif len(fin_set) == 0:
            pass
        else:
            new_policies_file.append(dict(policies_file.iloc[x]))
        
    df_new_policies_file = pd.DataFrame(new_policies_file)

    with pd.ExcelWriter(config_file, mode='a') as writer:
        df_new_policies_file.to_excel(writer,sheet_name='ACLs-policy_optimize')

if __name__=="__main__":
    typer.run(main)