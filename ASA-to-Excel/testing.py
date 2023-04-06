import json
import re
import typer

def main():
    data = {}
    runconfig = ''
    
#    with open('CNTCG-SECFEC101-21MAR2023.txt','r') as config:
    config = "class-map sfr\n match access-list sfr_redirect\nclass-map inspection_default\n match default-inspection-traffic"
    test = re.findall(r"^class-map sfr\n.*", config)
    print(test)
        
if __name__=="__main__":
    typer.run(main)