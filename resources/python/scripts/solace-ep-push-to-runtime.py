import argparse
import json
import logging
import sys
import time
import http.client as http_client

import requests
import urllib3

import solace_ep_integration as sepi

# logging
logger = logging.getLogger(__name__)

def validate_application_version(token, application):
    url = f"https://api.solace.cloud/api/v2/architecture/applicationVersions?pageSize=100&pageNumber=1&applicationIds={application.applicationId}&ids={application.applicationVersionId}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }
    logger.info(
        f"Validating Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Validation for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(response.json()))

    return response.text

def validate_application_client_profile(token, application):
    url = f"https://api.solace.cloud/api/v2/architecture/designer/configuration/solaceClientProfileNames?pageSize=20&pageNumber=1&entityIds={application.applicationVersionId}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    logger.info(f"Getting client profile for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting client profile for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(response.json()))

    return response.text

def validate_application_authorization_group(token, broker_id, application):
    url = f"https://api.solace.cloud/api/v2/architecture/designer/configuration/solaceAuthorizationGroups?pageSize=100&pageNumber=1&eventBrokerIds={broker_id}&entityIds={application.applicationId}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }
    logger.info(url)
    logger.info(
        f"Getting client authorization group for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} - BrokerId: {broker_id}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting client client Authorization group for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(response.json()))

    return response.text

def create_application_authorization_group(token, broker_id, application):
    url = "https://api.solace.cloud/api/v2/architecture/designer/configuration/solaceAuthorizationGroups"

    payload = {
        "action": "deploy",
        "applicationVersionId": f"{application.applicationVersionId}",
        "eventBrokerId": f"{broker_id}",

        "value": {
            "clientUsername": f"{application.clientUserName}",
            "authorizationGroupName": f"{application.clientAuthorizationGroupName}"
        },
        "configurationTypeId": "solaceAuthorizationGroup",
        "contextType": "EVENT_BROKER",
        "contextId": f"{broker_id}",
        "entityId": f"{application.applicationId}"
    }

    headers = {
        "accept": "application/json;charset=UTF-8",
        "content-type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200 and response.status_code != 201:
        raise Exception(f"Creating client client Authorization group for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(response.json()))

    return response.text

def get_deployment_status(token, broker_id, application):
    url = f"https://api.solace.cloud/api/v2/architecture/runtimeManagement/applications/{application.applicationId}/configurationPushJobs?pageSize=20&pageNumber=1&changeRecordIds={application.lastChangeRecordId}"

    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {token}"
    }
    logger.info(
        f"Getting deployment status for application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} to Runtime Broker with Id: {broker_id}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Getting deployment status for Application: {application.applicationTitle} ChangeRecordId: {application.lastChangeRecordId} failed! - error details: " + str(response.json()))

    return response.text

def deploy_application_to_runtime(token, broker_id, application):
    url = "https://api.solace.cloud/api/v2/architecture/runtimeManagement/applicationDeployments"

    payload = {
        "action": "deploy",
        "applicationVersionId": f"{application.applicationVersionId}",
        "eventBrokerId": f"{broker_id}"
    }
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "authorization": f"Bearer {token}"
    }
    logger.info(f"Pushing application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} to Runtime Broker with Id: {broker_id}")
    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code != 200:
        raise Exception(f"Pushing application: {application.applicationTitle} to Runtime Broker with Id: {broker_id} failed! - error details: " + str(response.json()))

    json_response = json.loads(response.text)

    data = json_response.get('data')
    if data is not None:
        application.lastChangeRecordId = data.get('changeRecordId')

    print(f"changeRecordId: {application.lastChangeRecordId}")

    return response.text


def deploy_single_application_to_runtime(token, broker_id, app):
    json_response = deploy_application_to_runtime(token, broker_id, app)
    pretty_json = sepi.to_pretty_json(json_response)
    print(pretty_json)

def get_deployment_status_single_application_to_runtime(token, broker_id, app):
    status = 'in_progress'

    while status == 'in_progress':
        txt_response = get_deployment_status(token, broker_id, app)
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

    for app in application_list:
        txt_response = validate_application_version(token, app)
        pretty_json = sepi.to_pretty_json(txt_response)
        print(pretty_json)

        json_response = json.loads(txt_response)
        data = json_response.get('data')
        if data is not None:
            if len(data) == 0:
                raise Exception(
                    f"Application: {app.applicationTitle}, version: {app.applicationVersion} - {app.applicationVersionName}, state: {app.applicationState} does not Exists on Event Portal Designer!. Aborting!")

    for app in application_list:
        txt_response = validate_application_client_profile(token, app)
        pretty_json = sepi.to_pretty_json(txt_response)
        print(pretty_json)

        json_response = json.loads(txt_response)
        data = json_response.get('data')
        if data is not None:
            if len(data) == 0:
                raise Exception(
                    f"Application: {app.applicationTitle}, version: {app.applicationVersion} - {app.applicationVersionName}, state: {app.applicationState} does not have a Client Profile! Create one before continue. Aborting!")


    for app in application_list:
        txt_response = validate_application_authorization_group(token, broker_id, app)
        pretty_json = sepi.to_pretty_json(txt_response)
        print(pretty_json)

        json_response = json.loads(txt_response)
        data = json_response.get('data')
        if data is not None:
            if len(data) == 0:
                logger.warning(
                    f"Application: {app.applicationTitle}, version: {app.applicationVersion} - {app.applicationVersionName}, state: {app.applicationState} does not have an Authorization Group (OAuth or LDAP)!.")

                logger.warning("Deploying the App to the Authorization Group...")
                deploy_single_application_to_runtime(token, broker_id, app)
                get_deployment_status_single_application_to_runtime(token, broker_id, app)

                logger.warning("Creating the Authorization Group...")
                txt_response = create_application_authorization_group(token, broker_id, app)
                pretty_json = sepi.to_pretty_json(txt_response)
                print(pretty_json)



    for app in application_list:
        deploy_single_application_to_runtime(token, broker_id, app)

    #logger.info(f"Waiting 3 seconds before querying for deployment status...")
    #time.sleep(3)

    for app in application_list:
        get_deployment_status_single_application_to_runtime(token, broker_id, app)
    return None


def get_application_list_by_name(token, application_name, application):
    url = f"https://api.solace.cloud/api/v2/architecture/applications?pageSize=100&pageNumber=1&name={application_name}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    logger.info(
        f"Getting application list by name: {application_name}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting Application List by name: {application_name} failed! - error details: " + str(response.json()))

    json_response = json.loads(response.text)
    data = json_response.get('data')
    if data is not None:
        for record in data:
            application.applicationTitle = record.get('name')
            application.applicationId = record.get('id')
            print(f"Application retrieved: {application}")

    return None

