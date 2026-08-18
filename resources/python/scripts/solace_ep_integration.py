import glob
import json
import logging
import re
from typing import Any
from urllib.parse import quote, quote_plus

import requests

# Constants
ASYNC_API_APPLICATION_TITLE_PATTERN = r'"title": "([\w\.\s]+)"'
ASYNC_API_APPLICATION_ID_PATTERN = r'"x-ep-application-id": "([\w\.]+)"'
ASYNC_API_APPLICATION_VERSION_PATTERN = r'"version": "([\w\.]+)"'
ASYNC_API_APPLICATION_VERSION_ID_PATTERN = r'"x-ep-application-version-id": "([\w\.]+)"'
ASYNC_API_APPLICATION_VERSION_NAME_PATTERN = r'"x-ep-displayname": "([\w\.\s]+)"'
ASYNC_API_APPLICATION_STATE_PATTERN = r'"x-ep-state-name": "([\w\.]+)"'
ASYNC_API_APPLICATION_STATE_ID_PATTERN = r'"x-ep-state-id": "([\w\.]+)"'

# logging
logger = logging.getLogger(__name__)

# Classes
class EventPortalApplication:
    lastChangeRecordId = None
    clientProfileName = None
    clientUserName = None
    clientAuthorizationGroupName = None
    clientAuthorizationGroupId = None

    def __init__(self, title : str, application_id: str, application_version: str, application_version_id: str, application_version_name: str, application_state: str, application_state_id: str):
        self.applicationTitle: str = title
        self.applicationId: str = application_id
        self.applicationVersion: str = application_version
        self.applicationVersionId: str = application_version_id
        self.applicationVersionName: str = application_version_name
        self.applicationState: str = application_state
        self.applicationStateId: str = application_state_id
        self.sharedAuthorizationGroup:str = None
        self.sharedACLProfile:str = None
        self.declaredProducedEventVersionIds: list[str] = []
        self.declaredConsumedEventVersionIds: list[str] = []
        self.declaredConsumedEventVersionIdsWithConsumers: list[str] = []
        self.producedEventTopics: list[dict[str, Any]] = []
        self.consumedEventTopics: list[dict[str, Any]] = []
        self.applicationType: str = None


    def __str__(self):
        return json.dumps(self.__dict__)

# Methods
def to_pretty_json(ugly_json):
    parsed = json.loads(ugly_json)
    pretty_json = json.dumps(parsed, indent=4)
    return pretty_json

def get_match(pattern, line):
    match_group = None
    match = re.match(pattern, line)
    if match:
        match_group = match.group(1)
        # print(f"Match: '{match_group}'")

    return match, match_group

def get_applications_from_json_files():
    application_list = []
    files = glob.glob('./**/*.json', recursive=True)

    for file in files:
        # print(file)
        with open(file, 'r') as o_file:
            application_title = None
            application_id = None
            application_version = None
            application_version_id = None
            application_version_name = None
            application_state = None
            application_state_id = None

            for line in o_file:
                # Removes trailing newline characters
                line = line.strip()
                # print(line)

                match, match_group = get_match(ASYNC_API_APPLICATION_TITLE_PATTERN, line)
                if match:
                    application_title = match_group

                match, match_group = get_match(ASYNC_API_APPLICATION_ID_PATTERN, line)
                if match:
                    application_id = match_group

                match, match_group = get_match(ASYNC_API_APPLICATION_VERSION_PATTERN, line)
                if match:
                    application_version = match_group

                match, match_group = get_match(ASYNC_API_APPLICATION_VERSION_ID_PATTERN, line)
                if match:
                    application_version_id = match_group

                match, match_group = get_match(ASYNC_API_APPLICATION_VERSION_NAME_PATTERN, line)
                if match:
                    application_version_name = match_group

                match, match_group = get_match(ASYNC_API_APPLICATION_STATE_PATTERN, line)
                if match:
                    application_state = match_group

                match, match_group = get_match(ASYNC_API_APPLICATION_STATE_ID_PATTERN, line)
                if match:
                    application_state_id = match_group


            if application_title is not None and application_version is not None:
                ep_application = EventPortalApplication(application_title, application_id, application_version,
                                                    application_version_id, application_version_name, application_state, application_state_id)
            # print(ep_application)
                application_list.append(ep_application)

    return application_list

