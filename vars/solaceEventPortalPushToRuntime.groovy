#!/usr/bin/env groovy

import com.cloudbees.groovy.cps.NonCPS


def script

@NonCPS
def call(Map config) {
	return new Python(this).pushApplicationToRuntime("","","","")
	
	
}
