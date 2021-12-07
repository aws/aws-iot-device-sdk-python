class mockMessage:
    topic = None
    payload = None

    def __init__(self, srcTopic, srcPayload):
        self.topic = srcTopic
        self.payload = srcPayload
