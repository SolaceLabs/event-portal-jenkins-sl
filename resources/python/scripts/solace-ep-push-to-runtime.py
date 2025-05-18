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

'''
Validate that the application with that version id exists in EP designer
'''
def validate_application_version(token, application):
    txt_response = sepi.get_application_version(token, application)
    pretty_json = sepi.to_pretty_json(txt_response)
    print(pretty_json)

    json_response = json.loads(txt_response)
    data = json_response.get('data')
    if data is not None:
        if len(data) == 0:
            raise Exception(
                f"Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} does not Exists on Event Portal Designer!. Aborting!")

    return None

def validate_application_client_profile(token, application):
    txt_response = sepi.get_application_client_profile(token, application)
    pretty_json = sepi.to_pretty_json(txt_response)
    print(pretty_json)

    json_response = json.loads(txt_response)
    data = json_response.get('data')
    if data is not None:
        if len(data) == 0:
            raise Exception(
                f"Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} does not have a Client Profile! Create one before continue. Aborting!")
    return None

def validate_application_authorization_group(token, broker_id, application):
    txt_response = sepi.get_application_authorization_group(token, broker_id, application)
    pretty_json = sepi.to_pretty_json(txt_response)
    print(pretty_json)

    json_response = json.loads(txt_response)
    data = json_response.get('data')
    if data is not None:
        if len(data) == 0:
            logger.warning(
                f"Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} does not have an Authorization Group (OAuth or LDAP)!.")

            logger.warning("Deploying the App to the Authorization Group...")
            deploy_undeploy_application_to_runtime(token, broker_id, ACTION_DEPLOY, application)
            get_deployment_status_single_application_to_runtime(token, broker_id, application)

            logger.warning("Creating the Authorization Group...")
            txt_response = sepi.create_application_authorization_group(token, broker_id, application)
            pretty_json = sepi.to_pretty_json(txt_response)
            print(pretty_json)

    return None


def deploy_undeploy_application_to_runtime(token, broker_id, action, app):
    json_response = sepi.deploy_application_to_runtime(token, broker_id, action, app)
    pretty_json = sepi.to_pretty_json(json_response)
    print(pretty_json)

def get_deployment_status_single_application_to_runtime(token, broker_id, app):
    status = 'in_progress'

    while status == 'in_progress':
        txt_response = sepi.get_application_deployment_status(token, broker_id, app)
        pretty_json = sepi.to_pretty_json(txt_response)
        print(pretty_json)

        json_response = json.loads(txt_response)
        data = json_response.get('data')
        if data is not None:
            if len(data) == 0:
                raise Exception(
                    f"Cannot find Deployment for Application: {app.applicationTitle}, version: {app.applicationVersion} - {app.applicationVersionName}, state: {app.applicationState}!. Aborting!")
            record = data[0]
            if record is not None:
                status = record.get('status')

        if status == 'in_progress':
            logger.info(f"Waiting 500 milliseconds before querying for deployment status...")
            time.sleep(500 / 1000)

        if status == 'error':
            raise Exception(
                f"Deployment for application: {app.applicationTitle}, version: {app.applicationVersion} - {app.applicationVersionName}, state: {app.applicationState} to Runtime Broker with Id: {broker_id} failed!")

    return None

def deploy_applications_to_runtime(token, broker_id, application_list):
    # Validate that the application with that version id exists in EP designer
    for app in application_list:
        validate_application_version(token, app)

    for app in application_list:
        validate_application_client_profile(token, app)

    for app in application_list:
        validate_application_authorization_group(token, broker_id, app)

    for app in application_list:
        deploy_undeploy_application_to_runtime(token, broker_id, ACTION_DEPLOY, app)

    logger.info(f"Waiting {WAIT_TIME_IN_SECONDS} second(s) before querying for deployment status...")
    time.sleep(WAIT_TIME_IN_SECONDS)

    for app in application_list:
        get_deployment_status_single_application_to_runtime(token, broker_id, app)

    return None

def undeploy_applications_to_runtime(token, broker_id, application_list):
    # Validate that the application with that version id exists in EP designer
    for app in application_list:
        validate_application_version(token, app)

    for app in application_list:
        deploy_undeploy_application_to_runtime(token, broker_id, ACTION_UNDEPLOY, app)

    logger.info(f"Waiting {WAIT_TIME_IN_SECONDS} second(s) before querying for undeployment status...")
    time.sleep(WAIT_TIME_IN_SECONDS)

    for app in application_list:
        get_deployment_status_single_application_to_runtime(token, broker_id, app)

    return None

# Main
def main(argv):

    # Parse parameters
    parser = argparse.ArgumentParser(description="Push Applications to Broker Runtime")
    parser.add_argument("-token", type=str, required=True, help="Event Portal Auth Token")
    parser.add_argument("-brokerName", type=str, required=True, help="Runtime broker Name")
    parser.add_argument("-action", type=str, required=True, help="deploy/undeploy")

    parser.add_argument("-applicationName", type=str, required=True, help="Application Name (case sensitive)")
    parser.add_argument("-applicationVersion", type=str, required=True, help="Application Version (case sensitive)")
    parser.add_argument("-clientUsername", type=str, required=True, help="Client username")
    parser.add_argument("-clientAuthorizationGroupName", type=str, required=True, help="Client Authorization group")

    args = parser.parse_args()

    print(f"Arguments: {args}")

    requested_app = sepi.EventPortalApplication(None, None, None,
                                                None, None, None, None)

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

    #scan current workspace to get all the yaml files and read them
    #application_list = sepi.get_applications_from_yaml_files()

    #i = 1
    #for app in application_list:
    #    app.clientUserName = args.clientUsername + "_" + "{:03d}".format(i)
    #    app.clientAuthorizationGroupName = args.clientAuthorizationGroupName  + "_" + "{:03d}".format(i)
    #    i = i +1

    application_list = [requested_app]

    if args.action == ACTION_DEPLOY:
        # deploy applications to runtime broker
        deploy_applications_to_runtime(args.token, broker_id, application_list)
    elif args.action == ACTION_UNDEPLOY:
        undeploy_applications_to_runtime(args.token, broker_id, application_list)

    return None


if __name__ == "__main__":
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig(level=logging.INFO)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    # disable warning messages about https connection
    urllib3.disable_warnings()
    main(sys.argv[1:])