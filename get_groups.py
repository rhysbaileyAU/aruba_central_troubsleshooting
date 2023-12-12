import aruba_central_troubleshooting as acts
import pprint

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"

site_list = acts.fn_list_aruba_central_groups(credentials_file,region)
pprint.pprint(site_list)

