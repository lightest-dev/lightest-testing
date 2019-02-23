class Settings:
    checker_folder: str
    ip: str
    tests_folder: str
    api_server: str
    max_tries: int

    def __init__(self):
        self.api_server = ''
        self.checker_folder = ''
        self.tests_folder = ''
        self.ip = ''
        self.max_try_time = 0

    @classmethod
    def from_json(cls, data):
        s = cls()
        s.api_server = data['apiServer']
        if not s.api_server.endswith('/'):
            s.api_server = s.api_server+'/'
        s.checker_folder = data['checkerFolder']
        s.tests_folder = data['testsFolder']
        s.max_try_time = data['maxTryTime']
        return s
