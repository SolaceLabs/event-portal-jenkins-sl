import glob
import json
import re

import requests

# Constants
ASYNC_API_APPLICATION_TITLE_PATTERN = r'title: "([\w\.\s]+)"'
ASYNC_API_APPLICATION_ID_PATTERN = r'x-ep-application-id: "([\w\.]+)"'
ASYNC_API_APPLICATION_VERSION_PATTERN = r'version: "([\w\.]+)"'
ASYNC_API_APPLICATION_VERSION_ID_PATTERN = r'x-ep-application-version-id: "([\w\.]+)"'
ASYNC_API_APPLICATION_VERSION_NAME_PATTERN = r'x-ep-displayname: "([\w\.\s]+)"'
ASYNC_API_APPLICATION_STATE_PATTERN = r'x-ep-state-name: "([\w\.]+)"'
ASYNC_API_APPLICATION_STATE_ID_PATTERN = r'x-ep-state-id: "([\w\.]+)"'

# Classes
class EventPortalApplication:
    lastChangeRecordId = None
    clientProfileName = None
    clientUserName = None
    clientAuthorizationGroupName = None
    def __init__(self, title, application_id, application_version, application_version_id, application_version_name, application_state, application_state_id):
        self.applicationTitle = title
        self.applicationId = application_id
        self.applicationVersion = application_version
        self.applicationVersionId = application_version_id
        self.applicationVersionName = application_version_name
        self.applicationState = application_state
        self.applicationStateId = application_state_id

    def __str__(self):
        return json.dumps(self.__dict__)

# Methods
def to_pretty_json(ugly_json):
    parsed = json.loads(ugly_json)
    pretty_json = json.dumps(parsed, indent=4)
    return pretty_json

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

def get_match(pattern, line):
    match_group = None
    match = re.match(pattern, line)
    if match:
        match_group = match.group(1)
        print(f"Match: '{match_group}'")

    return match, match_group

def get_applications_from_yaml_files():
    application_list = []
    files = glob.glob('./**/*.yaml', recursive=True)

    for file in files:
        print(file)
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
                print(line)

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


            ep_application = EventPortalApplication(application_title, application_id, application_version,
                                                    application_version_id, application_version_name, application_state, application_state_id)
            print(ep_application)
            application_list.append(ep_application)

    return application_list
