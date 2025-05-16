#!/usr/bin/env groovy

import com.cloudbees.groovy.cps.NonCPS


def script

@NonCPS
def call(def dir, Map config) {
	echo "Entering solaceEventPortalPushToRuntime step"

	directory = this.env.ASYNC_API_DIR
	
	echo "AsyncAPI directory: ${directory}"
	
	directory = config.get('async-api-dir')

	echo "AsyncAPI directory: ${directory}"
	
	
	//def files = findFiles()
	
	/*
	dir.eachFileRecurse (FileType.FILES) { file ->
		file = file.toString()
		echo "This is directory: ${file.name} "
	}
	*/
	/*
	
	dir(directory) {
		def files = findFiles()
		
		files.each{ f ->
			if(f.directory) {
				echo "This is directory: ${f.name} "
			}
		}
	}
	*/

}
