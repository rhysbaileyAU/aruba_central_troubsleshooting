import aruba_central_troubleshooting as acts
import pprint
import json

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"
ap_serial = "CNHVJSSJDC"
iperf_server_address = "10.1.5.101"
iperf_test_time = 5

ts_session_id = acts.fn_get_ts_sessionid(credentials_file,region,ap_serial)
print("Existing Session ID is ",ts_session_id)
acts.fn_clear_ts_session(credentials_file,region,ap_serial,ts_session_id)
print("Clearing Session ID ",ts_session_id)
ts_session_id = acts.fn_exec_iperf(credentials_file,region,ap_serial,iperf_server_address,iperf_test_time)
print("Successfully Queued iPerf test on "+ap_serial)
print(ts_session_id)
acts.fn_clear_ts_session(credentials_file,region,ap_serial,ts_session_id)
print("Clearing Session ID ",ts_session_id)
ts_session_id = acts.fn_fetch_iperf_result(credentials_file,region,ap_serial,iperf_server_address,iperf_test_time)
print("Sent command to collect iperf results")
print(ts_session_id)
ts_output = acts.fn_get_tshooting_log(credentials_file,region,ap_serial,ts_session_id)
print(ts_output)
speedtest_result_json = acts.fn_pars_speedtest_result_json(ts_output)
pprint.pprint(speedtest_result_json)
