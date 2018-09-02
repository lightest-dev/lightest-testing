from benchexec.runexecutor import RunExecutor
import os


class code_checker():
    def __init__(self, checker_folder):
        self.checker_folder = checker_folder

    def run_command(self, command, memory, time):
        executor = RunExecutor()
        return ""
        # result = executor.execute_run(args=[<TOOL_CMD>], ...)

    def compile(self, filename):
        _, file_extension = os.path.splitext(filename)
        if file_extension == "cpp":
            result = self.run_command("g++ -O2 -std=c++14 " + filename +
                                      " -o compiled.run", 0, 30000)
            return result
        elif file_extension == "c":
            result = self.run_command("g++ -O2 -std=c11 " + filename +
                                      " -o compiled.run", 0, 30000)
            return result
        elif file_extension == "py":
            return {"error": ""}
        return {"error": "Unknown format!"}

    def run_checker(self, checker_name, result_path, memory, time):
        checker_path = os.path.join(self.checker_folder, checker_name + ".run")
        result = self.run_command(checker_path + " --testset " +
                                  result_path, memory, time)
        # parse result
        return ""

    def compile_checker(self, name):
        path = os.path.join(self.checker_folder, name)
        result = self.run_command("g++ -I" + self.checker_folder + " -O2 -std=c++11 " + path +
                                  " -o " + name + ".run", 0, 30000)
        # parse result
        return ""
