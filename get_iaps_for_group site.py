import aruba_central_troubleshooting as acts
import pprint

region = "APAC-EAST1"
credentials_file = "/Users/rhysbailey/Documents/Code/Aruba Central/credentials.json"
sitename = "You Yangs"

ap_site_dictionary = acts.fn_get_iap_virtualcontrollers_for_site(credentials_file,region,sitename)
pprint.pprint(ap_site_dictionary)

