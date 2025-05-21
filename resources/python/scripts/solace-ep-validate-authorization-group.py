import argparse
import json
import logging
import sys
import time
import http.client as http_client

import requests
import urllib3

import solace_ep_integration as sepi

# Constants
WAIT_TIME_IN_SECONDS = 1
ACTION_DEPLOY = 'deploy'
ACTION_UNDEPLOY = 'undeploy'

# logging
logger = logging.getLogger(__name__)




def does_application_has_authorization_group(token, broker_id, application):
    txt_response = sepi.get_application_authorization_group(token, broker_id, application)
    pretty_json = sepi.to_pretty_json(txt_response)
    print(pretty_json)

    json_response = json.loads(txt_response)
    data = json_response.get('data')
    if data is not None:
        if len(data) == 0:
            logger.warning(
                f"Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} does not have an Authorization Group (OAuth or LDAP)!.")

            return False
    return True

# Main
def main(argv):

    # Parse parameters
    parser = argparse.ArgumentParser(description="Push Applications to Broker Runtime")
    parser.add_argument("-token", type=str, required=True, help="Event Portal Auth Token")
    parser.add_argument("-brokerName", type=str, required=True, help="Runtime broker Name")
    parser.add_argument("-applicationName", type=str, required=True, help="Application Name (case sensitive)")
    parser.add_argument("-applicationVersion", type=str, required=True, help="Application Version (case sensitive)")

    args = parser.parse_args()

    print(f"Arguments: Token: ***, brokerName: {args.brokerName}, " +
          f"applicationName: {args.applicationName}, applicationVersion: {args.applicationVersion}")

    requested_app = sepi.EventPortalApplication(None, None, None,
                                                None, None, None, None)

    # Get Broker ID
    broker_id = sepi.get_broker_id_by_name(args.token, args.brokerName)
    if broker_id is None:
        raise Exception(f"Could not find an broker with name: {args.brokerName}")

    # Get Application by Name
    sepi.get_application_list_by_name(args.token, args.applicationName, requested_app)
    if requested_app.applicationTitle is None or requested_app.applicationId is None:
        raise Exception(f"Could not find an application with name: {args.applicationName}")

    # Get Application Version by Name
    sepi.get_application_version_by_name(args.token, args.applicationVersion, requested_app)
    if requested_app.applicationVersion is None:
        raise Exception(f"Could not find an application versions for application with name: {requested_app.applicationTitle} and version name: {args.applicationVersion}")

    print(requested_app)

    if does_application_has_authorization_group(args.token, broker_id, requested_app):
        sys.exit(0)
    else:
        sys.exit(3)

if __name__ == "__main__":
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig(level=logging.INFO)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    # disable warning messages about https connection
    urllib3.disable_warnings()
    main(sys.argv[1:])