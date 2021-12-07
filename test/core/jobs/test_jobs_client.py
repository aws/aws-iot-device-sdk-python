# Test AWSIoTMQTTThingJobsClient behavior

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTThingJobsClient
from AWSIoTPythonSDK.core.jobs.thingJobManager import thingJobManager
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionTopicType
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionTopicReplyType
from AWSIoTPythonSDK.core.jobs.thingJobManager import jobExecutionStatus
import AWSIoTPythonSDK.MQTTLib
import time
import json
from mock import MagicMock

#asserts based on this documentation: https://docs.aws.amazon.com/iot/latest/developerguide/jobs-api.html
class TestAWSIoTMQTTThingJobsClient:
    thingName = 'testThing'
    clientTokenValue = 'testClientToken123'
    statusDetailsMap = {'testKey':'testVal'}

    def setup_method(self, method):
        self.mockAWSIoTMQTTClient = MagicMock(spec=AWSIoTMQTTClient)
        self.jobsClient = AWSIoTMQTTThingJobsClient(self.clientTokenValue, self.thingName, QoS=0, awsIoTMQTTClient=self.mockAWSIoTMQTTClient)
        self.jobsClient._thingJobManager = MagicMock(spec=thingJobManager)

    def test_unsuccessful_create_subscription(self):
        fake_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'UnsuccessfulCreateSubTopic'
        self.mockAWSIoTMQTTClient.subscribe.return_value = False
        assert False == self.jobsClient.createJobSubscription(fake_callback)

    def test_successful_job_request_create_subscription(self):
        fake_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SuccessfulCreateSubRequestTopic'
        self.mockAWSIoTMQTTClient.subscribe.return_value = True
        assert True == self.jobsClient.createJobSubscription(fake_callback)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_WILDCARD_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, None)
        self.mockAWSIoTMQTTClient.subscribe.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_callback)

    def test_successful_job_start_next_create_subscription(self):
        fake_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SuccessfulCreateSubStartNextTopic'
        self.mockAWSIoTMQTTClient.subscribe.return_value = True
        assert True == self.jobsClient.createJobSubscription(fake_callback, jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, None)
        self.mockAWSIoTMQTTClient.subscribe.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_callback)

    def test_successful_job_update_create_subscription(self):
        fake_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SuccessfulCreateSubUpdateTopic'
        self.mockAWSIoTMQTTClient.subscribe.return_value = True
        assert True == self.jobsClient.createJobSubscription(fake_callback, jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, 'jobUpdateId')
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, 'jobUpdateId')
        self.mockAWSIoTMQTTClient.subscribe.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_callback)

    def test_successful_job_update_notify_next_create_subscription(self):
        fake_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SuccessfulCreateSubNotifyNextTopic'
        self.mockAWSIoTMQTTClient.subscribe.return_value = True
        assert True == self.jobsClient.createJobSubscription(fake_callback, jobExecutionTopicType.JOB_NOTIFY_NEXT_TOPIC)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_NOTIFY_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, None)
        self.mockAWSIoTMQTTClient.subscribe.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_callback)

    def test_successful_job_request_create_subscription_async(self):
        fake_callback = MagicMock();
        fake_ack_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'CreateSubTopic1'
        self.mockAWSIoTMQTTClient.subscribeAsync.return_value = 'MessageId1'
        assert self.mockAWSIoTMQTTClient.subscribeAsync.return_value == self.jobsClient.createJobSubscriptionAsync(fake_ack_callback, fake_callback)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_WILDCARD_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, None)
        self.mockAWSIoTMQTTClient.subscribeAsync.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_ack_callback, fake_callback)

    def test_successful_job_start_next_create_subscription_async(self):
        fake_callback = MagicMock();
        fake_ack_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'CreateSubTopic3'
        self.mockAWSIoTMQTTClient.subscribeAsync.return_value = 'MessageId3'
        assert self.mockAWSIoTMQTTClient.subscribeAsync.return_value == self.jobsClient.createJobSubscriptionAsync(fake_ack_callback, fake_callback, jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, None)
        self.mockAWSIoTMQTTClient.subscribeAsync.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_ack_callback, fake_callback)

    def test_successful_job_update_create_subscription_async(self):
        fake_callback = MagicMock();
        fake_ack_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'CreateSubTopic4'
        self.mockAWSIoTMQTTClient.subscribeAsync.return_value = 'MessageId4'
        assert self.mockAWSIoTMQTTClient.subscribeAsync.return_value == self.jobsClient.createJobSubscriptionAsync(fake_ack_callback, fake_callback, jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, 'jobUpdateId3')
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_REJECTED_REPLY_TYPE, 'jobUpdateId3')
        self.mockAWSIoTMQTTClient.subscribeAsync.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_ack_callback, fake_callback)

    def test_successful_job_notify_next_subscription_async(self):
        fake_callback = MagicMock();
        fake_ack_callback = MagicMock();
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'CreateSubTopic5'
        self.mockAWSIoTMQTTClient.subscribeAsync.return_value = 'MessageId5'
        assert self.mockAWSIoTMQTTClient.subscribeAsync.return_value == self.jobsClient.createJobSubscriptionAsync(fake_ack_callback, fake_callback, jobExecutionTopicType.JOB_NOTIFY_NEXT_TOPIC)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_NOTIFY_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, None)
        self.mockAWSIoTMQTTClient.subscribeAsync.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, 0, fake_ack_callback, fake_callback)

    def test_send_jobs_query_get_pending(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendJobsQuery1'
        self.jobsClient._thingJobManager.serializeClientTokenPayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = True
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsQuery(jobExecutionTopicType.JOB_GET_PENDING_TOPIC)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_GET_PENDING_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, None)
        self.jobsClient._thingJobManager.serializeClientTokenPayload.assert_called_with()
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeClientTokenPayload.return_value, 0)

    def test_send_jobs_query_describe(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendJobsQuery2'
        self.jobsClient._thingJobManager.serializeClientTokenPayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = True
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsQuery(jobExecutionTopicType.JOB_DESCRIBE_TOPIC, 'jobId2')
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_DESCRIBE_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, 'jobId2')
        self.jobsClient._thingJobManager.serializeClientTokenPayload.assert_called_with()
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeClientTokenPayload.return_value, 0)

    def test_send_jobs_start_next(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendStartNext1'
        self.jobsClient._thingJobManager.serializeStartNextPendingJobExecutionPayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = True
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsStartNext(self.statusDetailsMap, 12)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        self.jobsClient._thingJobManager.serializeStartNextPendingJobExecutionPayload.assert_called_with(self.statusDetailsMap, 12)
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeStartNextPendingJobExecutionPayload.return_value, 0)

    def test_send_jobs_start_next_no_status_details(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendStartNext2'
        self.jobsClient._thingJobManager.serializeStartNextPendingJobExecutionPayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = False
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsStartNext({})
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_START_NEXT_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE)
        self.jobsClient._thingJobManager.serializeStartNextPendingJobExecutionPayload.assert_called_with({}, None)
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeStartNextPendingJobExecutionPayload.return_value, 0)

    def test_send_jobs_update_succeeded(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendJobsUpdate1'
        self.jobsClient._thingJobManager.serializeJobExecutionUpdatePayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = True
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsUpdate('jobId1', jobExecutionStatus.JOB_EXECUTION_SUCCEEDED, self.statusDetailsMap, 1, 2, True, False, 12)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, 'jobId1')
        self.jobsClient._thingJobManager.serializeJobExecutionUpdatePayload.assert_called_with(jobExecutionStatus.JOB_EXECUTION_SUCCEEDED, self.statusDetailsMap, 1, 2, True, False, 12)
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeJobExecutionUpdatePayload.return_value, 0)

    def test_send_jobs_update_failed(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendJobsUpdate2'
        self.jobsClient._thingJobManager.serializeJobExecutionUpdatePayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = False
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsUpdate('jobId2', jobExecutionStatus.JOB_EXECUTION_FAILED, {}, 3, 4, False, True, 34)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, 'jobId2')
        self.jobsClient._thingJobManager.serializeJobExecutionUpdatePayload.assert_called_with(jobExecutionStatus.JOB_EXECUTION_FAILED, {}, 3, 4, False, True, 34)
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeJobExecutionUpdatePayload.return_value, 0)

    def test_send_jobs_describe(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendJobsDescribe1'
        self.jobsClient._thingJobManager.serializeDescribeJobExecutionPayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = True
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsDescribe('jobId1', 2, True)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_DESCRIBE_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, 'jobId1')
        self.jobsClient._thingJobManager.serializeDescribeJobExecutionPayload.assert_called_with(2, True)
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeDescribeJobExecutionPayload.return_value, 0)

    def test_send_jobs_describe_false_return_val(self):
        self.jobsClient._thingJobManager.getJobTopic.return_value = 'SendJobsDescribe2'
        self.jobsClient._thingJobManager.serializeDescribeJobExecutionPayload.return_value = {}
        self.mockAWSIoTMQTTClient.publish.return_value = False
        assert self.mockAWSIoTMQTTClient.publish.return_value == self.jobsClient.sendJobsDescribe('jobId2', 1, False)
        self.jobsClient._thingJobManager.getJobTopic.assert_called_with(jobExecutionTopicType.JOB_DESCRIBE_TOPIC, jobExecutionTopicReplyType.JOB_REQUEST_TYPE, 'jobId2')
        self.jobsClient._thingJobManager.serializeDescribeJobExecutionPayload.assert_called_with(1, False)
        self.mockAWSIoTMQTTClient.publish.assert_called_with(self.jobsClient._thingJobManager.getJobTopic.return_value, self.jobsClient._thingJobManager.serializeDescribeJobExecutionPayload.return_value, 0)
