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
from models import upload, sent_file


class server():
    def __init__(self, api_server, checker_folder, tests_folder):
        if not api_server.endswith('/'):
            api_server = api_server+'/'
        self.api_server = api_server
        self.max_tries = 5
        self.upload = None
        self.current_file = None
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
        # should be resolved but left here just in case
        temp_file = str(uuid.uuid4())
        f = open(temp_file, "wb+")
        type = 0
        length_bytes = await reader.read(4)
        length = int.from_bytes(length_bytes, byteorder='little', signed=True)
        type = await reader.read(1)
        length = length - 1
        bytes_read = 0

        while True:
            to_read = 128
            if length - bytes_read < to_read:
                to_read = length - bytes_read
            chunk = await reader.read(to_read)
            read = len(chunk)
            bytes_read += read
            if read:
                f.write(chunk)
                if bytes_read == length:
                    f.close()
                    await self.process_data(type, temp_file)
                    break
            else:
                f.close()
                os.remove(temp_file)
                break

    async def process_data(self, type, temp_file):
        # json
        if type == 1:
            str = ""
            with open(temp_file, 'r') as myfile:
                str = myfile.read().replace('\n', '')
            if str.startswith("{"):
                await self.__parse_json__(str)
        # file
        elif type == 2:
            file = self.current_file.filename
            file_type = self.current_file.type
            if file_type == 'code':
                _, ext = os.path.splitext(file)
                path = os.path.join('./', self.upload.id + ext)
                os.rename(temp_file, path)
                await self.__check__(path)
            elif file_type == 'test':
                path = os.path.join(self.tests_folder, file)
                if self.upload.received_tests == 0:
                    await self.__clean_tests__()
                os.rename(temp_file, path)
                self.upload.received_tests += 1

    async def __check__(self, upload_file):
        ready = await self.__ensure_ready__()
        if not ready:
            message = {
                'failedTests': self.upload.tests_count,
                'successfulTests': 0,
                'message': 'Only {} of {} tests were transfered!'.format(self.upload.received_tests, self.upload.tests_count * 2),
                'status': 'Transfer error',
                'type': 'Code',
                'uploadId': self.upload.id
            }
            await self.send_result(message, 'result')
            return

        compile_result = self.code_checker.compile(upload_file)
        if 'error' in compile_result:
            message = {
                'failedTests': self.upload.tests_count,
                'successfulTests': 0,
                'message': compile_result['error'],
                'status': 'Compilation error',
                'type': 'Code',
                'uploadId': self.upload.id
            }
            await self.send_result(message, 'result')
            return
        result = self.code_checker.run_checker(
            self.upload.checker_id, self.tests_folder,
            self.upload.memory, self.upload.time)
        if 'error' in result:
            message = {
                'failedTests': self.upload.tests_count,
                'successfulTests': 0,
                'message': result['error'],
                'status': 'Test error',
                'type': 'Code',
                'uploadId': self.upload.id
            }
            await self.send_result(message, 'result')
            return
        message = {
            'failedTests': result['failed_tests'],
            'successfulTests': result['passed_tests'],
            'message': '',
            'status': 'Ok',
            'type': 'Code',
            'uploadId': self.upload.id
        }
        await self.send_result(message, 'result')

    async def send_result(self, data, endpoint):
        """Sends result to remote server

        Arguments:
            data {dict} -- json to send to remote
            endpoint {string} -- endpoint to send data to
        """
        tries = 0
        r = requests.post(self.api_server + endpoint, json=data)
        while r.status_code != 200:
            if tries == self.max_tries:
                break
            await asyncio.sleep(5)
            tries += 1
            r = requests.post(self.api_server + endpoint, json=data)

    async def __parse_json__(self, text):
        """Parses json provided by user

        Arguments:
            text {string} -- text of json data
        """
        in_json = json.loads(text)
        if in_json['type'] == 'upload':
            self.upload = upload.upload(in_json)
        # checker code is passed in json
        elif in_json['type'] == 'checker':
            await self.__parse_checker__(in_json)
        elif in_json['type'] == 'file':
            self.current_file = sent_file.file(in_json)

    async def __parse_checker__(self, checker_json):
        """Parses checker description and compiles it

        Arguments:
            checker_json {dict} -- dict with id and code of checker
        """
        path = os.path.join(self.checker_folder, checker_json['id'])
        f = open(path, 'w+')
        f.write(checker_json['code'])
        result = self.code_checker.compile_checker(checker_json['id'])
        result['id'] = checker_json['id']
        await self.send_result(result, 'checker-result')

    async def __clean_tests__(self):
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

    async def __ensure_ready__(self):
        """Waits until checker compilation and test upload is finished

        Returns:
            bool -- if system is ready to start testing
        """
        # wait for all tests to finish uploading
        tries = 0
        max_tries = self.max_tries * 5
        while self.upload.tests_count * 2 != self.upload.received_tests:
            if tries == max_tries:
                return False
            tries += 1
            await asyncio.sleep(1)

        # wait for checker to finish compiling
        tries = 0
        max_tries = self.code_checker.checker_compilation_max_time
        while self.code_checker.checker_compiling:
            if tries == max_tries:
                # should never actually get here
                return False
            tries += 1
            await asyncio.sleep(1)
        return True
