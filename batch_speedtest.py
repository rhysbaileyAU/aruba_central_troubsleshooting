import requests
import json
import time
import re
import datetime
import sys


##GLOBAL VARIABLES##
iperf_server_addr = "10.1.5.101"          
iperf_test_time = 5                             
output_dir = "/temp/"
credentials_dir = "/temp/"
region = "APAC-EAST1"


def fn_get_ts_sessionid(ap_serial):

    fn_get_tokens()          

    global ts_session_id

    url = "https://{0}".format(region_specific_url)+"/troubleshooting/v1/devices/{0}".format(ap_serial)+"/session"
    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        ts_session_id = response_json['session_id']
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_get_ts_sessionid(ap_serial)
    elif response.status_code == 404:
        ts_session_id = 0
    else:
        print("Error getting sessionID for IAP ",ap_serial,"- code: ",response," ",response.text)
        exit()
      
def fn_clear_ts_session(ap_serial,ts_session_id):
    if ts_session_id > 0:

        fn_get_tokens()

        url = "https://{0}".format(region_specific_url)+"/troubleshooting/v1/devices/{0}".format(ap_serial)+"?session_id={0}".format(ts_session_id)
        payload = {}
        headers = {
            'Authorization': 'Bearer '+api_token
        }
        response = requests.request("DELETE", url, headers=headers, data=payload)

        if response.status_code == 401:
            fn_refresh_token(api_token,refresh_token,client_id,client_secret)
            fn_clear_ts_session(ap_serial,ts_session_id)

