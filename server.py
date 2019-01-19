import socket
import sys
import requests
import time
import os
import shutil
import checker
import json
import asyncio
import uuid


class server():
    def __init__(self, api_server, checker_folder, tests_folder):
        if not api_server.endswith('/'):
            api_server = api_server+'/'
        self.api_server = api_server
        self.max_tries = 5
        self.server_address = ('localhost', 10000)
        self.current_file = {}
        self.code_upload = ""
        self.memory = 0
        self.time = 0
        self.tests_count = 0
        self.checker_id = 0
        self.checker_folder = checker_folder
        self.tests_folder = tests_folder
        self.code_checker = checker.code_checker(self.checker_folder)

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(
            self.read_data, 'localhost', 10000))
        loop.run_forever()

    async def read_data(self, reader, writer):
        # todo: resolve race conditions
        temp_file = str(uuid.uuid4())
        f = open(temp_file, "wb+")
        type = 0
        length_bytes = await reader.read(4)
        length = int.from_bytes(length_bytes, byteorder='little', signed=True)
        type = await reader.read(1)
        length = length - 1
        bytes_read = 0

        while True:
            chunk = await reader.read(16)
            read = len(chunk)
            bytes_read += read
            if read:
                f.write(chunk)
                if bytes_read == length:
                    f.close()
                    self.process_data(type, temp_file)
                    break
            else:
                f.close()
                break

    def process_data(self, type, temp_file):
        # json
        if type == 1:
            str = ""
            with open(temp_file, 'r') as myfile:
                str = myfile.read().replace('\n', '')
            if str.startswith("{"):
                self.parse_json(str)
        # file
        elif type == 2:
            file = self.current_file['filename']
            file_type = self.current_file['type']
            if file_type == 'code':
                _, ext = os.path.splitext(file)
                path = os.path.join('./', self.code_upload + ext)
                os.rename(temp_file, path)
                self.check(path)
            elif file_type == 'test':
                path = os.path.join(self.tests_folder, file)
                os.rename(temp_file, path)

    def check(self, path):
        tests_count = 0
        compile_result = self.code_checker.compile(
            os.path.join(self.code_upload, path))
        if 'error' in compile_result:
            message = {
                'failedTests': tests_count,
                'successfulTests': 0,
                'message': compile_result['error'],
                'status': 'Compilation error',
                'type': 'Code',
                'uploadId': self.code_upload
            }
            self.send_result(message, 'result')
            return
        result = self.code_checker.run_checker(
            self.checker_id, self.tests_folder, self.memory, self.time)
        if 'error' in result:
            message = {
                'failedTests': tests_count,
                'successfulTests': 0,
                'message': result['error'],
                'status': 'Test error',
                'type': 'Code',
                'uploadId': self.code_upload
            }
            self.send_result(message, 'result')
            return
        message = {
            'failedTests': result['failed_tests'],
            'successfulTests': result['passed_tests'],
            'message': '',
            'status': 'Ok',
            'type': 'Code',
            'uploadId': self.code_upload
        }
        self.send_result(message, 'result')

    def send_result(self, data, endpoint, tries=0):
        """Sends result to remote server

        Arguments:
            data {dict} -- json to send to remote
            endpoint {string} -- endpoitn to send data to

        Keyword Arguments:
            tries {int} -- maximum atempts to send data (default: {0})
        """
        r = requests.post(self.api_server + endpoint, json=data)
        if r.status_code != 200:
            if tries == self.max_tries:
                return
            time.sleep(1)
            self.send_result(data, endpoint, tries + 1)
        return

    def parse_json(self, text):
        """Parses json provided by user

        Arguments:
            text {string} -- text of json data
        """
        in_json = json.loads(text)
        if in_json['type'] == 'upload':
            self.parse_upload(in_json)
        # checker code is passed in json
        elif in_json['type'] == 'checker':
            self.parse_checker(in_json)
        elif in_json['type'] == 'file':
            self.parse_file(in_json)
        # can be called to clean tests directory
        elif in_json['type'] == 'tests':
            self.parse_tests(in_json)

    def parse_checker(self, checker_json):
        """Parses checker description and compiles it

        Arguments:
            checker_json {dict} -- dict with id and code of checker
        """
        path = os.path.join(self.checker_folder, checker_json['id'])
        f = open(path, 'w+')
        f.write(checker_json['code'])
        result = self.code_checker.compile_checker(checker_json['id'])
        result['id'] = checker_json['id']
        self.send_result(result, 'checker-result')

    def parse_upload(self, upload_json):
        """Parses user upload json

        Arguments:
            upload_json {dict} -- dict with upload configuration
        """
        self.code_upload = upload_json['uploadId']
        self.memory = upload_json['memoryLimit']
        self.time = upload_json['timeLimit']
        self.tests_count = upload_json['testsCount']
        self.checker_id = upload_json['checkerId']

    def parse_file(self, file_json):
        """Parses json with file description

        Arguments:
            file_json {dict} -- dictionary with filename and type of file
        """
        # type: code, test
        self.current_file = {
            'filename': file_json['filename'],
            'type': file_json['fileType']
        }

    def parse_tests(self, tests_json):
        """Deletes all files in tests folder

        Arguments:
            tests_json {dict} -- ignored
        """
        for file in os.listdir(self.tests_folder):
            file_path = os.path.join(self.tests_folder, file)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(e)
