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

def main():
    user_source_file = "running-config.cfg"

    # Open the source configuration file for reading and import/parse it.
    x = open(user_source_file,'r')
    config_raw = x.readlines()
    x.close()

    config_level = indent_level(config_raw)
    config_tree = ttree_to_json(config_level)

    

if __name__ == '__main__':
  main()
