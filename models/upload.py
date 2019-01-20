class upload():
    def __init__(self, upload_json):
        """Parses user upload json

        Arguments:
            upload_json {dict} -- dict with upload configuration
        """
        self.id = upload_json['uploadId']
        self.memory = upload_json['memoryLimit']
        self.time = upload_json['timeLimit']
        self.tests_count = upload_json['testsCount']
        self.checker_id = upload_json['checkerId']
        self.received_tests = 0
