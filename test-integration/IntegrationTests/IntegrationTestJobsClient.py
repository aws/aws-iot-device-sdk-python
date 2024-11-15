# This integration test verifies the jobs client functionality in the
# Python SDK.
# It performs a number of basic operations without expecting an actual job or
# job execution to be present. The callbacks associated with these actions
# are written to accept and pass server responses given when no jobs or job
# executions exist.
# Finally, the tester pumps through all jobs queued for the given thing
# doing a basic echo of the job document and updating the job execution
# to SUCCEEDED

import random
import string
import time
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary import simpleThreadManager
import TestToolLibrary.checkInManager as checkInManager
import TestToolLibrary.MQTTClientManager as MQTTClientManager
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTThingJobsClient
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionTopicType
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionTopicReplyType
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionStatus

import threading
import datetime
import argparse
import json

IOT_JOBS_MQTT_RESPONSE_WAIT_SECONDS = 5
CLIENT_ID = "integrationTestMQTT_Client" + "".join(random.choice(string.ascii_lowercase) for i in range(4))

class JobsMessageProcessor(object):
    def __init__(self, awsIoTMQTTThingJobsClient, clientToken):
        #keep track of this to correlate request/responses
        self.clientToken = clientToken
        self.awsIoTMQTTThingJobsClient = awsIoTMQTTThingJobsClient

    def _setupCallbacks(self):
        print('Creating test subscriptions...')
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.getPendingJobAcceptedCallback, jobExecutionTopicType.JOB_GET_PENDING_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.getPendingJobRejectedCallback, jobExecutionTopicType.JOB_GET_PENDING_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.describeJobExecAcceptedCallback, jobExecutionTopicType.JOB_DESCRIBE_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, '+')
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.describeJobExecRejectedCallback, jobExecutionTopicType.JOB_DESCRIBE_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, '+')
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.startNextPendingJobAcceptedCallback, jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.startNextPendingJobRejectedCallback, jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.updateJobAcceptedCallback, jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, '+')
        assert True == self.awsIoTMQTTThingJobsClient.createJobSubscription(self.updateJobRejectedCallback, jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, '+')

    def getPendingJobAcceptedCallback(self, client, userdata, message):
        self.testResult = (True, 'GetPending accepted callback invoked!')
        self.waitEvent.set()

    def getPendingJobRejectedCallback(self, client, userdata, message):
        self.testResult = (False, 'GetPending rejection callback invoked!')
        self.waitEvent.set()

    def describeJobExecAcceptedCallback(self, client, userdata, message):
        self.testResult = (True, 'DescribeJobExecution accepted callback invoked!')
        self.waitEvent.set()

    def describeJobExecRejectedCallback(self, client, userdata, message):
        self.testResult = (False, 'DescribeJobExecution rejected callback invoked!')
        self.waitEvent.set()

    def startNextPendingJobAcceptedCallback(self, client, userdata, message):
        self.testResult = (True, 'StartNextPendingJob accepted callback invoked!')
        payload = json.loads(message.payload.decode('utf-8'))
        if 'execution' not in payload:
            self.done = True
        else:
            print('Found job! Document: ' + payload['execution']['jobDocument'])
            threading.Thread(target=self.awsIoTMQTTThingJobsClient.sendJobsUpdate(payload['execution']['jobId'], jobExecutionStatus.JOB_EXECUTION_SUCCEEDED)).start()
        self.waitEvent.set()

    def startNextPendingJobRejectedCallback(self, client, userdata, message):
        self.testResult = (False, 'StartNextPendingJob rejected callback invoked!')
        self.waitEvent.set()

    def updateJobAcceptedCallback(self, client, userdata, message):
        self.testResult = (True, 'UpdateJob accepted callback invoked!')
        self.waitEvent.set()

    def updateJobRejectedCallback(self, client, userdata, message):
        #rejection is still a successful test because job IDs may or may not exist, and could exist in unknown state
        self.testResult = (True, 'UpdateJob rejected callback invoked!')
        self.waitEvent.set()

    def executeJob(self, execution):
        print('Executing job ID, version, number: {}, {}, {}'.format(execution['jobId'], execution['versionNumber'], execution['executionNumber']))
        print('With jobDocument: ' + json.dumps(execution['jobDocument']))

    def runTests(self):
        print('Running jobs tests...')
        ##create subscriptions
        self._setupCallbacks()

        #make publish calls
        self._init_test_wait()
        self._test_send_response_confirm(self.awsIoTMQTTThingJobsClient.sendJobsDescribe('$next'))

        self._init_test_wait()
        self._test_send_response_confirm(self.awsIoTMQTTThingJobsClient.sendJobsUpdate('junkJobId', jobExecutionStatus.JOB_EXECUTION_SUCCEEDED))

        self._init_test_wait()
        self._test_send_response_confirm(self.awsIoTMQTTThingJobsClient.sendJobsQuery(jobExecutionTopicType.JOB_GET_PENDING_TOPIC))

        self._init_test_wait()
        self._test_send_response_confirm(self.awsIoTMQTTThingJobsClient.sendJobsStartNext())

        self.processAllJobs()

    def processAllJobs(self):
        #process all enqueued jobs
        print('Processing all jobs found in queue for thing...')
        self.done = False
        while not self.done:
            self._attemptStartNextJob()
            time.sleep(5)

    def _attemptStartNextJob(self):
        statusDetails = {'StartedBy': 'ClientToken: {} on {}'.format(self.clientToken, datetime.datetime.now().isoformat())}
        threading.Thread(target=self.awsIoTMQTTThingJobsClient.sendJobsStartNext, kwargs = {'statusDetails': statusDetails}).start()

    def _init_test_wait(self):
        self.testResult = (False, 'Callback not invoked')
        self.waitEvent = threading.Event()

    def _test_send_response_confirm(self, sendResult):
        if not sendResult:
            print('Failed to send jobs message')
            exit(4)
        else:
            #wait 25 seconds for expected callback response to happen
            if not self.waitEvent.wait(IOT_JOBS_MQTT_RESPONSE_WAIT_SECONDS):
                print('Did not receive expected callback within %d second timeout' % IOT_JOBS_MQTT_RESPONSE_WAIT_SECONDS)
                exit(4)
            elif not self.testResult[0]:
                print('Callback result has failed the test with message: ' + self.testResult[1])
                exit(4)
            else:
                print('Recieved expected result: ' + self.testResult[1])