def get_modeled_event_meshes(token):
    url = "https://api.solace.cloud/api/v2/architecture/about/eventMeshes?pageSize=100&pageNumber=1&sort=name%3Aasc"

    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        raise Exception("Getting modeled event meshes failed: " + str(response.json()))
    return response.text

def get_messaging_services(token):
    url = "https://api.solace.cloud/api/v2/architecture/messagingServices?pageSize=100&pageNumber=1&sort=name%3Aasc"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}"    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception("Getting list of messaging services failed: " + str(response.json()))
    return response.text

def get_application_list_by_name(token: str, application_name: str, application: EventPortalApplication) -> None:
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

    logger.info(f"Application retrieved: \n{to_pretty_json(response.text)}")
    json_response = json.loads(response.text)
    data = json_response.get('data')
    if data is not None:
        for record in data:
            application.applicationTitle = record.get('name')
            application.applicationId = record.get('id')
            application.applicationType = record.get('applicationType')

            custom_attributes = record.get('customAttributes', [])
            for attribute in custom_attributes:
                attribute_name = attribute.get('customAttributeDefinitionName')
                attribute_value = attribute.get('value')
                if attribute_name == "AuthorizationGroup":
                    application.sharedAuthorizationGroup = attribute_value

    print(f"Application retrieved: {application}")
    return None

def get_application_list_by_shared_authorization_group(token : str, shared_authorization_group : str):
    url = f"https://api.solace.cloud/api/v2/architecture/applications?pageSize=100&pageNumber=1&customAttributes=AuthorizationGroup%3D%3D{shared_authorization_group}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    logger.info(
        f"Getting application list by custom attribute AuthorizationGroup: {shared_authorization_group}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting application list by custom attribute AuthorizationGroup: {shared_authorization_group} failed! - error details: " + str(response.json()))

    return response.text

def get_application_versions_list_by_application_and_version_ids(token : str, application_ids : list[str], app_version_ids : list[str]):
    application_ids_list = '&applicationIds='.join(application_ids)
    application_versions_ids_list = '&ids='.join(app_version_ids)
    url = f"https://api.solace.cloud/api/v2/architecture/applicationVersions?pageSize=100&pageNumber=1&applicationIds={application_ids_list}&ids={application_versions_ids_list}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    logger.info(
        f"Getting application version list by ids - AppIds: {application_ids_list}, VersionIds: {application_versions_ids_list}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting application version list by ids - AppIds: {application_ids_list}, VersionIds: {application_versions_ids_list} failed! - error details: " + str(response.json()))

    return response.text

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

    logger.info(f"Application version retrieved: \n{to_pretty_json(response.text)}")
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

                # Get topics from direct consumers
                consumers = record.get('consumers',[])
                for consumer in consumers:
                    consumer_type = consumer.get('consumerType')
                    if consumer_type != "eventQueue":
                        subscriptions = consumer.get('subscriptions')
                        for subscription in subscriptions:
                            full_topic = subscription.get('value')

                            attracted_event_version_ids = subscription.get('attractedEventVersionIds')
                            if not attracted_event_version_ids is None:
                                for attracted_event_version_id in attracted_event_version_ids:
                                    event_version_id = attracted_event_version_id.get('eventVersionId')
                                    application.declaredConsumedEventVersionIdsWithConsumers.append(event_version_id)

                            if not full_topic is None:
                                application.consumedEventTopics.append({"eventIds": [ attracted_event_version_ids ], "topic": full_topic})

                # Get topics from published events
                application.declaredProducedEventVersionIds = record.get('declaredProducedEventVersionIds')
                application.declaredConsumedEventVersionIds = record.get('declaredConsumedEventVersionIds')

    if not application.declaredProducedEventVersionIds is None:
        for produced_event in application.declaredProducedEventVersionIds:
            json_response_txt = get_event_by_version(token, produced_event)
            json_response = json.loads(json_response_txt)
            event = json_response.get('data')
            delivery_descriptor = event.get('deliveryDescriptor')
            address = delivery_descriptor.get('address')
            if not address is None:
                address_levels = address.get('addressLevels')
                topic = []
                for address_level in address_levels:
                    name = address_level.get('name')
                    add_type = address_level.get('addressLevelType')
                    if add_type == 'literal':
                        topic.append(name)
                    elif add_type == 'variable':
                        topic.append('*')

                full_topic = '/'.join(topic)
                application.producedEventTopics.append( {"eventIds": [ produced_event ], "topic": full_topic} )

    logger.info(f"Application retrieved: \n{to_pretty_json(str(application))}")
    return None

