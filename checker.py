from benchexec.runexecutor import RunExecutor
import os


class code_checker():
    def __init__(self, checker_folder):
        self.checker_folder = checker_folder

    def run_command(self, command, time, memory=None, file_count=None, stdin=None):
        """
        @param command: command to be run
        @param memory: memory limit in bytes
        @param time: time limit in seconds after which process is forcefully killed
        @param file_count: maximum number of file the process can write
        @param stdin: file used as standard input
        """
        executor = RunExecutor()
        try:
            result = executor.execute_run(
                command, "run.log", memlimit=memory, hardtimelimit=time, files_count_limit=file_count, stdin=stdin)
            return result
        except:
            # todo: check result value and return some error
            return None

    def compile(self, filename):
        _, file_extension = os.path.splitext(filename)
        if file_extension == "cpp":
            result = self.run_command("g++ -O2 -std=c++14 " + filename +
                                      " -o compiled.run", 30000)
            return result
        elif file_extension == "c":
            result = self.run_command("g++ -O2 -std=c11 " + filename +
                                      " -o compiled.run", 30000)
            return result
        elif file_extension == "py":
            return {"error": ""}
        return {"error": "Unknown format!"}

    def run_checker(self, checker_name, data_path, memory, time):
        checker_path = os.path.join(self.checker_folder, checker_name + ".run")
        # todo: parse files in data_path, run tests for each file
        # parse result
        return ""

    def run_test(self, checker, input_path, output_path, memory, time):
        input = os.open(input_path, "r")
        result = self.run_command(
            "compiled.run > temp.out", time,
            memory=memory, file_count=1, stdin=input)
        input.close()
        # check if run is ok
        result = self.run_command(" ".join([checker, input_path, "temp.out", output_path]), time,
                                  memory=memory, file_count=0)
        # parse result
        return result

    def compile_checker(self, name):
        path = os.path.join(self.checker_folder, name)
        result = self.run_command("g++ -I" + self.checker_folder + " -O2 -std=c++11 " + path +
                                  " -o " + name + ".run", 0, 30000)
        # parse result
        return result
