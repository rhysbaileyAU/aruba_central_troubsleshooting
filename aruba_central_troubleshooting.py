import requests
import json
import time
import re



iperf_server_addr = "10.1.5.101"          
iperf_test_time = 5                             
output_dir = "/Users/rhysbailey/Documents/Code/Aruba Central/ouputs/"
credentials_dir = "/Users/rhysbailey/Documents/Code/Aruba Central/"
#region = "APAC-EAST1"


def fn_get_ts_sessionid(credentials_file,region,ap_serial):

    api_token = (fn_get_tokens(credentials_file)["api_token"])
    region_specific_url = fn_get_api_url_for_region(region)         

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
        fn_refresh_token(region,credentials_file)
        fn_get_ts_sessionid(credentials_file,region,ap_serial)
    elif response.status_code == 404:
        ts_session_id = 0
    else:
        print("Error getting sessionID for IAP ",ap_serial,"- code: ",response," ",response.text)
        exit()
    return ts_session_id
      
def fn_clear_ts_session(credentials_file,region,ap_serial,ts_session_id):
    if ts_session_id > 0:
        api_token = (fn_get_tokens(credentials_file)["api_token"])
        region_specific_url = fn_get_api_url_for_region(region)    

        url = "https://{0}".format(region_specific_url)+"/troubleshooting/v1/devices/{0}".format(ap_serial)+"?session_id={0}".format(ts_session_id)
        payload = {}
        headers = {
            'Authorization': 'Bearer '+api_token
        }
        response = requests.request("DELETE", url, headers=headers, data=payload)

        if response.status_code == 401:
            fn_refresh_token(region,credentials_file)
            fn_clear_ts_session(credentials_file,region,ap_serial,ts_session_id)

def fn_exec_iperf(credentials_file,region,ap_serial,iperf_server_addr,iperf_test_time):
    
    api_token = (fn_get_tokens(credentials_file)["api_token"])
    region_specific_url = fn_get_api_url_for_region(region)

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
        fn_refresh_token(region,credentials_file)
        fn_exec_iperf(credentials_file,region,ap_serial,iperf_server_addr,iperf_test_time)
    else:
        print("Error Queueing iPerf Test - code: ",response," ",response.text)
        exit()
    return ts_session_id

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

def fn_refresh_token(region,credentials_file):
        
    pre_api_token = (fn_get_tokens(credentials_file)["api_token"])
    pre_refresh_token = (fn_get_tokens(credentials_file)["refresh_token"])
    client_id = (fn_get_tokens(credentials_file)["client_id"])
    client_secret = (fn_get_tokens(credentials_file)["client_secret"])
    region_specific_url = fn_get_api_url_for_region(region)
    dict_expired_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': pre_api_token, 'refresh_token': pre_refresh_token}
    
    url = "https://{0}".format(region_specific_url)+"/oauth2/token?client_id={0}".format(client_id)+"&client_secret={0}".format(client_secret)+"&grant_type=refresh_token&refresh_token={0}".format(pre_refresh_token)

    payload = {}
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 400:                            
        print("ERROR Code 400: Invalid Refresh Token - Create new Token in Aruba Central and populate credentials.json" )
        exit()
    
    response_json = json.loads(response.text)           
    post_api_token = response_json["access_token"]           
    post_refresh_token = response_json["refresh_token"]

    print(pre_api_token)
    print(post_api_token)

    if post_api_token != pre_api_token:
        print("Dong the thing")
        dict_expired_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': pre_api_token, 'refresh_token': pre_refresh_token}
        with open(credentials_file+".old", "w") as file: 
            json.dump(dict_expired_creds_out, file)     
        file.close()

        dict_creds_out = {'client_id': client_id, 'client_secret': client_secret, 'api_token': post_api_token, 'refresh_token': post_refresh_token}
        with open(credentials_file, "w") as file:     
            json.dump(dict_creds_out, file)             
        file.close()

    output = [dict_expired_creds_out,dict_expired_creds_out]
    return output

def fn_get_tokens(credentials_file):            
    with open(credentials_file, "r") as file:     
        dict_credentials = json.load(file)             
    file.close()
    return dict_credentials                                        

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
    return region_specific_url    






    
