import aruba_central_troubleshooting as acts

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"

refresh_token_output = acts.fn_refresh_token(region,credentials_file)
pre_creds = refresh_token_output[0]
post_creds = refresh_token_output[1]

print("Current:",pre_creds)
print("Update:",post_creds)



