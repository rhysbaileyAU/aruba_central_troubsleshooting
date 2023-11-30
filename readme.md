Batch SpeedTest Tool

Description:
Uses Aruba Central API to perform iPerf tests across multiple IAPs.


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




