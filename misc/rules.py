file1 = open('acls.log','r')
for line in file1:
    if line[0] != " ":
        print line[:-1]
