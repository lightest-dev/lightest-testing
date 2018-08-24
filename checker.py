from benchexec.runexecutor import RunExecutor
import os
checker_folder = ""


def run_command(command, memory, time):
    executor = RunExecutor()
    return ""
    # result = executor.execute_run(args=[<TOOL_CMD>], ...)


def compile(filename):
    _, file_extension = os.path.splitext(filename)
    if file_extension == "cpp":
        result = run_command("g++ -O2 -std=c++14 " + filename +
                             " -o compiled.run", 0, 30000)
        return True
    elif file_extension == "c":
        result = run_command("g++ -O2 -std=c11 " + filename +
                             " -o compiled.run", 0, 30000)
        return True
    elif file_extension == "py":
        return True
    return False


def run_checker(checker_name, result_path, memory, time):
    checker_path = os.path.join(checker_folder, checker_name + ".run")
    result = run_command(checker_path + " --testset " +
                         result_path, memory, time)
    # parse result
    return
