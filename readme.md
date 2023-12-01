# Aruba Central Batch SpeedTest Script #

Description:
Uses Aruba Central API to perform iPerf on IAP Virtual Controllers.


## Version 1.0.1 ##
Usage:
1. Generate API Token in Aruba Central and populate API credentials into 'credentials.json' (see sample)
2. Edit python global variables at top of file
    - iperf_server_addr = "(address of iperf server)"          
    - iperf_test_time = 5   (seconds to run iperf test)                           
    - output_dir = "(directory to put output files)"  eg: "/temp/"  (Absolute Path)
    - credentials_dir = "directory containing 'credentials.json'" eg: "/temp/"
3. Run Script with arguments:                 
    'python3 batch_speedtest.py ALL' - Run speedtest on all discovered Virtual controllers within Aruba Central Account, or

    'python3 batch_speedtest.py --group <groupname>' - Run speedtest on discovered Virtual controllers within the named group

Limitations:
- Aruba Central APAC-EAST cluster only

## Version 1.0.2 ##
Impromvements:
- Added support for for different Aruba Central Regions using global variable.
- Added support to target a particular site
- Added support to query available Group or site names
- Command Line argument error checking

Usage:
1. Generate API Token in Aruba Central and populate API credentials into 'credentials.json' (see sample)
2. Edit variables at top of file
    - iperf_server_addr = "(address of iperf server)"          
    - iperf_test_time = 5   (seconds to run iperf test)                           
    - output_dir = "(directory to put output files)"  eg: "/temp/"  (Absolute Path)
    - credentials_dir = "directory containing 'credentials.json'" eg: "/temp/"
    - region = "APAC-EAST1" (Aruba Central Region \[US-1,US-2,US-WEST-4,EU-1,EU-2,EU-3,Canada-1,China-1,APAC-1,APAC-EAST1,APAC-SOUTH1\])
3. Run Script with arguments:                 
    'python3 batch_speedtest.py arg1 arg2 

    Available Arguments:
    - '--ALL' - Batch Speedtest all Virtual Controllers"
    - '--group <group-name> or list' - Batch Speedtest all Virtual Controllers in Group"
    - '--site <site-name> or list - Speed Test IAP at Site"

    Examples:
   
    python3 batch_speedtest.py --ALL   <--- Speedtest All Virtual controllers discovered in Central Account
   
    python3 batch_speedtest.py --site list    <----- List all sites in Aruba Central Account (Same applies for '--group')
   
    python3 batch_speedtest.py --site 'site_name'  <---- run speedtet on all virtual controllers at a site (Same applies for '--group')


