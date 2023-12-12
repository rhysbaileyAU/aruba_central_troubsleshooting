import aruba_central_troubleshooting as acts
import pprint

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"

ap_site_dictionary = acts.fn_get_all_iap_virtualcontrollers(credentials_file,region)
pprint.pprint(ap_site_dictionary)