def get_event_by_version(token, event_version : str) -> str:
    url = f"https://api.solace.cloud/api/v2/architecture/eventVersions/{event_version}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    logger.info(f"Getting event versions with id: {event_version}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting event version  with id: {event_version} failed! - error details: " + str(response.json()))

    logger.info(response.text)
    return response.text

def get_broker_id_by_name(token, broker_name):
    response = get_messaging_services(token)

    broker_id = None

    json_response = json.loads(response)
    data = json_response.get('data')
    if data is not None:
        for record in data:
            t_broker_name = record.get('name')
            if t_broker_name == broker_name:
                broker_id = record.get('id')

    print(f"BrokerId retrieved: {broker_id}")
    return broker_id

def get_broker_service_id_by_name(token, broker_name):
    url = f"https://api.solace.cloud/api/v2/missionControl/eventBrokerServices?customAttributes=name%3D%3D{broker_name}&pageNumber=1&pageSize=100"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}"
    }

    logger.info(f"Getting Broker Service Id by Name: {broker_name}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting Broker Service Id by Name: {broker_name} failed! - error details: " + str(response.json()))

    broker_service_id = None

    json_response = json.loads(response.text)
    data = json_response.get('data')
    if data is not None:
        for record in data:
            broker_service_id = record.get('id')

    print(f"BrokerServiceId retrieved: {broker_service_id}")
    return broker_service_id

def get_application_version(token, application):
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

'''
Validate that the application with that version id exists in EP designer
'''
def validate_application_version(token, application):
    txt_response = get_application_version(token, application)
    pretty_json = to_pretty_json(txt_response)
    print(pretty_json)

    json_response = json.loads(txt_response)
    data = json_response.get('data')
    if data is not None:
        if len(data) == 0:
            raise Exception(
                f"Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} does not Exists on Event Portal Designer!. Aborting!")

    return None

