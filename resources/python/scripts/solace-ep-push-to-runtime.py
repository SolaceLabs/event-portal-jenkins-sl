import argparse
import json
import logging
import sys
import time
import http.client as http_client


import urllib3

import solace_ep_integration as sepi

# Constants
WAIT_TIME_IN_SECONDS = 1
ACTION_DEPLOY = 'deploy'
ACTION_UNDEPLOY = 'undeploy'

# logging
logger = logging.getLogger(__name__)

def write_application_async_api_specification(token, application):
    txt_response = sepi.get_application_async_api_specification(token, application)
    pretty_json = sepi.to_pretty_json(txt_response)
    print(pretty_json)

    async_api_file = f"{application.applicationTitle}_v{application.applicationVersion}.json"
    async_api_file = async_api_file.replace(" ", "_")

    logger.info(
        f"Writing AsyncAPI specification for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} to file: {async_api_file}")
    with open(async_api_file, "w") as file:
        file.write(pretty_json)

    return None

def validate_application_client_profile(token, broker_service_id, application):
    txt_response = sepi.get_application_client_profile(token, application)
    pretty_json = sepi.to_pretty_json(txt_response)
    print(pretty_json)

    client_profile_name = None
    json_response = json.loads(txt_response)
    data = json_response.get('data')
    if data is not None:
        if len(data) == 0:
            raise Exception(
                f"Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} does not have a Client Profile! Create one in Event Portal Designer before continue. Aborting!")
        else:
            record = data[0]
            if record is not None:
                client_profile_name = record.get('identifier')

    sepi.create_application_client_profile(token, broker_service_id, client_profile_name)
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

            # Application does not have and authorization group defined
            # check if it have configured a shared 'AuthorizationGroup' in the custom Attributes
            if application.sharedAuthorizationGroup is None:
                logger.warning("Creating the Authorization Group...")
                txt_response = sepi.create_application_authorization_group(token, broker_id, application)
            else:
               # create a reference to an existing client username
               logger.warning("Deleting existing ClientUsername reference (if exists)...")
               sepi.delete_application_client_username_reference(token, broker_id, application)
               logger.warning("Creating a ClientUsername reference...")
               txt_response = sepi.create_application_client_username_reference(token, broker_id, application)

            pretty_json = sepi.to_pretty_json(txt_response)
            print(pretty_json)

    if not application.sharedAuthorizationGroup is None:
        #
        # Get Authorization Group - ACL Name
        # Get ACL details
        pass

    return None


def deploy_undeploy_application_to_runtime(token, broker_id, action, app):
    json_response = sepi.deploy_application_to_runtime(token, broker_id, action, app)
    pretty_json = sepi.to_pretty_json(json_response)
    print(pretty_json)

def deploy_undeploy_application_to_runtime_preview(token, broker_id, action, application):
    txt_response = sepi.get_preview_deploy_application_to_runtime(token, broker_id, action, application.applicationVersionId)
    txt_response = sepi.to_pretty_json(txt_response)
    print(txt_response)
    json_response = json.loads(txt_response)
    data = json_response.get('data')
    existing = data.get('existing')

    txt_response = json.dumps(existing, indent=4, sort_keys=True)

    async_api_file = f"{application.applicationTitle}_v{application.applicationVersion}_broker.json"
    async_api_file = async_api_file.replace(" ", "_")

    logger.info(f"Writing Broker existing objects for Application: {application.applicationTitle}, version: {application.applicationVersion} - {application.applicationVersionName}, state: {application.applicationState} to file: {async_api_file}")
    with open(async_api_file, "w") as file:
        file.write(txt_response)

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

