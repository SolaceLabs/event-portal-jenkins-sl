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
		copyResourceFromLibrary("python/dependencies/install-dependencies.bat", "python/dependencies/")
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
	
	private String copyResourceFromLibrary(String pathToResource, String destFolder) {
		def resourceContent = script.libraryResource(pathToResource)
		def fileName = getFileNameFromPath(pathToResource)
		def outputPath = String.format("%s/%s", destFolder, fileName)
		script.writeFile file: outputPath, text: resourceContent
		//script.sh "chmod +x ${outputFile}"
		return outputPath
	}
	
	private String getFileNameFromPath (filePath) {
		def fileName = filePath.substring(filePath.lastIndexOf('/') + 1)
		return fileName
	}
	
}