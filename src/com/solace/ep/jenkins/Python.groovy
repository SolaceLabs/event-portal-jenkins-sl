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
	
	def pushApplicationToRuntime (String token, String brokerId, String clientUsername, String clientAuthorizationGroupName) {
		
		String params = "-token eyJhbGciOiJSUzI1NiIsImtpZCI6Im1hYXNfcHJvZF8yMDIwMDMyNiIsInR5cCI6IkpXVCJ9.eyJvcmciOiJzb2xhY2V1c2VycyIsIm9yZ1R5cGUiOiJFTlRFUlBSSVNFIiwic3ViIjoiOXV6MjUyb2MybWkiLCJwZXJtaXNzaW9ucyI6IkFBQUFBSUFrQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUlBd0NBTUFJQURnTC8vL2c1WWZCUVlBQUVNRFk0WTVNd01CQVBoZkJnQUkiLCJhcGlUb2tlbklkIjoiMDZxODNiMTN0OXIiLCJpc3MiOiJTb2xhY2UgQ29ycG9yYXRpb24iLCJpYXQiOjE3NDY2NDMzODh9.O3Olpmp5So5k_1w0ZlmjZD60T088K9I6pnyWeWhhGZgcR1W2GewjHc4G4kzSNTPTImNHIhCvg2nc9xsS5EBA5fD5B93a4Z1iwaNtVwMjcXJ92sBExGGria1I2JgL2yQZ3Hal4MfSTb_CNfUYK1xiBd-MqweBjBf1m12rw8utVPuUNIvD_IVjIK0Gz3R-_hGcDIRcn6TJZl7ALAF6CX5AY3Des2NyEmfiShwiDPxRFsxga40ghxqahs1FLoWVAU7gCVboIh_tjz6U7j7xVL1Y001k6u0_dcab-ghYPDLIdqjLvzuq5j4s-BN3abiJhrncTjEeBoQGkC9ltLJt8VtxJw -brokerId wy6s3djof41 -clientUsername incident_manager -clientAuthorizationGroupName IncidentManagerOAuth"
		
		def commandOutput
		
		if(this.script.isUnix()) {
			commandOutput = script.sh (
				script: '. env/bin/python3 python/scripts/solace-ep-push-to-runtime.py ' + params,
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
	
	/*
    def lintCheck()
    {
        script.sh "python3 -m flake8 ."
    }
    def pytestCheck()
    {
        script.sh "python3 -m pytest ."
    }
    def IncrementVersion(String type)
    {
        script.sh "python3 utils/versioner.py --${type}"
    }
    */
	
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