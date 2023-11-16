import requests
import json
import time
import re
import datetime



##GLOBAL VARIABLES##
groupname = "HeadOffice-WiFi"                   #Aruba Central Group from which to draw Test devices (IAP Virtual controllers)                               #Time to wait to allow iperf test to complete
iperf_server_addr = "10.1.5.101"                #Address of iPerf3 server
iperf_test_time = 5                             #Seconds to run the iperf test
debug = 0                                       #Turn on debug visibility (0=disabled, 1=enabled)


def fn_get_ts_sessionid(ap_serial,debug):

    fn_get_tokens()          

    global ts_session_id

    if debug == 1: 
        print("Get current troubleshooting ID for IAP "+ap_serial)
        print("API Token: ",api_token)

    url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)+"/session"
    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        if debug == 1:
            print("Function - fn_get_ts_sessionid")
            print("URL:",url)
            print("Response:",response.text) 
        else:
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

        if debug == 1: 
            print("Clear current troubleshooting ID for IAP "+ap_serial)

        url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)+"?session_id={0}".format(ts_session_id)
        payload = {}
        headers = {
            'Authorization': 'Bearer '+api_token
        }
        response = requests.request("DELETE", url, headers=headers, data=payload)

        if response.status_code == 200:
            if debug == 1:
                print("Troubleshooting session ID ",ts_session_id," Cleared Successfully on ",ap_serial)
        elif response.status_code == 401:
            if debug == 1:
                print("401 Unauthorized - Refreshing Tokens")
            fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
            fn_clear_ts_session(ap_serial,ts_session_id,debug)
    else:
        if debug == 1: 
             print("No Troubleshooting ID Found")


def fn_exec_iperf(ap_serial,iperf_server_addr,debug):
    global ts_session_id
    fn_get_tokens()

    if debug == 1:   
        print("3. Start troubleshooting session for IAP "+ap_serial)

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
        if debug == 1: 
            print("Command has been triggered - SessionID=",ts_session_id)
    elif response.status_code == 401:
        if debug == 1:
            print("401 Unauthorized - Refreshing Tokens")
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_exec_iperf(ap_serial,iperf_server_addr,debug)
    else:
        print("Error Queueing iPerf Test - code: ",response," ",response.text)
        exit()

def fn_fetch_iperf_result(ap_serial,iperf_server_addr,debug):  
    global ts_session_id
    fn_get_tokens()               
    if debug == 1: 
        print("6. Start troubleshooting session for IAP "+ap_serial)

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
        if debug == 1: 
            print("Troubleshooting sessionID=",ts_session_id)
    elif response.status_code == 401:
        if debug == 1:
            print("401 Unauthorized - Refreshing Tokens")
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_fetch_iperf_result(ap_serial,iperf_server_addr,debug)
    else:
        print("Error queueing collection of iPerf Test Results - code: ",response," ",response.text)
        exit()


def fn_get_tshooting_log(ap_serial,ts_session_id,debug):      
    
    fn_get_tokens()
    
    global ts_output

    if debug == 1: 
        print("7. Get troubleshooting Output for IAP "+ap_serial)
    url = "https://apigw-apaceast.central.arubanetworks.com/troubleshooting/v1/devices/{0}".format(ap_serial)+"?session_id={0}".format(ts_session_id)

    payload = {}
    headers = {
        'Authorization': 'Bearer '+api_token
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        ts_hostname = response_json['hostname']
        ts_serial = response_json['serial']
        ts_output = response_json['output']
        if debug == 1:
            print("")
            print("")
            print(ts_hostname, "("+ts_serial+")")
            print(ts_output)
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

    sysname = re.search(r"([A-Za-z]+-AP+[1-99]|[A-Za-z]+-L\d+-AP+[1-99])",log)
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
    with open("credentials.old.json", "w") as file: 
        json.dump(dict_expired_creds_out, file)     
    file.close()                                    

    if debug == 1:                                      
        print("old_api_token: ",fnc_api_token)
        print("old_refresh_token: ",fnc_refresh_token)
        print("ClientID: ",fnc_client_id)
        print("Client Secret: ",fnc_client_secret)

    url = "https://apigw-apaceast.central.arubanetworks.com/oauth2/token?client_id={0}".format(client_id)+"&client_secret={0}".format(client_secret)+"&grant_type=refresh_token&refresh_token={0}".format(refresh_token)

    payload = {}
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload)
    
    if response.status_code == 400:                                     #Error detection for an invalid refresh token
        print("ERROR Code 400: Invalid Refresh Token - Create new Token in Aruba Central and populate credentials.json" )
        exit()
    
    if debug == 1:
        print(response)
        print(response.text)

    response_json = json.loads(response.text)           #Load response into JSON
    api_token = response_json["access_token"]           #Read returned API token into varibale 'api_token'
    refresh_token = response_json["refresh_token"]      #Read returned refresh token into variable 'refresh_token'


    if debug == 1:
        print("new_api_token: ",api_token)
        print("new_refresh_token: ",refresh_token)

    #Create dictionary for updated credential details
    dict_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': api_token, 'refresh_token': refresh_token}

    #Output refreshed credentials to file 'credentials.json'
    with open("credentials.json", "w") as file:     
        json.dump(dict_creds_out, file)             
    file.close()


def fn_get_tokens():            

    global api_token            
    global refresh_token        
    global client_id            
    global client_secret        

    with open("credentials.json", "r") as file:     
        dict_creds_in = json.load(file)             

        if debug == 1:
            print("Import from File:")
            print(dict_creds_in)


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
        if debug == 1:
                print("401 Unauthorized - Refreshing Tokens")
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
        print("IAP Count: ",len(ap_site_dictionary))
    elif response.status_code == 401:
        if debug == 1:
                print("401 Unauthorized - Refreshing Tokens")
        fn_refresh_token(api_token,refresh_token,client_id,client_secret,debug)
        fn_get_iap_virtualcontrollers_for_group(groupname)
    else:
        print("Error fetching list of IAP virtual controllers - code: ",response," ",response.text)
        exit()

###GLOBAL###

##Run functions for test

fn_get_all_iap_virtualcontrollers()
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
resultsfilename = "./results_ALL_" +timestamp +".csv"
testlogfilename = "testlog_ALL_" +timestamp +".txt"
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


results_json = []                          
for site, ap in ap_site_dictionary.items():
    ap_serial = ap
    site_being_tested = site
    print("Running Speedtest on "+ap_serial +" at site " +site_being_tested)
    fn_get_ts_sessionid(ap_serial,debug)                      
    fn_clear_ts_session(ap_serial,ts_session_id,debug)        
    fn_exec_iperf(ap_serial,iperf_server_addr,debug)          
    time.sleep(15)                                  
    fn_clear_ts_session(ap_serial,ts_session_id,debug)        
    fn_fetch_iperf_result(ap_serial,iperf_server_addr,debug)
    time.sleep(5) 
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




    