def deploy_applications_to_runtime(token, broker_service_id, broker_id, application_list):
    # Validate that the application with that version id exists in EP designer
    for app in application_list:
        sepi.validate_application_version(token, app)

    for app in application_list:
        validate_application_client_profile(token, broker_service_id, app)

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
        sepi.validate_application_version(token, app)

    for app in application_list:
        txt_response = sepi.get_application_authorization_group(token, broker_id, app)
        pretty_json = sepi.to_pretty_json(txt_response)
        print(pretty_json)

        json_response = json.loads(txt_response)
        data = json_response.get('data')
        if data is not None:
            if len(data) > 0:
                record = data[0]
                if record is not None:
                    client_authorization_group_id = record.get('id')
                    app.clientAuthorizationGroupId = client_authorization_group_id

    # delete the application group
    for app in application_list:
        txt_response = sepi.delete_application_authorization_group(token, broker_id, app)
        pretty_json = sepi.to_pretty_json(txt_response)
        print(pretty_json)

    # push the application group changes to the broker
    for app in application_list:
        deploy_undeploy_application_to_runtime(token, broker_id, ACTION_DEPLOY, app)

    logger.info(f"Waiting {WAIT_TIME_IN_SECONDS} second(s) before querying for update app status...")
    time.sleep(WAIT_TIME_IN_SECONDS)

    for app in application_list:
        get_deployment_status_single_application_to_runtime(token, broker_id, app)

    for app in application_list:
        deploy_undeploy_application_to_runtime(token, broker_id, ACTION_UNDEPLOY, app)

    logger.info(f"Waiting {WAIT_TIME_IN_SECONDS} second(s) before querying for undeployment status...")
    time.sleep(WAIT_TIME_IN_SECONDS)

    for app in application_list:
        get_deployment_status_single_application_to_runtime(token, broker_id, app)

    return None

def update_acl_for_shared_apps(ep_token : str, broker_id : str, semp_token : str, broker_hostname: str, broker_msg_vpn: str, application_list, action : str):
    # Validate that the application with that version id exists in EP designer
    for app in application_list:
        update_acl_for_shared_app(ep_token, broker_id, semp_token, broker_hostname, broker_msg_vpn, app, action)