def get_application_async_api_specification(token, application):
    url = f"https://api.solace.cloud/api/v2/architecture/applicationVersions/{application.applicationVersionId}/asyncApi?format=json&showVersioning=true&includedExtensions=all&asyncApiVersion=2.5.0"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}"
    }

    logger.info(
        f"Getting AsyncAPI specification for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Getting AsyncAPI specification for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(response.json()))

    print(response.text)
    return response.text

def get_application_client_profile(token, application):
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

def create_application_client_profile(token, broker_service_id, client_profile_name):
    url = f"https://api.solace.cloud/api/v2/missionControl/eventBrokerServices/{broker_service_id}/clientProfiles"

    payload = {
        "name": f"{client_profile_name}",
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {token}"
    }

    logger.info(f"Creating client profile with name: {client_profile_name}")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200 and response.status_code != 202 and response.status_code != 400:
        raise Exception(f"Creation of client profile with name: {client_profile_name} failed! - error details: " + str(response.json()))

    print(response.text)

def get_application_authorization_group(token, broker_id, application):
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

def delete_application_client_username_reference(token, broker_id, application):
    url = f"https://api.solace.cloud/api/v2/architecture/designer/configuration/solaceClientUsernameReferences?pageSize=100&pageNumber=1&entityIds={application.applicationId}&eventBrokerIds={broker_id}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }
    logger.info(url)
    logger.info(f"Getting client username reference configuration for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} - BrokerId: {broker_id}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Getting client username reference configuration for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(response.json()))

    client_username_reference_id = None
    json_response = json.loads(response.text)
    data = json_response.get('data')
    if data is not None:
        if len(data) == 0:
            logger.info(f"Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} does not have a Client Username reference!")
            return None
        else:
            record = data[0]
            if record is not None:
                client_username_reference_id = record.get('id')


    if not client_username_reference_id is None:
        url = f"https://api.solace.cloud/api/v2/architecture/designer/configuration/solaceClientUsernameReferences/{client_username_reference_id}"

        logger.info(url)
        logger.info(
            f"Deleting client username reference configuration for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} - BrokerId: {broker_id}")
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise Exception(
                f"Deleting client username reference configuration for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(
                    response.json()))

    return None

def create_application_client_username_reference(token, broker_id, application):
    url = "https://api.solace.cloud/api/v2/architecture/designer/configuration/solaceClientUsernameReferences"

    payload = {
        "value": {
            "clientUsername": f"{application.clientUserName}"
        },
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
        raise Exception(f"Creating client user name reference for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! - error details: " + str(response.json()))

    return response.text

def delete_application_authorization_group(token, broker_id, application):
    if application.clientAuthorizationGroupId is None:
        return "{}"

    url = f"https://api.solace.cloud/api/v2/architecture/designer/configuration/solaceAuthorizationGroups/{application.clientAuthorizationGroupId}"

    headers = {
        "accept": "application/json;charset=UTF-8",
        "content-type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    response = requests.delete(url, headers=headers)
    if response.status_code != 204:
        raise Exception(f"Deleting client client Authorization group for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} failed! ")

    return "{}"


def get_preview_deploy_application_to_runtime(token, broker_id, action, application_version_id):
    url = "https://api.solace.cloud/api/v2/architecture/runtimeManagement/applicationDeploymentPreviews"

    payload = {
        "action": f"{action}",
        "applicationVersionId": f"{application_version_id}",
        "eventBrokerId": f"{broker_id}"
    }
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "authorization": f"Bearer {token}"
    }
    logger.info(f"Getting deployment preview for applicationVersionId: {application_version_id} to Runtime Broker with Id: {broker_id}")
    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code != 200:
        raise Exception(f"Getting deployment preview for applicationVersionId: {application_version_id} to Runtime Broker with Id: {broker_id} failed! - error details: " + str(response.json()))

    return response.text

def deploy_application_to_runtime(token: str, broker_id: str, action: str, application: EventPortalApplication) -> str:
    url = "https://api.solace.cloud/api/v2/architecture/runtimeManagement/applicationDeployments"

    payload = {
        "action": f"{action}",
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
    logger.info(response.text)
    if response.status_code != 200:
        raise Exception(f"Pushing application: {application.applicationTitle} to Runtime Broker with Id: {broker_id} failed! - error details: " + str(response.json()))

    json_response = json.loads(response.text)

    data = json_response.get('data')
    if data is not None:
        application.lastChangeRecordId = data.get('changeRecordId')
        print(f"changeRecordId: {application.lastChangeRecordId}")

        url = f"https://api.solace.cloud/api/v2/architecture/runtimeManagement/applications/{application.applicationId}/configurationPushJobs?pageSize=100&pageNumber=1&changeRecordIds={application.lastChangeRecordId}"

        response = requests.get(url, headers=headers)
        logger.info(response.text)
        if response.status_code != 200:
            raise Exception(f"Getting the list of push jobs for Application: {application.applicationTitle} to Runtime Broker with Id: {broker_id} failed! - error details: " + str(response.json()))

        job_id: str = ""
        json_response = json.loads(response.text)
        data = json_response.get('data')
        if data is not None:
            for record in data:
                job_id = record.get('id')

        logger.info(f"Push Job Id: {job_id}")

        if job_id != "":
            url = f"https://api.solace.cloud/api/v2/architecture/runtimeManagement/applicationConfigurationPushJobs/{job_id}/run"

            response = requests.post(url, headers=headers)

            if response.status_code != 200:
                raise Exception(f"Pushing JobId: {job_id} to run for application: {application.applicationTitle} to Runtime Broker with Id: {broker_id} failed! - error details: " + str(response.json()))

    logger.info(response.text)
    return response.text

def get_application_deployment_status(token, broker_id, application):
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

def get_broker_authorization_group_details(semp_token : str, broker_hostname : str, broker_msg_vpn : str, authorization_group : str):
    url = f"https://{broker_hostname}/SEMP/v2/config/msgVpns/{broker_msg_vpn}/authorizationGroups/{authorization_group}"

    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {semp_token}"
    }
    logger.info(f"Getting details for authorization group: '{authorization_group}' from msgVpn: '{broker_msg_vpn}'")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Getting details for authorization group: '{authorization_group}' from msgVpn: '{broker_msg_vpn}' failed! - error details: " + str(
                response.json()))

    return response.text

