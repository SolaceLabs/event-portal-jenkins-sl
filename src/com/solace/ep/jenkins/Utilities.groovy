package com.solace.ep.jenkins

import groovy.io.*

class Utilities {
	/*
	static def script = null
	
	static def InitializeU(Script scriptz) {
		if(script == null) {
			script = scriptz;
		}
	}
	*/
	
	static def FindAsyncApiFiles(script) {
		return script.findFiles()
	}
	
	@NonCPS
	static def fetFilenamesFromDir(def dir, def list) {

		dir.eachFileRecurse (FileType.FILES) { file ->
			file = file.toString()
			if (file.endsWith("json")) {
				list << file
			}
		}

	}
	
}
