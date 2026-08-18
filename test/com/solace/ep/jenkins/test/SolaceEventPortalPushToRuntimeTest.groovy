package com.solace.ep.jenkins.test;

import static org.junit.jupiter.api.Assertions.*

import static org.junit.jupiter.api.Assumptions.*
import static org.junit.jupiter.api.DynamicContainer.*
import static org.junit.jupiter.api.DynamicTest.*

import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.DynamicNode
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.TestFactory

import static com.lesfurets.jenkins.unit.global.lib.LibraryConfiguration.library
import static com.lesfurets.jenkins.unit.global.lib.ProjectSource.projectSource

import com.lesfurets.jenkins.unit.BasePipelineTest;
import com.lesfurets.jenkins.unit.declarative.DeclarativePipelineTest

public class SolaceEventPortalPushToRuntimeTest extends DeclarativePipelineTest { //BasePipelineTest {//DeclarativePipelineTest {
    @Override
    @BeforeEach
    void setUp() {
        super.setUp()
		
		Object library = library() 
		.name('solace-ep-integration')
		.defaultVersion('<notNeeded>')
		.allowOverride(true)
		.implicit(true)
		.targetPath('<notNeeded>')
		.retriever(projectSource())
		.build()
		helper.registerSharedLibrary(library)
		
        // Assigns false to a job parameter ENABLE_TEST_STAGE
        addParam('ENABLE_TEST_STAGE', 'false')
        // Assigns 1.0.0-rc.1 to the environment variable TAG_NAME
        addEnvVar('TAG_NAME', '1.0.0-rc.1')
        // Defines the previous execution status
        binding.getVariable('currentBuild').previousBuild = [result: 'UNSTABLE']
    }

    @Test
    void verifyParam() {
        assertEquals('false', binding.getVariable('params')['ENABLE_TEST_STAGE'])
    }
	
	@Test
	void solaceEventPortalPushToRuntimeTest () {
		runScript("test/resources/workspace/Jenkinsfile")
		//runScript("Jenkinsfile")
	}
	
}
