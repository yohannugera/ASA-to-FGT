# This is where I'll configure rule-consolidation and route-checkup
import pandas as pd
import typer

def main(config_file: str):
    ## Reading Excel Configuration
    file = pd.ExcelFile(config_file)
    
    # Read Address Groups from Excel
    policies_file = pd.read_excel(file,'ACLs')
    
    new_policies_file = pd.DataFrame(policies_file.T.pop(0))
    policies_file.drop(index=policies_file.index[0],axis=0,inplace=True)
    
    while len(policies_file)>0:
        new_policies_file.append(policies_file.T.pop(0))
        policies_file.drop(index=policies_file.index[0],axis=0,inplace=True)
        

if __name__=="__main__":
    typer.run(main)