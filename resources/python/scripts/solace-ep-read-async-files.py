import solace_ep_integration as sepi
import sys

# Main
def main(argv):
    # scan current workspace to get all the json files and read them
    application_list = sepi.get_applications_from_json_files()
    app_list = []
    for app in application_list:
       app_list.append( f"{app.applicationTitle} - v{app.applicationVersion}" )

    apps = '@'.join(app_list)
    print(apps)
    return None

if __name__ == "__main__":
    main(sys.argv[1:])
