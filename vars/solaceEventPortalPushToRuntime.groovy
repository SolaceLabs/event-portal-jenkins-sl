#!/usr/bin/env groovy

import com.cloudbees.groovy.cps.NonCPS
import com.solace.ep.jenkins.Python

def script

@NonCPS
def call(Map config) {
	return new Python(this).pushApplicationToRuntime("","","","")
	
	
}