def add_publish_topic_exception(semp_token : str, broker_hostname : str, broker_msg_vpn : str, acl_profile : str, topic_exception : str):
    url = f"https://{broker_hostname}/SEMP/v2/config/msgVpns/{broker_msg_vpn}/aclProfiles/{acl_profile}/publishTopicExceptions"

    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {semp_token}"
    }
    payload = {
        "publishTopicExceptionSyntax": "smf",
        "publishTopicException": f"{topic_exception}"
    }

    logger.info(f"Adding publishTopicExceptions to ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}'")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200 and response.status_code != 400:
        raise Exception(
            f"Adding publishTopicExceptions to ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}' failed! - error details: " + str(response.json()))

    return response.text

def remove_publish_topic_exception(semp_token : str, broker_hostname : str, broker_msg_vpn : str, acl_profile : str, topic_exception : str):
    url = f"https://{broker_hostname}/SEMP/v2/config/msgVpns/{broker_msg_vpn}/aclProfiles/{acl_profile}/publishTopicExceptions/smf,{quote_plus(topic_exception)}"

    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {semp_token}"
    }

    logger.info(f"Removing publishTopicExceptions from ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}'")
    response = requests.delete(url, headers=headers)
    if response.status_code != 200 and response.status_code != 400:
        raise Exception(
            f"Removing publishTopicExceptions from ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}' failed! - error details: " + str(response.json()))

    return response.text

def add_subscribe_topic_exception(semp_token : str, broker_hostname : str, broker_msg_vpn : str, acl_profile : str, topic_exception : str):
    url = f"https://{broker_hostname}/SEMP/v2/config/msgVpns/{broker_msg_vpn}/aclProfiles/{acl_profile}/subscribeTopicExceptions"

    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {semp_token}"
    }
    payload = {
        "subscribeTopicExceptionSyntax": "smf",
        "subscribeTopicException": f"{topic_exception}"
    }

    logger.info(f"Adding subscribeTopicException to ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}'")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200 and response.status_code != 400:
        raise Exception(
            f"Adding subscribeTopicException to ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}' failed! - error details: " + str(response.json()))

    return response.text

def remove_subscribe_topic_exception(semp_token : str, broker_hostname : str, broker_msg_vpn : str, acl_profile : str, topic_exception : str):
    url = f"https://{broker_hostname}/SEMP/v2/config/msgVpns/{broker_msg_vpn}/aclProfiles/{acl_profile}/subscribeTopicExceptions/smf,{quote_plus(topic_exception)}"

    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {semp_token}"
    }

    logger.info(f"Removing subscribeTopicException from ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}'")
    response = requests.delete(url, headers=headers)
    if response.status_code != 200 and response.status_code != 400:
        raise Exception(
            f"Removing subscribeTopicException from ACL profile: '{acl_profile}', msgVpn: '{broker_msg_vpn}', Exception: '{topic_exception}' failed! - error details: " + str(response.json()))

    return response.text