import aruba_central_troubleshooting as acts

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"
ap_serial = "CNHVJSSJDC"
iperf_server_address = "10.1.5.101"
iperf_test_time = 5

ts_session_id = acts.fn_exec_iperf(credentials_file,region,ap_serial,iperf_server_address,iperf_test_time)
print(ts_session_id)