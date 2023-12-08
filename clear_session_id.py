import aruba_central_troubleshooting as acts

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"
ap_serial = "CNHVJSSJDC"


ts_session_id = acts.fn_get_ts_sessionid(credentials_file,region,ap_serial)
print(ts_session_id)
acts.fn_clear_ts_session(credentials_file,region,ap_serial,ts_session_id)
