import os
import json
import asyncio
import uuid
import logging
from checker import CodeChecker
from models import Status, Settings, File, Upload
from models.limits import Limits
from sender import Sender


class Server:
    _sender: Sender
    _status: Status
    _code_checker: CodeChecker
    _upload: Upload
    _settings: Settings

    def __init__(self, settings: Settings, checker: CodeChecker, sender: Sender):
        logging.info('Creating server')
        self._upload = None
        self._settings = settings
        self._code_checker = checker
        self._status = Status.Free
        self._sender = sender

    async def start(self):
        logging.info('Starting server')
        if not os.path.exists(self._settings.tests_folder):
            os.makedirs(self._settings.tests_folder)
        asyncio.create_task(self._sender.notify_started())
        server = await asyncio.start_server(self._read_data, port=10000)
        await server.serve_forever()

    async def _read_data(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if self._status == Status.Free:
            self._status = Status.Transferring
        try:
            length_bytes = await reader.read(8)
            length = int.from_bytes(
                length_bytes, byteorder='little', signed=True)
            type_bytes = await reader.read(1)
            request_type = int.from_bytes(
                type_bytes, byteorder='little', signed=True)
            length -= 1
            logging.info(f"Type: {request_type}. Length {length}")

            if request_type == 1:
                chunk = await reader.read(length)
                message = chunk.decode(encoding='utf-8')
                await self._parse_json(message)
            elif request_type == 2:
                await self._parse_file_metadata(reader, length)
            elif request_type == 4:
                await self._sender.send_status(self._status)
        except Exception as e:
            logging.error(e)
            await self._sender.send_error(e)
        finally:
            writer.close()

    async def _parse_file_metadata(self, reader: asyncio.StreamReader, length: int):
        # parses file metadata from stream
        temp_file = str(uuid.uuid4())
        length_bytes = await reader.read(4)
        length -= 4
        message_length = int.from_bytes(
            length_bytes, byteorder='little', signed=True)
        chunk = await reader.read(message_length)
        message = chunk.decode(encoding='utf-8')
        logging.info(f"Message: {message}.")
        in_json = json.loads(message)
        current_file = File(in_json)
        length -= len(chunk)
        successful = await self._write_file(reader, length, temp_file)
        if successful:
            await self._process_file(current_file, temp_file)

    @staticmethod
    async def _write_file(reader: asyncio.StreamReader, length: int, filename: str):
        # writes file from stream to drive
        logging.info(f"Writing {filename}, length {length}.")
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
                logging.error(f'Failed to write {filename}.')
                f.close()
                os.remove(filename)
                return False

    async def _process_file(self, current_file: File, temp_file: str):
        file = current_file.filename
        file_type = current_file.type
        logging.info(f'Processing file {file}, type: {file_type}.')
        if file_type == 'code':
            await self._wait_upload()
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

    async def _check(self, upload_file: str):
        ready = await self._ensure_ready()
        if not ready:
            message = {
                'failedTests': self._upload.tests_count,
                'successfulTests': 0,
                'message': 'Only {} of {} tests were transferred!'.format(self._upload.received_tests,
                                                                          self._upload.tests_count * 2),
                'status': 'Transfer error',
                'type': 'Code',
                'uploadId': self._upload.id
            }
            return await self._send_result(message)

        logging.info(f'Compiling file {upload_file}')
        self._status = Status.Compiling
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
            return await self._send_result(message)

        logging.info('Running checker')
        self._status = Status.Testing
        result = self._code_checker.run_checker(
            self._upload.checker_id, upload_file,
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
            return await self._send_result(message)
        message = {
            'failedTests': result['failed_tests'],
            'successfulTests': result['passed_tests'],
            'message': '',
            'status': 'Ok',
            'type': 'Code',
            'uploadId': self._upload.id
        }
        return await self._send_result(message)

    async def _parse_json(self, text: str):
        """Parses json provided by user

        Arguments:
            text {string} -- text of json data
        """
        logging.info(f'Parsing message {text}')
        in_json = json.loads(text)
        if in_json['Type'] == 'upload':
            self._upload = Upload(in_json)
        # checker code is passed in json
        elif in_json['Type'] == 'checker':
            await self._parse_checker(in_json)

    async def _parse_checker(self, checker_json: dict):
        """Parses checker description and compiles it

        Arguments:
            checker_json {dict} -- dict with checker_id and code of checker
        """
        self._status = Status.Compiling
        checker_id = checker_json['Id']
        path = os.path.join(self._settings.checker_folder,
                            checker_id + '.cpp')
        f = open(path, 'w+')
        f.write(checker_json['Code'])
        f.close()
        logging.info(f'Compiling checker: {checker_id}')
        result = self._code_checker.compile_checker(checker_id)
        result['checker_id'] = checker_id
        self._status = Status.Free
        await self._sender.send_message(result, 'checker-result')

    async def _clean_tests(self):
        """Deletes all files in tests folder

        Arguments:
            tests_json {dict} -- ignored
        """
        logging.info('Cleaning tests')
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
        while self._upload.tests_count * 2 != self._upload.received_tests:
            if tries == self._settings.max_try_time:
                logging.error(f'Tests not uploaded for {self._upload.id}')
                return False
            tries += 1
            await asyncio.sleep(1)

        # wait for checker to finish compiling
        tries = 0
        while self._code_checker.checker_compiling:
            if tries == self._settings.max_try_time:
                # should never actually get here
                logging.error(f'Checker not compiled for {self._upload.id}')
                return False
            tries += 1
            await asyncio.sleep(1)
        return True

    async def _wait_upload(self):
        tries = 0
        while self._upload is None:
            if tries == self._settings.max_try_time:
                logging.error(f'Upload manifest not transferred.')
                return False
            tries += 1
            await asyncio.sleep(1)

    async def _send_result(self, message: dict):
        self._upload = None
        self._status = Status.Free
        return await self._sender.send_message(message, 'result')
