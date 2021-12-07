# Test thingJobManager behavior

from AWSIoTPythonSDK.core.jobs.thingJobManager import thingJobManager as JobManager
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionTopicType
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionTopicReplyType
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionStatus
import time
import json
from mock import MagicMock

#asserts based on this documentation: https://docs.aws.amazon.com/iot/latest/developerguide/jobs-api.html
class TestThingJobManager:
    thingName = 'testThing'
    clientTokenValue = "testClientToken123"
    thingJobManager = JobManager(thingName, clientTokenValue)
    noClientTokenJobManager = JobManager(thingName)
    jobId = '8192'
    statusDetailsMap = {'testKey':'testVal'}

    def test_pending_topics(self):
        topicType = jobExecutionTopicType.JOB_GET_PENDING_TOPIC
        assert ('$aws/things/' + self.thingName + '/jobs/get') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        assert ('$aws/things/' + self.thingName + '/jobs/get/accepted') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert ('$aws/things/' + self.thingName + '/jobs/get/rejected') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert ('$aws/things/' + self.thingName + '/jobs/get/#') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE, self.jobId)

    def test_start_next_topics(self):
        topicType = jobExecutionTopicType.JOB_START_NEXT_TOPIC
        assert ('$aws/things/' + self.thingName + '/jobs/start-next') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        assert ('$aws/things/' + self.thingName + '/jobs/start-next/accepted') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert ('$aws/things/' + self.thingName + '/jobs/start-next/rejected') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert ('$aws/things/' + self.thingName + '/jobs/start-next/#') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE, self.jobId)

    def test_describe_topics(self):
        topicType = jobExecutionTopicType.JOB_DESCRIBE_TOPIC
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/get') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, self.jobId)
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/get/accepted') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, self.jobId)
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/get/rejected') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, self.jobId)
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/get/#') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)

    def test_update_topics(self):
        topicType = jobExecutionTopicType.JOB_UPDATE_TOPIC
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/update') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, self.jobId)
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/update/accepted') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, self.jobId)
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/update/rejected') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, self.jobId)
        assert ('$aws/things/' + self.thingName + '/jobs/' + str(self.jobId) + '/update/#') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)

    def test_notify_topics(self):
        topicType = jobExecutionTopicType.JOB_NOTIFY_TOPIC
        assert ('$aws/things/' + self.thingName + '/jobs/notify') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE, self.jobId)

    def test_notify_next_topics(self):
        topicType = jobExecutionTopicType.JOB_NOTIFY_NEXT_TOPIC
        assert ('$aws/things/' + self.thingName + '/jobs/notify-next') == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE, self.jobId)

    def test_wildcard_topics(self):
        topicType = jobExecutionTopicType.JOB_WILDCARD_TOPIC
        topicString = '$aws/things/' + self.thingName + '/jobs/#'
        assert topicString == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        assert topicString == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert topicString == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert topicString == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)

    def test_thingless_topics(self):
        thinglessJobManager = JobManager(None)
        assert None == thinglessJobManager.getJobTopic(jobExecutionTopicType.JOB_GET_PENDING_TOPIC)
        assert None == thinglessJobManager.getJobTopic(jobExecutionTopicType.JOB_START_NEXT_TOPIC)
        assert None == thinglessJobManager.getJobTopic(jobExecutionTopicType.JOB_DESCRIBE_TOPIC)
        assert None == thinglessJobManager.getJobTopic(jobExecutionTopicType.JOB_UPDATE_TOPIC)
        assert None == thinglessJobManager.getJobTopic(jobExecutionTopicType.JOB_NOTIFY_TOPIC)
        assert None == thinglessJobManager.getJobTopic(jobExecutionTopicType.JOB_NOTIFY_NEXT_TOPIC)
        assert None == thinglessJobManager.getJobTopic(jobExecutionTopicType.JOB_WILDCARD_TOPIC)

    def test_unrecognized_topics(self):
        topicType = jobExecutionTopicType.JOB_UNRECOGNIZED_TOPIC
        assert None == self.thingJobManager.getJobTopic(topicType)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, self.jobId)
        assert None == self.thingJobManager.getJobTopic(topicType, jobExecutionTopicReplyType.JOB_WILDCARD_REPLY_TYPE, self.jobId)

    def test_serialize_client_token(self):
        payload = '{"clientToken": "' + self.clientTokenValue + '"}'
        assert payload == self.thingJobManager.serializeClientTokenPayload()
        assert "{}" == self.noClientTokenJobManager.serializeClientTokenPayload()

    def test_serialize_start_next_pending_job_execution(self):
        payload = {'clientToken': self.clientTokenValue}
        assert payload == json.loads(self.thingJobManager.serializeStartNextPendingJobExecutionPayload())
        assert {} == json.loads(self.noClientTokenJobManager.serializeStartNextPendingJobExecutionPayload())
        payload.update({'statusDetails': self.statusDetailsMap})
        assert payload == json.loads(self.thingJobManager.serializeStartNextPendingJobExecutionPayload(self.statusDetailsMap))
        assert {'statusDetails': self.statusDetailsMap} == json.loads(self.noClientTokenJobManager.serializeStartNextPendingJobExecutionPayload(self.statusDetailsMap))

    def test_serialize_describe_job_execution(self):
        payload = {'includeJobDocument': True}
        assert payload == json.loads(self.noClientTokenJobManager.serializeDescribeJobExecutionPayload())
        payload.update({'executionNumber': 1})
        assert payload == json.loads(self.noClientTokenJobManager.serializeDescribeJobExecutionPayload(1))
        payload.update({'includeJobDocument': False})
        assert payload == json.loads(self.noClientTokenJobManager.serializeDescribeJobExecutionPayload(1, False))

        payload = {'includeJobDocument': True, 'clientToken': self.clientTokenValue}
        assert payload == json.loads(self.thingJobManager.serializeDescribeJobExecutionPayload())
        payload.update({'executionNumber': 1})
        assert payload == json.loads(self.thingJobManager.serializeDescribeJobExecutionPayload(1))
        payload.update({'includeJobDocument': False})
        assert payload == json.loads(self.thingJobManager.serializeDescribeJobExecutionPayload(1, False))

    def test_serialize_job_execution_update(self):
        assert None == self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_STATUS_NOT_SET)
        assert None == self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_UNKNOWN_STATUS)
        assert None == self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_STATUS_NOT_SET)
        assert None == self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_UNKNOWN_STATUS)

        payload = {'status':'IN_PROGRESS'}
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_IN_PROGRESS))
        payload.update({'status':'FAILED'})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_FAILED))
        payload.update({'status':'SUCCEEDED'})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_SUCCEEDED))
        payload.update({'status':'CANCELED'})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_CANCELED))
        payload.update({'status':'REJECTED'})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_REJECTED))
        payload.update({'status':'QUEUED'})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED))
        payload.update({'statusDetails': self.statusDetailsMap})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap))
        payload.update({'expectedVersion': '1'})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1))
        payload.update({'executionNumber': '1'})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1, 1))
        payload.update({'includeJobExecutionState': True})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1, 1, True))
        payload.update({'includeJobDocument': True})
        assert payload == json.loads(self.noClientTokenJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1, 1, True, True))

        payload = {'status':'IN_PROGRESS', 'clientToken': self.clientTokenValue}
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_IN_PROGRESS))
        payload.update({'status':'FAILED'})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_FAILED))
        payload.update({'status':'SUCCEEDED'})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_SUCCEEDED))
        payload.update({'status':'CANCELED'})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_CANCELED))
        payload.update({'status':'REJECTED'})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_REJECTED))
        payload.update({'status':'QUEUED'})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED))
        payload.update({'statusDetails': self.statusDetailsMap})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap))
        payload.update({'expectedVersion': '1'})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1))
        payload.update({'executionNumber': '1'})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1, 1))
        payload.update({'includeJobExecutionState': True})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1, 1, True))
        payload.update({'includeJobDocument': True})
        assert payload == json.loads(self.thingJobManager.serializeJobExecutionUpdatePayload(jobExecutionStatus.JOB_EXECUTION_QUEUED, self.statusDetailsMap, 1, 1, True, True))
