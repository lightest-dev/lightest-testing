class Upload():
    def __init__(self, upload_json):
        """Parses user upload json

        Arguments:
            upload_json {dict} -- dict with upload configuration
        """
        self.id = upload_json['UploadId']
        # convert memory to bytes from MB
        self.memory = upload_json['MemoryLimit'] * (2**20)
        self.time = upload_json['TimeLimit']
        self.tests_count = upload_json['TestsCount']
        self.checker_id = upload_json['CheckerId']
        self.received_tests = 0