############################################################################
# Main #
# Check inputs
myCheckInManager = checkInManager.checkInManager(2)
myCheckInManager.verify(sys.argv)

host = myCheckInManager.host
rootCA = "./test-integration/Credentials/rootCA.crt"
certificate = "./test-integration/Credentials/certificate.pem.crt"
privateKey = "./test-integration/Credentials/privateKey.pem.key"
mode = myCheckInManager.mode

skip_when_match(ModeIsALPN(mode).And(
    Python2VersionLowerThan((2, 7, 10)).Or(Python3VersionLowerThan((3, 5, 0)))
), "This test is not applicable for mode %s and Python verison %s. Skipping..." % (mode, sys.version_info[:3]))

# Init Python core and connect
myMQTTClientManager = MQTTClientManager.MQTTClientManager()
client = myMQTTClientManager.create_connected_mqtt_client(mode, CLIENT_ID, host, (rootCA, certificate, privateKey))

clientId = 'AWSPythonkSDKTestThingClient'
thingName = 'AWSPythonkSDKTestThing'
jobsClient = AWSIoTMQTTThingJobsClient(clientId, thingName, QoS=1, awsIoTMQTTClient=client)

print('Connecting to MQTT server and setting up callbacks...')
jobsMsgProc = JobsMessageProcessor(jobsClient, clientId)
print('Starting jobs tests...')
jobsMsgProc.runTests()
print('Done running jobs tests')

#can call this on the jobsClient, or myAWSIoTMQTTClient directly
jobsClient.disconnect()
