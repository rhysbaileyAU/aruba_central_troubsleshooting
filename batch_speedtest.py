import json
import time
import datetime
import sys
import aruba_central_troubleshooting as acts


##GLOBAL VARIABLES##
iperf_server_addr = "10.1.5.101"          
iperf_test_time = 5                             
output_dir = "/Users/rhysbailey/Documents/Code/Aruba Central/ouputs/"
credentials_dir = "/Users/rhysbailey/Documents/Code/Aruba Central/"
region = "APAC-EAST1"

###GLOBAL###
##Select Region##
acts.fn_get_api_url_for_region(region)

##Parse Command-Line Arguments
if ((len(sys.argv) > 1) and ((sys.argv[1] == "--group")or(sys.argv[1] == "--site")or(sys.argv[1] == "--ALL"))):
    testing_scope = (sys.argv[1])
else:
    acts.fn_display_expected_arguments()

##Establish Scope for Batch and create output files
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
if testing_scope == "--ALL":
    print("Running tests on ALL Virtual Controllers")
    acts.fn_get_all_iap_virtualcontrollers()
    resultsfilename = output_dir +"results_ALL_" +timestamp +".csv"
    testlogfilename = output_dir +"testlog_ALL_" +timestamp +".txt"
elif testing_scope == "--group":
    if len(sys.argv) < 3 or sys.argv[2] == 'list':
        acts.fn_list_aruba_central_groups()
    else:
        test_groupname = (sys.argv[2])
        print("This will perform tests on all Virtual Controllers in group: "+test_groupname)
        acts.fn_get_iap_virtualcontrollers_for_group(test_groupname)
        resultsfilename = output_dir +"results_group_"+test_groupname+"_" +timestamp +".csv"
        testlogfilename = output_dir +"testlog_group_"+test_groupname+"_" +timestamp +".txt"
elif testing_scope == "--site":
    if len(sys.argv) < 3 or sys.argv[2] == 'list':
        acts.fn_list_aruba_central_sites()
    else:
        test_sitename = (sys.argv[2])
        print("This will perform tests on all Virtual Controllers at site: "+test_sitename)
        acts.fn_get_iap_virtualcontrollers_for_site(test_sitename)
        resultsfilename = output_dir +"results_site_"+test_sitename+"_" +timestamp +".csv"
        testlogfilename = output_dir +"testlog_site_"+test_sitename+"_" +timestamp +".txt"
print("Results file: " +resultsfilename)
print("Test Log File: " +testlogfilename)

## Write Test Scope to Test Log File ##
with open(testlogfilename, "w") as file:
    file.write("Start of Testing Window: "+timestamp)
    file.write("\nAPs in Scope of test window: ")
    for site, ap in acts.ap_site_dictionary.items():
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
for site, ap in acts.ap_site_dictionary.items():
    ts_session_id = acts.ts_session_id
    ap_serial = ap
    if isinstance(site, str) is True:
        print("Running Speedtest on "+ap_serial +" at site " +site)
    elif isinstance(site,str) is False:
        print("Running Speedtest on "+ap_serial +" at no assigned site")
    acts.fn_get_ts_sessionid(ap_serial)                      
    acts.fn_clear_ts_session(ap_serial,ts_session_id)        
    acts.fn_exec_iperf(ap_serial,iperf_server_addr)          
    time.sleep(15)                                  
    acts.fn_clear_ts_session(ap_serial,ts_session_id)        
    acts.fn_fetch_iperf_result(ap_serial,iperf_server_addr)
    acts.fn_get_tshooting_log(ap_serial,ts_session_id)       
    acts.fn_pars_speedtest_result_json(acts.ts_output)                                
    results_json.append(acts.dict_result)
    with open(resultsfilename, "a") as resultsfile:
        resultsfile.write("\n" +acts.dict_result["Test Date"] +"," +acts.dict_result["Test Time"] +"," +acts.dict_result["Systen Name"] +"," +ap_serial +"," +acts.dict_result["Downstream(mbps)"] +"," +acts.dict_result["Upstream(mbps)"])
    resultsfile.close()
    print(ap_serial,acts.dict_result)                                         

##Format and print results
json_formatted_results = json.dumps(results_json,indent=2)
print(json_formatted_results)




    
