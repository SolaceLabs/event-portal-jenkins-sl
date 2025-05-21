#!/usr/bin/env groovy

import com.solace.ep.jenkins.Python

def call(Map config) {
	return new Python(this).validateAuthGroup(config)
	
	
}
