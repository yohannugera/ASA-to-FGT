# ASA-to-FGT

Cisco ASA to Fortigate firewall conversion scripting are included here. I envisioned to be a three-step process.

## Step 01 - Parsing ASA configuration to an Excel
[Code Repo](https://github.com/yohannugera/ASA-to-FGT/tree/master/ASA-to-Excel)

1. To run the code, place the configuration file in the same folder as the code 'main.py'. Let's say "running-config.txt" is our ASA configuration file.

2. Then, open CMD and type run the code

	python main.py running-config.txt
	
3. You should get files on your working directory

	- running-config.xlsx - Parsed configuration in an Excel
	- running-config.unparsed - Lines that couldn't be parsed by the code (limitations)

4. Once you have it, you're ready for the next-step.

## Step 02 - Optimizing Parsed Rule-Base
[Code Repo](https://github.com/yohannugera/ASA-to-FGT/tree/master/Amendments-to-Excel)

1. Copy the Parsed configuration file (.xlsx) to the folder "Amendments-to-Excel"

2. I have two codes here

	- main-route_checkup.py - Code that'll review source/destination objects and determine applicable interfaces that needs to be assigned in policy
	- main-policy_optimize.py - Code that'll review each source/destination/service tuple and identify if they can be combined or not
	
3. Once you run each script, you'll see the configuration file getting new sheets. Once you run,

	- main-route_checkup.py - Sheet named "ACLs-route_check" appended with determined source/destination interfaces
	- main-policy_optimize.py - Sheet named "ACLs-policy_optimize" appended with bundled in policies (not coded yet)
	
4. You can review them and determine whether to accept the code output (sheets) and amend the "ACLs" sheet or whether to keep the rule-base unaltered.

5. Once you done that, you're good to go to the next-step.

## Step 03 - Optimizing Parsed Rule-Base
[Code Repo](https://github.com/yohannugera/ASA-to-FGT/tree/master/Excel-to-FMG)

1. Copy the configuration file (with or without amendments)

2. Prepare the "environment.cfg" file. File should include following JSON data

	{
		"username":"<Administrator User with JSON RW Access>",
		"password":"<Administrator Password>",
		"ip":"<IP of FortiManager>",
		"adom":"<ADOM>",
		"region":"<Folder you wish to have the package>",
		"package_name":"<Package Name>",
		"device":"<Model Device Name>",
		"config_file":"<Configuration Filename>"
	}
	
3. Once you have "environment.cfg" and configuration file in the same folder as "main.py", run-it.