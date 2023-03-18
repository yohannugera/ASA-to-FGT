###########################################################################
# Name      : rule_checkup.py
# Function  : Accepts ASA running-config and creates an excel with rules
# Comment   : run in cmd "python rule_checkup.py <config_file>         
###########################################################################

import sys
import xlwt 
from xlwt import Workbook
import re
import ipaddress
from ciscoconfparse import CiscoConfParse
import netaddr

# Function to parse the full configuration into dictionaries/lists that we will later use for analysis. Returns a bunch of lists and dictionaries.
def parse_asa_configuration(input_raw,input_parse):
    # Set up lists and dictionaries for return purposes
    access_lists = []
    
    # Read each line of the config, looking for configuratio components that we care about
    for line in input_raw:
        
        # Identify and collect configurations for all configured access lists
        if re.match("^access-list .*",line):
            access_lists.append(line)
        
    # Return all these things. At this point we aren't being discriminate. These are a raw collections of all items.
    return access_lists

def main(config_file):
    user_source_file = config_file

    # Open the source configuration file for reading and import/parse it.
    x = open(user_source_file,'r')
    config_raw = x.readlines()
    config_parse = CiscoConfParse(config_raw) 
    x.close()

    # Send configuration off to get split up into a list for reference
    ret_access_lists = parse_asa_configuration(config_raw,config_parse)

    for x in ret_access_lists:
        print x[:-1]

    # Workbook is created
    wb = Workbook() 
      
    # add_sheet is used to create sheet. 
    sheet1 = wb.add_sheet('Rules')

    row_num = 0
    
    for x in ret_access_lists:
        tmp = x.lstrip().split(' ')
        print tmp
        #sheet1.write(row_num,0,tmp[1])
      
    wb.save('xlwt example.xls')

if __name__ == '__main__':
    main('running-config.cfg')
##    fileout=sys.stdout
##    from sys import argv, stdin
##    if len(argv) == 2:
##        config_file = argv[1]
##        main(config_file)
##
##    else:
##        print 'Please provide ASA Configuration files...'