def update_acl_for_shared_app(ep_token : str, broker_id : str, semp_token : str, broker_hostname: str, broker_msg_vpn: str, application : sepi.EventPortalApplication, action : str) -> None:
    # Validate that the application uses 'Authorization Group' custom attribute
    if application.sharedAuthorizationGroup is None:
        logger.info("Regular application with unique AuthorizationGroup")
        return

    logger.info("MicroService - application with shared AuthorizationGroup")

    txt_response = sepi.get_broker_authorization_group_details(semp_token, broker_hostname, broker_msg_vpn, application.sharedAuthorizationGroup)
    pretty_json = sepi.to_pretty_json(txt_response)
    logger.info(pretty_json)

    json_response = json.loads(txt_response)
    data = json_response.get('data')
    if data is not None:
        if len(data) > 0:
            application.sharedACLProfile = data.get('aclProfileName')


    if application.sharedACLProfile is None:
        raise Exception(
            f"Could not get application shared ACL profile from shared Authorization Group: '{application.sharedAuthorizationGroup}'")

    if action == ACTION_DEPLOY:
        # We just add the exceptions to the ACL!
        for produced_topic in application.producedEventTopics:
            sepi.add_publish_topic_exception(semp_token, broker_hostname, broker_msg_vpn, application.sharedACLProfile, produced_topic.get('topic'))

        for subscribe_topic in application.consumedEventTopics:
            sepi.add_subscribe_topic_exception(semp_token, broker_hostname, broker_msg_vpn, application.sharedACLProfile, subscribe_topic.get('topic'))

    elif action == ACTION_UNDEPLOY:
        # get all applications that share the same AuthorizationGroup
        txt_response = sepi.get_application_list_by_shared_authorization_group(ep_token, application.sharedAuthorizationGroup)
        pretty_json = sepi.to_pretty_json(txt_response)
        logger.info(pretty_json)
        json_response = json.loads(txt_response)
        data = json_response.get('data')
        applications_with_same_shared_auth_grp = []
        if data is not None:
            if len(data) > 0:
                for record in data:
                    applications_with_same_shared_auth_grp.append(record.get('id'))

        for event in application.declaredProducedEventVersionIds:
            txt_response = sepi.get_event_by_version(ep_token, event)
            pretty_json = sepi.to_pretty_json(txt_response)
            logger.info(pretty_json)
            json_response = json.loads(txt_response)
            data = json_response.get('data')
            if data is not None:
                if len(data) > 0:
                    #Get all events that are publishing that specific event!
                    producing_application_version_ids_tmp = data.get('declaredProducingApplicationVersionIds')
                    #remove itself!
                    if application.applicationVersionId in producing_application_version_ids_tmp:
                        producing_application_version_ids_tmp.remove(application.applicationVersionId)
                    # get list of all the microservices apps that are publishing that event
                    txt_response = sepi.get_application_versions_list_by_application_and_version_ids(ep_token, applications_with_same_shared_auth_grp, producing_application_version_ids_tmp)
                    pretty_json = sepi.to_pretty_json(txt_response)
                    logger.info(pretty_json)
                    json_response = json.loads(txt_response)
                    data = json_response.get('data')

                    # validate if the app is deployed or not
                    deployed_apps = []
                    for app_record in data:
                        app_version_id = app_record.get('id')
                        txt_response = sepi.get_preview_deploy_application_to_runtime(ep_token, broker_id, ACTION_DEPLOY,
                                                                                       app_version_id)
                        txt_response = sepi.to_pretty_json(txt_response)
                        print(txt_response)
                        json_response = json.loads(txt_response)
                        data = json_response.get('data')
                        existing = data.get('existing')
                        if len(existing) > 0:
                            deployed_apps.append(app_version_id)

                    print(f'Deployed Apps: {deployed_apps}')
                    if len(deployed_apps) == 0:
                        # no other microservice app is publishing that same event
                        # we can remove this entry from ACL
                        for produced_event_topic in application.producedEventTopics:
                            if event in produced_event_topic.get('eventIds'):
                                full_topic = produced_event_topic.get('topic')
                                sepi.remove_publish_topic_exception(semp_token, broker_hostname, broker_msg_vpn, application.sharedACLProfile, full_topic)

                            for event_id in produced_event_topic.get('eventIds'):
                                for entry in event_id:
                                    if isinstance(entry, dict) and entry.get('eventVersionId') is not None:
                                        if event in entry.get('eventVersionId'):
                                            full_topic = produced_event_topic.get('topic')
                                            sepi.remove_publish_topic_exception(semp_token, broker_hostname, broker_msg_vpn, application.sharedACLProfile, full_topic)

        for event in application.declaredConsumedEventVersionIdsWithConsumers:
            txt_response = sepi.get_event_by_version(ep_token, event)
            pretty_json = sepi.to_pretty_json(txt_response)
            logger.info(pretty_json)
            json_response = json.loads(txt_response)
            data = json_response.get('data')
            if data is not None:
                if len(data) > 0:
                    # Get all events that are consuming that specific event!
                    consuming_application_version_ids_tmp = data.get('declaredConsumingApplicationVersionIds')
                    # remove itself!
                    if application.applicationVersionId in consuming_application_version_ids_tmp:
                        consuming_application_version_ids_tmp.remove(application.applicationVersionId)
                    # get list of all the microservices apps that are publishing that event
                    txt_response = sepi.get_application_versions_list_by_application_and_version_ids(ep_token,
                                                                                                     applications_with_same_shared_auth_grp,
                                                                                                     consuming_application_version_ids_tmp)
                    pretty_json = sepi.to_pretty_json(txt_response)
                    logger.info(pretty_json)
                    json_response = json.loads(txt_response)
                    data = json_response.get('data')

                    # validate if the app is deployed or not
                    deployed_apps = []
                    for app_record in data:
                        app_version_id = app_record.get('id')
                        txt_response = sepi.get_preview_deploy_application_to_runtime(ep_token, broker_id, ACTION_DEPLOY,
                                                                                       app_version_id)
                        txt_response = sepi.to_pretty_json(txt_response)
                        print(txt_response)
                        json_response = json.loads(txt_response)
                        data = json_response.get('data')
                        existing = data.get('existing')
                        if len(existing) > 0:
                            deployed_apps.append(app_version_id)

                    print(f'Deployed Apps: {deployed_apps}')
                    if len(deployed_apps) == 0:
                        # no other microservice app is publishing that same event
                        # we can remove this entry from ACL
                        for consumed_event_topic in application.consumedEventTopics:
                            if event in consumed_event_topic.get('eventIds'):
                                full_topic = consumed_event_topic.get('topic')
                                sepi.remove_subscribe_topic_exception(semp_token, broker_hostname, broker_msg_vpn,
                                                                    application.sharedACLProfile, full_topic)
                            for event_id in consumed_event_topic.get('eventIds'):
                                for entry in event_id:
                                    if isinstance(entry, dict) and entry.get('eventVersionId') is not None:
                                        if event in entry.get('eventVersionId'):
                                            full_topic = consumed_event_topic.get('topic')
                                            sepi.remove_subscribe_topic_exception(semp_token, broker_hostname, broker_msg_vpn, application.sharedACLProfile, full_topic)

    return

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

    # for SEMP Calls - ACL
    parser.add_argument("-brokerHostname", type=str, required=True, help="Broker Hostname and Port")
    parser.add_argument("-msgVpn", type=str, required=True, help="Broker msgVpn")
    parser.add_argument("-sempToken", type=str, required=True, help="SEMP v2 Token to manipulate ACL")


    args = parser.parse_args()

    print(f"Arguments: Token: ***, brokerName: {args.brokerName}, action: {args.action} " +
          f"applicationName: {args.applicationName}, applicationVersion: {args.applicationVersion}, clientUsername: {args.clientUsername}, clientAuthorizationGroupName: {args.clientAuthorizationGroupName}")

    requested_app = sepi.EventPortalApplication(None, None, None,
                                                None, None, None, None)

    # Get Broker ID
    broker_id = sepi.get_broker_id_by_name(args.token, args.brokerName)
    if broker_id is None:
        raise Exception(f"Could not find an broker with name: {args.brokerName}")

    broker_service_id = sepi.get_broker_service_id_by_name(args.token, args.brokerName)
    if broker_service_id is None:
        raise Exception(f"Could not find an broker service with name: {args.brokerName}")

    # Get Application by Name
    sepi.get_application_list_by_name(args.token, args.applicationName, requested_app)
    if requested_app.applicationTitle is None or requested_app.applicationId is None:
        raise Exception(f"Could not find an application with name: {args.applicationName}")

    # Get Application Version by Name
    sepi.get_application_version_by_name(args.token, args.applicationVersion, requested_app)
    if requested_app.applicationVersion is None:
        raise Exception(f"Could not find an application versions for application with name: {requested_app.applicationTitle} and version name: {args.applicationVersion}")

    # Set Authorization parameters
    requested_app.clientUserName = args.clientUsername
    requested_app.clientAuthorizationGroupName = args.clientAuthorizationGroupName

    print(requested_app)

    # Write Async API spec to json file
    write_application_async_api_specification(args.token, requested_app)

    application_list = [requested_app]

    if args.action == ACTION_DEPLOY:
        # deploy applications to runtime broker
        deploy_applications_to_runtime(args.token, broker_service_id, broker_id, application_list)
    elif args.action == ACTION_UNDEPLOY:
        undeploy_applications_to_runtime(args.token, broker_id, application_list)

    update_acl_for_shared_apps(args.token, broker_id, args.sempToken, args.brokerHostname, args.msgVpn, application_list, args.action)

    for app in application_list:
        deploy_undeploy_application_to_runtime_preview(args.token, broker_id, ACTION_DEPLOY, app)

    return None


if __name__ == "__main__":
    http_client.HTTPConnection.debuglevel = 1

    # Create a console handler
    logging_format = '%(asctime)s.%(msecs)03d|%(levelname)-5s|%(name)s|%(message)s'
    console_handler = logging.StreamHandler(sys.stdout)
    logging_handlers = [console_handler]
    logging.basicConfig(handlers=logging_handlers, level=logging.INFO, format=logging_format, datefmt="%Y-%m-%d %H:%M:%S")
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

    # disable warning messages about https connection
    urllib3.disable_warnings()
    main(sys.argv[1:])