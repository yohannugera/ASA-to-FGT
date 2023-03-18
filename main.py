import sys

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
def parse_asa_configuration(input_raw, input_parse):
    # Set up lists and dictionaries for return purposes
    names = []
    objects = {}
    object_groups = {}
    # Read each line of the config, looking for configuratio components that we care about
    for line in input_raw:
        # Identify all staticallly configured name/IPAddress translations
        if re.match(
                "^name (([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]).*",
                line):
            names.append(line)

        # Identify and collect configurations for all configured objects
        if 'object network' in line:
            obj = input_parse.find_children_w_parents(line, '^(?! nat ?.*)')
            obj_name = (line.split()).pop(2)
            if not obj_name in objects and obj:
                objects[obj_name] = (obj)

        # Identify and collect configurations for all configured object groups
        if 'object-group network' in line:
            obj_group = input_parse.find_children_w_parents(line, '.*')
            obj_group_name = (line.split()).pop(2)
            if not obj_group_name in object_groups and obj_group:
                object_groups[obj_group_name] = (obj_group)

    return (names, objects, object_groups)
def main():
    user_source_file = "src/running-config.cfg"

    # Open the source configuration file for reading and import/parse it.
    x = open(user_source_file,'r')
    config_raw = x.readlines()
    x.close()

    config_level = indent_level(config_raw)
    config_tree = ttree_to_json(config_level)
    print(config_tree)
if __name__ == '__main__':
  main()