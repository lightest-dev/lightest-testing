from benchexec.runexecutor import RunExecutor
from benchexec.check_cgroups import check_cgroup_availability
import os
from glob import glob


class CodeChecker:
    def __init__(self, checker_folder):
        """Creates new instance

        Arguments:
            checker_folder {string} -- path to folder with checkers
        """
        check_cgroup_availability()
        self.checker_folder = checker_folder
        # checker compilation can be long, can be used to wait for finish
        self.checker_compiling = False
        self.checker_compilation_max_time = 30
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
        args = command.split(' ')
        try:
            result = executor.execute_run(
                args, self._output_log_file, memlimit=memory, hardtimelimit=time, files_count_limit=file_count, stdin=stdin)
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
        _, file_extension = os.path.splitext(filename)
        if file_extension == ".cpp":
            result = self._run_command('g++ -O2 -std=c++14 ' + filename +
                                       ' -o compiled.run', 30000)
        elif file_extension == ".c":
            result = self._run_command("g++ -O2 -std=c11 " + filename +
                                       " -o compiled.run", 30000)
        elif file_extension == ".py":
            result = {"error": "python is not supported"}
        else:
            result = {"error": "Unknown format!"}
        if 'terminationreason' in result or result['exitcode'] != 0:
            if self._copy_log():
                result = {'error': self._get_log()}
            else:
                result = {'error': 'Compilation failed'}
        return result

    def run_checker(self, checker_name: str, data_path: str, memory: int, time: float) -> dict:
        """Runs checker

        Arguments:
            checker_name {str} -- checker name without extension
            data_path {str} -- path to input and output files
            memory {int} -- memory limit in bytes
            time {float} -- time limit in seconds after which process is forcefully killed

        Returns:
            dict -- dictionary with passed_tests and failed_tests or with error if there is error with tests
        """
        checker_path = os.path.join(self.checker_folder, checker_name + ".run")
        if not os.path.isfile(checker_path):
            result = {'error': 'Checker is missing'}
            return result
        input_file_format = os.path.join(data_path, '*.in')
        input_files = glob(input_file_format)
        failed_tests = 0
        passed_tests = 0
        for filename in input_files:
            file_path, _ = os.path.splitext(filename)
            output_file = file_path + '.out'
            if not os.path.isfile(output_file):
                result = {'error': 'Output file for test is missing'}
                return result
            test_result = self._run_test(
                checker_path, filename, output_file, memory, time)
            if 'error' in test_result:
                if test_result['error'] == 'Checker is not working':
                    return test_result
                failed_tests = failed_tests + 1
            elif 'code' in test_result and test_result['code'] == 0:
                passed_tests = passed_tests + 1
            else:
                failed_tests = failed_tests + 1
        result = {
            'passed_tests': passed_tests,
            'failed_tests': failed_tests
        }
        return result

    def _run_test(self, checker: str, input_path: str, output_path: str, memory: int, time: float) -> dict:
        """Runs checker for specified files

        Arguments:
            checker {str} -- name of checker
            input_path {str} -- name of input file
            output_path {str} -- name of correct output file
            memory {int} -- memory limit in bytes
            time {float} -- time limit in seconds

        Returns:
            dict -- dictionary with error or exit code
        """
        with open(input_path, "r") as input:
            self._run_command(
                "./compiled.run", time,
                memory=memory, file_count=1, stdin=input)
        result_exists = self._copy_log()
        if not result_exists:
            result = {'error': 'User output is empty'}
            return result
        result = self._run_command(" ".join([checker, input_path, self._output_file, output_path]), time,
                                   memory=memory, file_count=0)
        result = {'code': result['exitcode']}
        if 'terminationreason' in result:
            result['error'] = 'Checker is not working'
        return result

    def compile_checker(self, name: str) -> dict:
        """Compiles checker

        Arguments:
            name {string} -- name of checker to compile

        Returns:
            dict -- dictionary with error or exitcode
        """
        self.checker_compiling = True
        path = os.path.join(self.checker_folder, name + '.cpp')
        result_path = os.path.join(self.checker_folder, name + '.run')
        result = self._run_command("g++ -I " + self.checker_folder + " -O2 -std=c++11 " + path +
                                   " -o " + result_path, self.checker_compilation_max_time * 1000)
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
        self.checker_compiling = False
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
