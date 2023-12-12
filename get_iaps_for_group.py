import aruba_central_troubleshooting as acts
import pprint

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"
group = "Branch-WiFi"

ap_site_dictionary = acts.fn_get_iap_virtualcontrollers_for_group(credentials_file,region,group)
pprint.pprint(ap_site_dictionary)

