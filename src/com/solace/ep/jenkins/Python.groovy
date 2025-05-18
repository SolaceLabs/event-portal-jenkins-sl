#! /usr/bin/env groovy

package com.solace.ep.jenkins

class Python implements Serializable {
    def script
	
    Python(script) {
        this.script = script
    }

    def createVirtualEnv() {
		def currentFolder = script.pwd()
		script.echo "Creating python virtual environment in folder: '${currentFolder}'"
		
		def commandOutput
		
		if(this.script.isUnix()) {
			commandOutput = script.sh (
				script: 'python3 -m venv env',
				returnStdout: true
			).trim()
			
		} else {
			commandOutput = script.sh (
				script: 'python -m venv env',
				returnStdout: true
			).trim()
		}
		
		script.echo "Output:  ${commandOutput}"
    }
	
    def activateVirtualEnv() {
		def currentFolder = script.pwd()
		script.echo "Activating python virtual environment in folder: '${currentFolder}/env'"

		def commandOutput
		
		if(this.script.isUnix()) {
			commandOutput = script.sh (
				script: '. env/bin/activate',
				returnStdout: true
			).trim()

		} else {
			commandOutput = script.sh (
				script: '.\\env\\Scripts\\activate.bat',
				returnStdout: true
			).trim()
		}
		
		script.echo "Output:  ${commandOutput}"
    }
    
    def installDependencies() {
        
		script.echo "Copying required dependencies...'"
		copyResourceFromLibrary("python/dependencies/install-dependencies.bat", true)
		copyResourceFromLibrary("python/dependencies/install-dependencies.sh", true)
		copyResourceFromLibrary("python/dependencies/lib/certifi-2025.4.26-py3-none-any.whl", false)
		copyResourceFromLibrary("python/dependencies/lib/charset_normalizer-3.4.2-py3-none-any.whl", false)
		copyResourceFromLibrary("python/dependencies/lib/idna-3.10-py3-none-any.whl", false)
		copyResourceFromLibrary("python/dependencies/lib/pip-25.1.1-py3-none-any.whl", false)
		copyResourceFromLibrary("python/dependencies/lib/requests-2.32.3-py3-none-any.whl", false)
		copyResourceFromLibrary("python/dependencies/lib/urllib3-2.4.0-py3-none-any.whl", false)
		
		script.echo "All dependencies copied'"
		script.echo "Installing dependencies.."

		def commandOutput
		
		if(this.script.isUnix()) {
			commandOutput = script.sh (
				script: 'sh python/dependencies/install-dependencies.sh',
				returnStdout: true
			).trim()

		} else {
			commandOutput = script.sh (
				script: '.\\python\\dependencies\\install-dependencies.bat',
				returnStdout: true
			).trim()
		}
		
		script.echo "Output:  ${commandOutput}"

		script.echo "Copying required scripts...'"
		copyResourceFromLibrary("python/scripts/solace_ep_integration.py", true)
		script.sh "chmod +x python/scripts/solace_ep_integration.py"
		copyResourceFromLibrary("python/scripts/solace-ep-list-messaging-services.py", true)
		script.sh "chmod +x python/scripts/solace_ep_integration.py"
		copyResourceFromLibrary("python/scripts/solace-ep-list-modeled-event-meshes.py", true)
		script.sh "chmod +x python/scripts/solace_ep_integration.py"
		copyResourceFromLibrary("python/scripts/solace-ep-push-to-runtime.py", true)
		script.sh "chmod +x python/scripts/solace_ep_integration.py"
    }
	
	def pushApplicationToRuntime (HashMap config) {
		
		String token = config.get("token")
		String brokerName = config.get("brokerName")
		String action = config.get("action")
		String applicationName = config.get("applicationName")
		String applicationVersion = config.get("applicationVersion")
		String clientUsername = config.get("clientUsername")
		String clientAuthorizationGroupName = config.get("clientAuthorizationGroupName")
		
		String params = String.format("-token %s -brokerName \"%s\" -action \"%s\" -applicationName \"%s\" -applicationVersion \"%s\" -clientUsername \"%s\" -clientAuthorizationGroupName \"%s\"", 
				token, brokerName, action, applicationName, applicationVersion, clientUsername, clientAuthorizationGroupName) 
		
		def commandOutput
		
		if(this.script.isUnix()) {
			commandOutput = script.sh (
				script: 'env/bin/python3 python/scripts/solace-ep-push-to-runtime.py ' + params,
				returnStdout: true
			).trim()

		} else {
			commandOutput = script.sh (
				script: 'python python\\scripts\\solace-ep-push-to-runtime.py ' + params,
				returnStdout: true
			).trim()
		}
		
		script.echo "Output:  ${commandOutput}"
	}
	
	
	private void copyResourceFromLibrary(String pathToResource, boolean isText) {
		if(isText) {
			def resourceContent = script.libraryResource resource: pathToResource
			script.writeFile file: pathToResource, text: resourceContent
		} else {
			def resourceContent = script.libraryResource resource: pathToResource, encoding: "Base64"
			script.writeFile file: pathToResource, text: resourceContent, encoding: "Base64"
			
		}
	}
	
	private String getFileNameFromPath (filePath) {
		def fileName = filePath.substring(filePath.lastIndexOf('/') + 1)
		return fileName
	}
	
}