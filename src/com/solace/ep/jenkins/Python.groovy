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
        //script.sh "pip3 install -r devrequirements.txt"
		copyResourceFromLibrary("python/dependencies/install-dependencies.bat", true)
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
		def resourceContent = script.libraryResource(pathToResource)
		if(isText) {
			script.writeFile file: pathToResource, text: resourceContent
		}  
		//script.sh "chmod +x ${outputFile}"
	}
	
	private String getFileNameFromPath (filePath) {
		def fileName = filePath.substring(filePath.lastIndexOf('/') + 1)
		return fileName
	}
	
}