def get_application_version_by_name(token, version_name, application):
    url = f"https://api.solace.cloud/api/v2/architecture/applicationVersions?pageSize=100&pageNumber=1&applicationIds={application.applicationId}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    logger.info(f"Getting application versions for Application: {application.applicationTitle}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting application versions for application: {application.applicationTitle} failed! - error details: " + str(response.json()))

    json_response = json.loads(response.text)
    data = json_response.get('data')
    if data is not None:
        for record in data:
            version = record.get('version')
            if version == version_name:
                application.applicationVersion = version
                application.applicationVersionId = record.get('id')
                application.applicationVersionName = record.get('displayName')
                application.applicationStateId = record.get('stateId')
                if application.applicationStateId == '1':
                    application.applicationState = 'DRAFT'
                elif application.applicationStateId == '2':
                    application.applicationState = 'RELEASED'
                else:
                    application.applicationState = 'X'

    print(f"Application retrieved: {application}")

    if application.applicationVersion is None:
        raise Exception(f"Could find an application versions for application: {application.applicationTitle} with version name: {version_name} failed! - error details: " + str(response.json()))

    return None

# Main
def main(argv):

    # Parse parameters
    parser = argparse.ArgumentParser(description="Push Applications to Broker Runtime")
    parser.add_argument("-token", type=str, required=True, help="Event Portal Auth Token")
    parser.add_argument("-brokerId", type=str, required=True, help="Runtime broker ID")
    parser.add_argument("-action", type=str, required=True, help="deploy/undeploy")

    parser.add_argument("-applicationName", type=str, required=True, help="Application Name (case sensitive)")
    parser.add_argument("-applicationVersion", type=str, required=True, help="Application Version (case sensitive)")
    parser.add_argument("-clientUsername", type=str, required=True, help="Client username")
    parser.add_argument("-clientAuthorizationGroupName", type=str, required=True, help="Client Authorization group")

    args = parser.parse_args()

    requested_app = sepi.EventPortalApplication(None, None, None,
                                                None, None, None, None)



    get_application_list_by_name(args.token, args.applicationName, requested_app)
    get_application_version_by_name(args.token, args.applicationVersion, requested_app)

    application_list = []

    #scan current workspace to get all the yaml files and read them
    #application_list = sepi.get_applications_from_yaml_files()

    #i = 1
    #for app in application_list:
    #    app.clientUserName = args.clientUsername + "_" + "{:03d}".format(i)
    #    app.clientAuthorizationGroupName = args.clientAuthorizationGroupName  + "_" + "{:03d}".format(i)
    #    i = i +1

    print(requested_app)
    application_list.append(requested_app)

    # deploy applications to runtime broker
    deploy_applications_to_runtime(args.token, args.brokerId, application_list)

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