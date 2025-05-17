#!/usr/bin/env groovy

import com.solace.ep.jenkins.Python

def call(Map config) {
	def value = config.token
	sh "echo the value is ${value}"
	return new Python(this).pushApplicationToRuntime("","","","")
	
	
}
