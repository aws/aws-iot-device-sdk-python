from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from threading import Lock
import logging
import time
import json
import argparse

timeout = 5
pendingJob = True
runningJobLock = Lock()


# Custom job start-next callback
def customJobCallback_StartNext(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    print(responseStatus)
    if responseStatus != "timeout":
        payloadDict = json.loads(payload)
        print("\n\n+++++++START-NEXT++++++\n"
              + json.dumps(payloadDict, indent=4, sort_keys=True)
              + "\n+++++++++++++++++++++++\n\n")
        # Check if there is a job to run
        if u"execution" in payloadDict.keys():
            # Lock to prevent concurrent execution of jobs
            runningJobLock.acquire()
            # Execute the job
            executeJob(payloadDict[u"execution"])


# Custom job update callback
def customJobCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    print(responseStatus)
    # Release the job execution lock regardless of status (Publish QoS=1)
    runningJobLock.release()
    if responseStatus != "timeout":
        payloadDict = json.loads(payload)
        print("\n\n+++++++UPDATE++++++\n"
              + json.dumps(payloadDict, indent=4, sort_keys=True)
              + "\n+++++++++++++++++++++++\n\n")


# Custom job notify-next callback
def customJobCallback_NotifyNext(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    print(responseStatus)
    payloadDict = json.loads(payload)
    print("\n\n++++++++NOTIFY+++++++++\n"
          + json.dumps(payloadDict, indent=4, sort_keys=True)
          + "\n+++++++++++++++++++++++\n\n")
    # Trigger an execution if there is a pending job
    if u"execution" in payloadDict.keys():
        # Trigger the next pending job execution
        jobHandler.jobStartNext(customJobCallback_StartNext, timeout)


# Simulates a job being processed - must update the job or release the lock
def executeJob(jobExecutionDict):
    # Simulate processing time
    time.sleep(10)
    # Report successful execution
    jobHandler.jobUpdate("SUCCEEDED", customJobCallback_Update, timeout)


# Read in command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicJobHandler",
                    help="Targeted client id")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
useWebsocket = args.useWebsocket
thingName = args.thingName
clientId = args.clientId

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = None
if useWebsocket:
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId, useWebsocket=True)
    myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
    myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a job handler with persistent subscription
jobHandler = myAWSIoTMQTTShadowClient.createJobHandlerWithName(thingName, True)

# Listen for changes to the next pending job
jobHandler.jobRegisterNotifyNextCallback(customJobCallback_NotifyNext)

# Trigger the next pending job execution in case any are already queued
jobHandler.jobStartNext(customJobCallback_StartNext, timeout)

# Loop forever
while True:
    time.sleep(1)
