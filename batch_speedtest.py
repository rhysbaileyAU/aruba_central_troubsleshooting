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


def fn_get_ts_sessionid(ap_serial,debug):

    fn_get_tokens()          

    global ts_session_id

    url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)+"/session"
    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        ts_session_id = response_json['session_id']
    elif response.status_code == 401:
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_get_ts_sessionid(ap_serial,debug)
    elif response.status_code == 404:
        ts_session_id = 0
    else:
        print("Error getting sessionID for IAP ",ap_serial,"- code: ",response," ",response.text)
        exit()
      
def fn_clear_ts_session(ap_serial,ts_session_id,debug):
    if ts_session_id > 0:

        fn_get_tokens()

        url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)+"?session_id={0}".format(ts_session_id)
        payload = {}
        headers = {
            'Authorization': 'Bearer '+api_token
        }
        response = requests.request("DELETE", url, headers=headers, data=payload)

        if response.status_code == 401:
            if debug == 1:
                print("401 Unauthorized - Refreshing Tokens")
            fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
            fn_clear_ts_session(ap_serial,ts_session_id,debug)

def fn_exec_iperf(ap_serial,iperf_server_addr,debug):
    global ts_session_id
    fn_get_tokens()

    url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)

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
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_exec_iperf(ap_serial,iperf_server_addr,debug)
    else:
        print("Error Queueing iPerf Test - code: ",response," ",response.text)
        exit()

def fn_fetch_iperf_result(ap_serial,iperf_server_addr,debug):  
    global ts_session_id
    fn_get_tokens()               

    url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)

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
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_fetch_iperf_result(ap_serial,iperf_server_addr,debug)
    else:
        print("Error queueing collection of iPerf Test Results - code: ",response," ",response.text)
        exit()

def fn_get_tshooting_log(ap_serial,ts_session_id,debug):      
    
    fn_get_tokens()
    
    global ts_output

    url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)+"?session_id={0}".format(ts_session_id)

    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        ts_status = response_json['status']
        #ts_hostname = response_json['hostname']
        #ts_serial = response_json['serial']
        if ts_status == "COMPLETED":
                ts_output = response_json['output']
        else:
            time.sleep(5)
            fn_get_tshooting_log(ap_serial,ts_session_id,debug)
    elif response.status_code == 401:
        if debug == 1:
            print("401 Unauthorized - Refreshing Tokens")
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_get_tshooting_log(ap_serial,ts_session_id,debug)
    else:
        print("Error fetching Troubleshooting Log - code: ",response," ",response.text)
        exit()

def fn_pars_speedtest_result_json(log):        
    global dict_result

    sysname = re.search(r"((([A-Z]+-)|[^!:])[A-Za-z]+-AP+[1-99]|[A-Za-z]+-L\d+-AP+[1-99])",log)
    date = re.search(r"(\d+\sOct\s\d+|\d+\sNov\s\d+)",log)

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

def fn_refresh_token(fnc_api_token,fnc_refresh_token,fnc_client_id,fnc_client_secret,debug):          

    global api_token                               
    global refresh_token                            

    #Create dictionary for expired token credential details then write to 'credentials.old.json'
    dict_expired_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': fnc_api_token, 'refresh_token': fnc_refresh_token}
    with open(credentials_dir+"credentials.old.json", "w") as file: 
        json.dump(dict_expired_creds_out, file)     
    file.close()                                    

    url = "https://apigw-apaceast.central.arubanetworks.com/oauth2/token?client_id={0}".format(client_id)+"&client_secret={0}".format(client_secret)+"&grant_type=refresh_token&refresh_token={0}".format(refresh_token)

    payload = {}
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload)
    
    if response.status_code == 400:                                     #Error detection for an invalid refresh token
        print("ERROR Code 400: Invalid Refresh Token - Create new Token in Aruba Central and populate credentials.json" )
        exit()
    
    response_json = json.loads(response.text)           #Load response into JSON
    api_token = response_json["access_token"]           #Read returned API token into varibale 'api_token'
    refresh_token = response_json["refresh_token"]      #Read returned refresh token into variable 'refresh_token'

    #Create dictionary for updated credential details
    dict_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': api_token, 'refresh_token': refresh_token}

    #Output refreshed credentials to file 'credentials.json'
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

        #Define script variables from file
        api_token = dict_creds_in["api_token"]
        refresh_token = dict_creds_in["refresh_token"]
        client_id = dict_creds_in["client_id"]
        client_secret = dict_creds_in["client_secret"]
    file.close()                                        

def fn_get_all_iap_virtualcontrollers():
    global ap_site_dictionary
    
    fn_get_tokens()
    
    url = "https://apigw-apaceast.central.arubanetworks.com/monitoring/v2/aps?limit=250"

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
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_get_all_iap_virtualcontrollers()
    else:
        print("Error fetching list of IAP virtual controllers - code: ",response," ",response.text)
        exit()

def fn_get_iap_virtualcontrollers_for_group(groupname):
    global ap_site_dictionary
    
    fn_get_tokens()
    
    url = "https://apigw-apaceast.central.arubanetworks.com/monitoring/v2/aps?group={0}".format(groupname)

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
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_get_iap_virtualcontrollers_for_group(groupname)
    else:
        print("Error fetching list of IAP virtual controllers - code: ",response," ",response.text)
        exit()

###GLOBAL###

##Parse Command-Line Arguments
if len(sys.argv) == 1:
    print("ERROR - must specify test scope of '--group <group-name>' OR 'ALL'")
    exit() 
elif len(sys.argv) > 1:
    testing_scope = (sys.argv[1])

##Establish Scope for Batch and create output files
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
if testing_scope == "ALL":
    print("Running tests on ALL Virtual Controllers")
    fn_get_all_iap_virtualcontrollers()
    resultsfilename = output_dir +"results_ALL_" +timestamp +".csv"
    testlogfilename = output_dir +"testlog_ALL_" +timestamp +".txt"
elif testing_scope == "--group":
    testing_group = (sys.argv[2])
    print("This will perform tests on all Virtual Controllers in group: "+testing_group)
    fn_get_iap_virtualcontrollers_for_group(testing_group)
    resultsfilename = output_dir +"results_group_"+testing_group+"_" +timestamp +".csv"
    testlogfilename = output_dir +"testlog_group_"+testing_group+"_" +timestamp +".txt"
print("Results file: " +resultsfilename)
print("Test Log File: " +testlogfilename)

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
    fn_get_ts_sessionid(ap_serial,debug)                      
    fn_clear_ts_session(ap_serial,ts_session_id,debug)        
    fn_exec_iperf(ap_serial,iperf_server_addr,debug)          
    time.sleep(15)                                  
    fn_clear_ts_session(ap_serial,ts_session_id,debug)        
    fn_fetch_iperf_result(ap_serial,iperf_server_addr,debug)
    fn_get_tshooting_log(ap_serial,ts_session_id,debug)       
    fn_pars_speedtest_result_json(ts_output)                                
    results_json.append(dict_result)
    with open(resultsfilename, "a") as resultsfile:
        resultsfile.write("\n" +dict_result["Test Date"] +"," +dict_result["Test Time"] +"," +dict_result["Systen Name"] +"," +ap_serial +"," +dict_result["Downstream(mbps)"] +"," +dict_result["Upstream(mbps)"])
    resultsfile.close()
    print(ap_serial,dict_result)                                         

##Format and print results
json_formatted_results = json.dumps(results_json,indent=2)
print(json_formatted_results)




    