def fn_exec_iperf(ap_serial,iperf_server_addr):
    global ts_session_id
    fn_get_tokens()

    url = "https://{0}".format(region_specific_url)+"/troubleshooting/v1/devices/{0}".format(ap_serial)

    payload = json.dumps({
        "device_type": "IAP",
        "commands": [
        {
            "command_id": 168,
            "arguments": [
            {
                "name": "Host",
                "value": iperf_server_addr
            },
            {
                "name": "Protocol",
                "value": "tcp"
            },
            {
                "name": "Options",
                "value": "include-reverse sec-to-measure {0}".format(iperf_test_time)
            }
            ]
        }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+api_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        if response_json["status"] != "QUEUED":
            print("ERROR(3) - Unable to queue troubleshooting command, please try again")
            exit()
        ts_session_id = response_json['session_id']
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_exec_iperf(ap_serial,iperf_server_addr)
    else:
        print("Error Queueing iPerf Test - code: ",response," ",response.text)
        exit()

def fn_fetch_iperf_result(ap_serial,iperf_server_addr):  
    global ts_session_id
    fn_get_tokens()               

    url = "https://{0}".format(region_specific_url)+"/troubleshooting/v1/devices/{0}".format(ap_serial)

    payload = json.dumps({
        "device_type": "IAP",
        "commands": [
        {
            "command_id": 167,
            "arguments": [
            {
                "name": "Host",
                "value": iperf_server_addr
            },
            {
                "name": "Protocol",
                "value": "tcp"
            },
            {
                "name": "Options",
                "value": "include-reverse sec-to-measure {0}".format(iperf_test_time)
            }
            ]
        }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+api_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        if response_json["status"] != "QUEUED":
            print("ERROR(6) - Unable to queue troubleshooting command, please try again")
            exit()
        ts_session_id = response_json['session_id']
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_fetch_iperf_result(ap_serial,iperf_server_addr)
    else:
        print("Error queueing collection of iPerf Test Results - code: ",response," ",response.text)
        exit()

def fn_get_tshooting_log(ap_serial,ts_session_id):      
    
    fn_get_tokens()
    
    global ts_output

    url = "https://{0}".format(region_specific_url)+"/troubleshooting/v1/devices/{0}".format(ap_serial)+"?session_id={0}".format(ts_session_id)

    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        ts_status = response_json['status']
        if ts_status == "COMPLETED":
                ts_output = response_json['output']
        else:
            time.sleep(5)
            fn_get_tshooting_log(ap_serial,ts_session_id)
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_get_tshooting_log(ap_serial,ts_session_id)
    else:
        print("Error fetching Troubleshooting Log - code: ",response," ",response.text)
        exit()

def fn_pars_speedtest_result_json(log):        
    global dict_result

    sysname = re.search(r"((([A-Z]+-)|[^!:])[A-Za-z]+-AP+[1-99]|[A-Za-z]+-L\d+-AP+[1-99])",log)
    date = re.search(r"(\d+\sJan\s\d+|\d+\sFeb\s\d+|\d+\sMar\s\d+|\d+\sApr\s\d+|\d+\sMay\s\d+|\d+\sJun\s\d+|\d+\sJul\s\d+|\d+\sAug\s\d+|\d+\sSep\s\d+|\d+\sOct\s\d+|\d+\sNov\s\d+|\d+\sDec\s\d+)",log)

    time_raw = re.search(r"Time of Execution :\w{1,3},\s\d{1,2}\s\w{3}\s\d{4}\s\d{2}:\d{2}:\d{2}",log)
    time = re.split(" ",time_raw.group(),maxsplit=7)

    upstream_raw = re.search(r"Upstream Bandwidth\(Mbps\) :+\d+.\d+",log)
    upstream = re.split(":",upstream_raw.group(),maxsplit=1)

    downstream_raw = re.search(r"Downstream bandwidth\(Mbps\) :+\d+.\d+",log)
    downstream = re.split(":",downstream_raw.group(),maxsplit=1)

    server_raw = re.search(r"Server IP :(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",log)
    server = re.split(":",server_raw.group(),maxsplit=1)

    client_raw = re.search(r"Local IP :(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",log)
    client = re.split(":",client_raw.group(),maxsplit=1)

    dict_result = {
        "Systen Name": sysname.group(),
        "Test Date": date.group(),
        "Test Time": time[7],
        "Upstream(mbps)": upstream[1],
        "Downstream(mbps)": downstream[1],
        "Server IP": server[1],
        "Client IP": client[1]
    }

def fn_refresh_token(fnc_api_token,fnc_refresh_token,fnc_client_id,fnc_client_secret):          

    global api_token                               
    global refresh_token                            

    dict_expired_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': fnc_api_token, 'refresh_token': fnc_refresh_token}
    with open(credentials_dir+"credentials.old.json", "w") as file: 
        json.dump(dict_expired_creds_out, file)     
    file.close()                                    

    url = "https://{0}".format(region_specific_url)+"/oauth2/token?client_id={0}".format(client_id)+"&client_secret={0}".format(client_secret)+"&grant_type=refresh_token&refresh_token={0}".format(refresh_token)

    payload = {}
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload)
    
    if response.status_code == 400:                            
        print("ERROR Code 400: Invalid Refresh Token - Create new Token in Aruba Central and populate credentials.json" )
        exit()
    
    response_json = json.loads(response.text)           
    api_token = response_json["access_token"]           
    refresh_token = response_json["refresh_token"]

    dict_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': api_token, 'refresh_token': refresh_token}

    with open(credentials_dir+"credentials.json", "w") as file:     
        json.dump(dict_creds_out, file)             
    file.close()

def fn_get_tokens():            

    global api_token            
    global refresh_token        
    global client_id            
    global client_secret        

    with open(credentials_dir+"credentials.json", "r") as file:     
        dict_creds_in = json.load(file)             
        api_token = dict_creds_in["api_token"]
        refresh_token = dict_creds_in["refresh_token"]
        client_id = dict_creds_in["client_id"]
        client_secret = dict_creds_in["client_secret"]
    file.close()                                        

def fn_get_all_iap_virtualcontrollers():
    global ap_site_dictionary
    
    fn_get_tokens()
    
    url = "https://{0}".format(region_specific_url)+"/monitoring/v2/aps?limit=250"

    payload = {}
    headers = {
    'Authorization': 'Bearer '+api_token
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        response_json = json.loads(response.text)
        ap_site_dictionary = {}
        for ap in range(len(response_json["aps"])):
            if response_json["aps"][ap]["status"] == "Up" and response_json["aps"][ap]["swarm_master"] == True:
                ap_site_dictionary.update({response_json["aps"][ap]["site"]:response_json["aps"][ap]["serial"]})
        print("IAP Count: ",len(ap_site_dictionary))
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_get_all_iap_virtualcontrollers()
    else:
        print("Error fetching list of IAP virtual controllers - code: ",response," ",response.text)
        exit()

def fn_get_iap_virtualcontrollers_for_group(groupname):
    global ap_site_dictionary
    
    fn_get_tokens()
    
    url = "https://{0}".format(region_specific_url)+"/monitoring/v2/aps?group={0}".format(groupname)

    payload = {}
    headers = {
    'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        ap_site_dictionary = {}

        for ap in range(len(response_json["aps"])):
            if response_json["aps"][ap]["status"] == "Up" and response_json["aps"][ap]["swarm_master"] == True:
                ap_site_dictionary.update({response_json["aps"][ap]["site"]:response_json["aps"][ap]["serial"]})
        if len(ap_site_dictionary) < 1:
            print("ERROR: No Online Virtual Controllers in Group for testing")
            exit()
        elif len(ap_site_dictionary) >= 1:
            print("IAP Count: ",len(ap_site_dictionary))
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_get_iap_virtualcontrollers_for_group(groupname)
    else:
        print("Error fetching list of IAP virtual controllers - code: ",response," ",response.text)
        exit()

def fn_get_iap_virtualcontrollers_for_site(sitename):
    global ap_site_dictionary
    
    fn_get_tokens()
    
    url = "https://{0}".format(region_specific_url)+"/monitoring/v2/aps?site={0}".format(sitename)

    payload = {}
    headers = {
    'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        ap_site_dictionary = {}
        for ap in range(len(response_json["aps"])):
            if response_json["aps"][ap]["status"] == "Up" and response_json["aps"][ap]["swarm_master"] == True:
                ap_site_dictionary.update({response_json["aps"][ap]["site"]:response_json["aps"][ap]["serial"]})
        if len(ap_site_dictionary) < 1:
            print("ERROR: No Online Virtual Controllers in Site for testing")
            exit()
        elif len(ap_site_dictionary) >= 1:
            print("IAP Count: ",len(ap_site_dictionary))
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_get_iap_virtualcontrollers_for_group(sitename)
    else:
        print("Error fetching list of IAP virtual controllers - code: ",response," ",response.text)
        exit()

def fn_list_aruba_central_sites():

    fn_get_tokens()

    url = "https://{0}".format(region_specific_url)+"/central/v2/sites?limit=500"

    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        print("Aruba Central Sites:")
        print("=====================")
        for site in range(len(response_json["sites"])):
            print(response_json["sites"][site]["site_name"])
        exit()   
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_list_aruba_central_sites()
    else:
        print("Error fetching list of Sites - code: ",response," ",response.text)
        exit()

def fn_list_aruba_central_groups():

    fn_get_tokens()

    url = "https://{0}".format(region_specific_url)+"/configuration/v2/groups?limit=100&offset=0"

    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        print("Aruba Central Groups:")
        print("=====================")
        for group in range(len(response_json["data"])):
            print(response_json["data"][group][0])
        exit()
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret)
        fn_list_aruba_central_groups()   
    else:
        print("Error fetching list of Groups - code: ",response," ",response.text)
        exit()

def fn_display_expected_arguments():
    print("Expecting Arguments:")
    print(" '--ALL' - Batch Speedtest all Virtual Controllers")
    print(" '--group <group-name> or list' - Batch Speedtest all Virtual Controllers in Group")
    print(" '--site <site-name> or list - Speed Test IAP at Site")
    exit()

def fn_get_api_url_for_region(region):
    global region_specific_url
    ## Select region URL based on region variable ##
    if region == "US-1":
        region_specific_url = "app1-apigw.central.arubanetworks.com"
    elif region == "US-2":
        region_specific_url = "app1-apigw.central.arubanetworks.com"
    elif region == "US-WEST-4":
        region_specific_url = "app1-apigw.central.arubanetworks.com"
    elif region == "EU-1":
        region_specific_url = "eu-apigw.central.arubanetworks.com"
    elif region == "EU-2":
        region_specific_url = "apigw-eucentral2.central.arubanetworks.com"
    elif region == "EU-3":
        region_specific_url = "apigw-eucentral3.central.arubanetworks.com"
    elif region == "Canada-1":
        region_specific_url = "apigw-ca.central.arubanetworks.com"
    elif region == "China-1":
        region_specific_url = "apigw.central.arubanetworks.com.cn"
    elif region == "APAC-1":
        region_specific_url = "api-ap.central.arubanetworks.com"
    elif region == "APAC-EAST1":
        region_specific_url = "apigw-apaceast.central.arubanetworks.com"
    elif region == "APAC-SOUTH1":
        region_specific_url = "apigw-apacsouth.central.arubanetworks.com"    

###GLOBAL###
##Select Region##
fn_get_api_url_for_region(region)

##Parse Command-Line Arguments
if ((len(sys.argv) > 1) and ((sys.argv[1] == "--group")or(sys.argv[1] == "--site")or(sys.argv[1] == "--ALL"))):
    testing_scope = (sys.argv[1])
else:
    fn_display_expected_arguments()

##Establish Scope for Batch and create output files
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
if testing_scope == "--ALL":
    print("Running tests on ALL Virtual Controllers")
    fn_get_all_iap_virtualcontrollers()
    resultsfilename = output_dir +"results_ALL_" +timestamp +".csv"
    testlogfilename = output_dir +"testlog_ALL_" +timestamp +".txt"
elif testing_scope == "--group":
    if len(sys.argv) < 3 or sys.argv[2] == 'list':
        fn_list_aruba_central_groups()
    else:
        test_groupname = (sys.argv[2])
        print("This will perform tests on all Virtual Controllers in group: "+test_groupname)
        fn_get_iap_virtualcontrollers_for_group(test_groupname)
        resultsfilename = output_dir +"results_group_"+test_groupname+"_" +timestamp +".csv"
        testlogfilename = output_dir +"testlog_group_"+test_groupname+"_" +timestamp +".txt"
elif testing_scope == "--site":
    if len(sys.argv) < 3 or sys.argv[2] == 'list':
        fn_list_aruba_central_sites()
    else:
        test_sitename = (sys.argv[2])
        print("This will perform tests on all Virtual Controllers at site: "+test_sitename)
        fn_get_iap_virtualcontrollers_for_site(test_sitename)
        resultsfilename = output_dir +"results_site_"+test_sitename+"_" +timestamp +".csv"
        testlogfilename = output_dir +"testlog_site_"+test_sitename+"_" +timestamp +".txt"
print("Results file: " +resultsfilename)
print("Test Log File: " +testlogfilename)

## Write Test Scope to Test Log File ##
with open(testlogfilename, "w") as file:
    file.write("Start of Testing Window: "+timestamp)
    file.write("\nAPs in Scope of test window: ")
    for site, ap in ap_site_dictionary.items():
        if isinstance(site, str) is True:
            file.write("\n" +ap +":" +site )
        elif isinstance(site,str) is False:
            file.write("\n" +ap +":" +"No Assigned Site" )
file.close()
with open(resultsfilename, "w") as file:
    file.write("\nDate,Time,SystemName,SerialNumber,downstream_mbps,upstream_mbps")
file.close()

#Loop through Batch scope and run speedtest functions sequentially
results_json = []                          
for site, ap in ap_site_dictionary.items():
    ap_serial = ap
    if isinstance(site, str) is True:
        print("Running Speedtest on "+ap_serial +" at site " +site)
    elif isinstance(site,str) is False:
        print("Running Speedtest on "+ap_serial +" at no assigned site")
    fn_get_ts_sessionid(ap_serial)                      
    fn_clear_ts_session(ap_serial,ts_session_id)        
    fn_exec_iperf(ap_serial,iperf_server_addr)          
    time.sleep(15)                                  
    fn_clear_ts_session(ap_serial,ts_session_id)        
    fn_fetch_iperf_result(ap_serial,iperf_server_addr)
    fn_get_tshooting_log(ap_serial,ts_session_id)       
    fn_pars_speedtest_result_json(ts_output)                                
    results_json.append(dict_result)
    with open(resultsfilename, "a") as resultsfile:
        resultsfile.write("\n" +dict_result["Test Date"] +"," +dict_result["Test Time"] +"," +dict_result["Systen Name"] +"," +ap_serial +"," +dict_result["Downstream(mbps)"] +"," +dict_result["Upstream(mbps)"])
    resultsfile.close()
    print(ap_serial,dict_result)                                         

##Format and print results
json_formatted_results = json.dumps(results_json,indent=2)
print(json_formatted_results)




    
