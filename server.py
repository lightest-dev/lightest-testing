import requests
import os
import json
import asyncio
import uuid
from checker import CodeChecker
from models.upload import Upload
from models.sent_file import File
from hasher import get_server_hash


class Server:
    def __init__(self, settings):
        self.max_tries = 5
        self._upload = None
        self._settings = settings
        self._code_checker = CodeChecker(self._settings.checker_folder)

    async def start(self):
        await self._notify_started()
        server = await asyncio.start_server(self._read_data, 'localhost', 10000)
        await server.serve_forever()

    async def _notify_started(self):
        hash = get_server_hash()
        message = {
            'serverVersion': hash
        }
        await self._send_message(message, 'free')

    async def _read_data(self, reader, writer):
        # todo: resolve race conditions
        # should be resolved but left here just in case
        length_bytes = await reader.read(8)
        length = int.from_bytes(length_bytes, byteorder='little', signed=True)
        type = await reader.read(1)
        length -= 1

        if type == 1:
            chunk = await reader.read(length)
            message = chunk.decode(encoding='utf-8')
            await self._parse_json(message)
        elif type == 2:
            await self._parse_file(reader, length)
        writer.close()

    async def _parse_file(self, reader, length):
        temp_file = str(uuid.uuid4())
        length_bytes = await reader.read(4)
        length -= 4
        message_length = int.from_bytes(
            length_bytes, byteorder='little', signed=True)
        chunk = await reader.read(message_length)
        message = chunk.decode(encoding='utf-8')
        in_json = json.loads(message)
        current_file = File(in_json)
        length -= len(chunk)
        successful = await self._read_file(reader, length, temp_file)
        if successful:
            await self._process_file(current_file, temp_file)

    async def _read_file(self, reader, length, filename):
        f = open(filename, "wb+")
        bytes_read = 0
        while True:
            to_read = 2048
            if length - bytes_read < to_read:
                to_read = length - bytes_read
            chunk = await reader.read(to_read)
            read = len(chunk)
            bytes_read += read
            if read:
                f.write(chunk)
                if bytes_read == length:
                    f.close()
                    return True
            else:
                f.close()
                os.remove(filename)
                return False

    async def _process_file(self, current_file, temp_file):
        await self._wait_upload()
        file = current_file.filename
        file_type = current_file.type
        if file_type == 'code':
            _, ext = os.path.splitext(file)
            path = os.path.join('./', self._upload.id + ext)
            os.rename(temp_file, path)
            await self._check(path)
        elif file_type == 'test':
            path = os.path.join(self._settings.tests_folder, file)
            if self._upload.received_tests == 0:
                await self._clean_tests()
                os.rename(temp_file, path)
                self._upload.received_tests += 1

    async def _check(self, upload_file):
        ready = await self._ensure_ready()
        if not ready:
            message = {
                'failedTests': self._upload.tests_count,
                'successfulTests': 0,
                'message': 'Only {} of {} tests were transfered!'.format(self._upload.received_tests, self._upload.tests_count * 2),
                'status': 'Transfer error',
                'type': 'Code',
                'uploadId': self._upload.id
            }
            self._upload = None
            await self._send_message(message, 'result')
            return

        compile_result = self._code_checker.compile(upload_file)
        if 'error' in compile_result:
            message = {
                'failedTests': self._upload.tests_count,
                'successfulTests': 0,
                'message': compile_result['error'],
                'status': 'Compilation error',
                'type': 'Code',
                'uploadId': self._upload.id
            }
            self._upload = None
            await self._send_message(message, 'result')
            return
        result = self._code_checker.run_checker(
            self._upload.checker_id, self._settings.tests_folder,
            self._upload.memory, self._upload.time)
        if 'error' in result:
            message = {
                'failedTests': self._upload.tests_count,
                'successfulTests': 0,
                'message': result['error'],
                'status': 'Test error',
                'type': 'Code',
                'uploadId': self._upload.id
            }
            self._upload = None
            await self._send_message(message, 'result')
            return
        message = {
            'failedTests': result['failed_tests'],
            'successfulTests': result['passed_tests'],
            'message': '',
            'status': 'Ok',
            'type': 'Code',
            'uploadId': self._upload.id
        }
        self._upload = None
        await self._send_message(message, 'result')

    async def _send_message(self, data, endpoint):
        """Sends result to remote server

        Arguments:
            data {dict} -- json to send to remote
            endpoint {string} -- endpoint to send data to
        """
        tries = 0
        r = requests.post(self._settings.api_server + endpoint, json=data)
        while r.status_code != 200:
            if tries == self.max_tries:
                break
            await asyncio.sleep(5)
            tries += 1
            r = requests.post(self._settings.api_server + endpoint, json=data)

    async def _parse_json(self, text):
        """Parses json provided by user

        Arguments:
            text {string} -- text of json data
        """
        in_json = json.loads(text)
        if in_json['type'] == 'upload':
            self._upload = Upload(in_json)
        # checker code is passed in json
        elif in_json['type'] == 'checker':
            await self._parse_checker(in_json)

    async def _parse_checker(self, checker_json):
        """Parses checker description and compiles it

        Arguments:
            checker_json {dict} -- dict with id and code of checker
        """
        path = os.path.join(self._settings.checker_folder, checker_json['id'])
        f = open(path, 'w+')
        f.write(checker_json['code'])
        result = self._code_checker.compile_checker(checker_json['id'])
        result['id'] = checker_json['id']
        await self._send_message(result, 'checker-result')

    async def _clean_tests(self):
        """Deletes all files in tests folder

        Arguments:
            tests_json {dict} -- ignored
        """
        for file in os.listdir(self._settings.tests_folder):
            file_path = os.path.join(self._settings.tests_folder, file)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(e)

    async def _ensure_ready(self):
        """Waits until checker compilation and test upload is finished

        Returns:
            bool -- if system is ready to start testing
        """
        # wait for all tests to finish uploading
        tries = 0
        max_tries = self.max_tries * 5
        while self._upload.tests_count * 2 != self._upload.received_tests:
            if tries == max_tries:
                return False
            tries += 1
            await asyncio.sleep(1)

        # wait for checker to finish compiling
        tries = 0
        max_tries = self._code_checker.checker_compilation_max_time
        while self._code_checker.checker_compiling:
            if tries == max_tries:
                # should never actually get here
                return False
            tries += 1
            await asyncio.sleep(1)
        return True

    async def _wait_upload(self):
        tries = 0
        max_tries = self.max_tries * 5
        while self._upload is None:
            if tries == max_tries:
                return False
            tries += 1
            await asyncio.sleep(1)
