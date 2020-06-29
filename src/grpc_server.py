from checker import CodeChecker
from models import Status
from protos.CodeTester_pb2 import *
from protos.CodeTester_pb2_grpc import CodeTesterServicer
from models.settings import Settings
import os
import logging


class GrpcServer(CodeTesterServicer):
    _code_checker: CodeChecker
    _settings: Settings

    def __init__(self, checker: CodeChecker, settings: Settings):
        self._code_checker = checker
        self._settings = settings

    def CompileChecker(self, request: CheckerRequest, context) -> CheckerResponse:
        if self._code_checker.status != Status.Free:
            raise RuntimeError('Server is not free')
        checker_id = request.id
        path = os.path.join(self._settings.checker_folder,
                            checker_id + '.cpp')
        with open(path, 'w') as checker_file:
            checker_file.write(request.code)
        logging.info(f'Compiling checker: {checker_id}')
        result = self._code_checker.compile_checker(checker_id)
        return CheckerResponse(id=checker_id, message=result['message'], compiled=result['compiled'])

    def GetStatus(self, request: CheckerStatusRequest, context) -> CheckerStatusResponse:
        status = self._code_checker.status
        is_free = status == Status.Free
        return CheckerStatusResponse(free=is_free, serverStatus=status.name)

    def TestUpload(self, request: TestingRequest, context) -> TestingResponse:
        if self._code_checker.status != Status.Free:
            raise RuntimeError('Server is not free')
        self._clean_tests()
        code_path = os.path.join('./', request.codeFile.fileName)
        with open(code_path, 'w') as code_file:
            code_file.write(request.codeFile.code)

        logging.info(f'Compiling file {code_path}')
        compile_result = self._code_checker.compile(code_path)
        if 'error' in compile_result:
            return TestingResponse(uploadId=request.uploadId, testingFailed=True, message=compile_result['error'],
                                   status='Compilation error', successfulTestsCount=0,
                                   failedTestsCount=len(request.tests))

        logging.info('Writing tests')
        for test in request.tests:
            input_path = os.path.join(
                self._settings.tests_folder, test.testName + '.in')
            output_path = os.path.join(
                self._settings.tests_folder, test.testName + '.out')
            with open(input_path, 'w') as input_file:
                input_file.write(test.input)
            with open(output_path, 'w') as output_file:
                output_file.write(test.output)

        logging.info('Running checker')
        result = self._code_checker.run_checker(
            request.checkerId, code_path,
            # convert memory to bytes from MB
            request.memoryLimit * (2**20),
            # convert time to s from ms
            request.timeLimit / 1000)

        if 'error' in result:
            return TestingResponse(uploadId=request.uploadId, testingFailed=True, message=result['error'],
                                   status='Testing error', successfulTestsCount=0,
                                   failedTestsCount=len(request.tests))
        return TestingResponse(uploadId=request.uploadId, testingFailed=False, message='',
                               status='Ok', successfulTestsCount=result['passed_tests'],
                               failedTestsCount=result['failed_tests'])

    def _clean_tests(self):
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
