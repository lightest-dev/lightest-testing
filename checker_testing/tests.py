from .. import checker

checker = checker.CodeChecker("./checkers")
memory_limit = 128*1028*1024
result = checker.compile_checker('integer')
result = checker.compile('./testing/sum_console.cpp')
result = checker.run_checker(
    'integer', './testing/sum_tests', memory_limit, 0.1)
result = checker.compile("./testing/sum.cpp")
result = checker._run_command("./compiled.run", 0.1, memory_limit, 0)
checker._parse_log()
result = checker.compile("./testing/infinite.cpp")
result = checker._run_command("./compiled.run", 0.1, memory_limit, 0)
result = checker.compile("./testing/sleep.cpp")
result = checker._run_command(
    "./compiled.run", 0.1, memory_limit)
memory_limit = 2
