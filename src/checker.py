from benchexec.runexecutor import RunExecutor
from benchexec.check_cgroups import check_cgroup_availability
import os
from glob import glob
from command_provider import CommandProvider
from models import Settings
from models.limits import Limits
from models.status import Status


class CodeChecker:
    def __init__(self, settings: Settings, limits: Limits, command_provider: CommandProvider):
        """Creates new instance

        Arguments:
            checker_folder {str} -- path to folder with checkers
            tests_folder {str} -- path to folder with tests
        """
        check_cgroup_availability()
        self.checker_folder = settings.checker_folder
        self._data_folder = settings.tests_folder
        self._command_provider = command_provider
        self.status = Status.Free
        self._limits = limits
        self._output_log_file = 'run.log'
        self._output_file = './temp.out'
        self._separator = '--------------------------------------------------------------------------------'

    def _run_command(self, command: str, time: float, memory=None, file_count=None, stdin=None):
        """Runs specified command

        Arguments:
            command {str} -- command to be run
            time {float} -- time limit in seconds

        Keyword Arguments:
            memory {int} -- memory limit in bytes (default: {None})
            file_count {int} -- maximum number of files to write (default: {None})
            stdin {file} -- file used as standard input (default: {None})

        Returns:
            OrderedDict -- dict with results
        """
        executor = RunExecutor()
        if memory is None:
            memory = self._limits.max_memory
        args = command.split(' ')
        try:
            result = executor.execute_run(
                args, self._output_log_file, memlimit=memory, hardtimelimit=time,
                files_count_limit=file_count, stdin=stdin)
            if 'cputime' in result and result['cputime'] > time:
                result['terminationreason'] = 'cputime'
        except:
            result = {'terminationreason': 'something went very wrong'}
        return result

    def compile(self, filename: str) -> dict:
        """Compiles specified file

        Arguments:
            filename {str} -- Name of file to compile

        Returns:
            dict -- dictionary with code or error
        """
        self.status = Status.Compiling
        command = self._command_provider.get_compile_command(filename)
        if command is None:
            result = {
                'error': 'No suitable compiler found'
            }
            self.status = Status.Free
            return result
        result = self._run_command(command, self._limits.compilation_time)
        if 'terminationreason' in result or result['exitcode'] != 0:
            if self._copy_log():
                result = {'error': self._get_log()}
            else:
                result = {'error': 'Compilation failed'}
        self.status = Status.Free
        return result

    def run_checker(self, checker_name: str, upload: str, memory: int, time: float) -> dict:
        """Runs checker

        Arguments:
            checker_name {str} -- checker name without extension
            data_path {str} -- path to input and output files
            memory {int} -- memory limit in bytes
            time {float} -- time limit in seconds after which process is forcefully killed

        Returns:
            dict -- dictionary with passed_tests and failed_tests or with error if there is error with tests
        """
        self.status = Status.Testing
        checker_path = os.path.join(self.checker_folder, checker_name + ".run")
        if not os.path.isfile(checker_path):
            result = {'error': 'Checker is missing'}
            self.status = Status.Free
            return result
        input_file_format = os.path.join(self._data_folder, '*.in')
        input_files = glob(input_file_format)
        failed_tests = 0
        passed_tests = 0
        for filename in input_files:
            file_path, _ = os.path.splitext(filename)
            output_file = file_path + '.out'
            if not os.path.isfile(output_file):
                result = {'error': 'Output file for test is missing'}
                self.status = Status.Free
                return result
            output_found = self._run_upload(upload, memory, time, filename)
            if not output_found:
                failed_tests += 1
                continue
            test_result = self._run_test(
                checker_path, filename, output_file)
            if 'error' in test_result:
                failed_tests += 1
            elif 'code' in test_result and test_result['code'] == 0:
                passed_tests += 1
            else:
                failed_tests += 1
        result = {
            'passed_tests': passed_tests,
            'failed_tests': failed_tests
        }
        self.status = Status.Free
        return result

    def _run_test(self, checker: str, input_path: str, output_path: str) -> dict:
        """Runs checker for specified files

        Arguments:
            checker {str} -- name of checker
            input_path {str} -- name of input file
            output_path {str} -- name of correct output file

        Returns:
            dict -- dictionary with error or exit code
        """
        result = self._run_command(" ".join([checker, input_path, self._output_file, output_path]),
                                   self._limits.compilation_time, file_count=0)
        result = {'code': result['exitcode']}
        if 'terminationreason' in result:
            result['error'] = 'Checker is not working'
        return result

    def _run_upload(self, upload: str, memory: int, time: float, input_path: str) -> bool:
        """Runs checker for specified files

        Arguments:
                upload {str} -- name of upload
                memory {int} -- memory limit in bytes
                time {float} -- time limit in seconds

        Returns:
            dict -- dictionary with error or exit code
        """
        command = self._command_provider.get_run_command(upload)
        with open(input_path, "r") as input_stream:
            self._run_command(
                command, time,
                memory=memory, file_count=1, stdin=input_stream)
        result_exists = self._copy_log()
        return result_exists

    def compile_checker(self, name: str) -> dict:
        """Compiles checker

        Arguments:
            name {string} -- name of checker to compile

        Returns:
            dict -- dictionary with error or exitcode
        """
        self.status = Status.CompilingChecker
        path = os.path.join(self.checker_folder, name + '.cpp')
        result_path = os.path.join(self.checker_folder, name + '.run')
        result = self._run_command("g++ -I " + self.checker_folder + " -O2 -std=c++11 " + path +
                                   " -o " + result_path, self._limits.compilation_time)
        code = result['exitcode']
        compilation_result = {
            'compiled': code == 0,
            'message': ''
        }
        if 'terminationreason' in result:
            compilation_result['message'] = result['terminationreason']
        elif code != 0:
            if self._copy_log():
                compilation_result['message'] = self._get_log()
            else:
                compilation_result['message'] = 'Something went wrong with checker!'
        self.status = Status.Free
        return compilation_result

    def _copy_log(self) -> bool:
        """Copies output from temp file to output file

        Returns:
            boolean -- if any content was copied
        """
        log_end_found = False
        content_found = False
        with open(self._output_log_file, 'r') as log, open(self._output_file, 'w') as output:
            content = log.readlines()
            for line in content:
                if content_found:
                    output.write(line)
                elif log_end_found:
                    stripped = line.strip()
                    if stripped:
                        content_found = True
                        output.write(line)
                elif line.strip() == self._separator:
                    log_end_found = True
        return content_found

    def _get_log(self) -> str:
        """Returns config from copied log

        Returns:
            str -- content of copied log
        """
        with open(self._output_file, 'r') as output:
            data = output.read()
        return data
