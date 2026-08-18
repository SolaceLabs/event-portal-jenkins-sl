import argparse
import sys
import urllib3
import solace_ep_integration as sepi

def main(argv):
    # Parse parameters
    parser = argparse.ArgumentParser(description="List Messaging Services")
    parser.add_argument("-token", type=str, required=True, help="Event Portal Auth Token")

    args = parser.parse_args()

    json_response = sepi.get_messaging_services(args.token)

    pretty_json = sepi.to_pretty_json(json_response)
    print(pretty_json)
    return None

if __name__ == "__main__":
    # disable warning messages about https connection
    urllib3.disable_warnings()
    main(sys.argv[1:])

