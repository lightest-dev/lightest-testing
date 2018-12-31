from checker import code_checker

checker = code_checker("")
memory_limit = 128*1028*1024
result = checker.compile("./testing/sum.cpp")
result = checker.__run_command__("./compiled.run", 0.1, memory_limit, 0)
checker.__parse_log__()
result = checker.compile("./testing/infinite.cpp")
result = checker.__run_command__("./compiled.run", 0.1, memory_limit, 0)
result = checker.compile("./testing/sleep.cpp")
result = checker.__run_command__(
    "./compiled.run", 0.1, memory_limit)
memory_limit = 2
