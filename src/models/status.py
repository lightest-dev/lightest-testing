from enum import Enum


class Status(Enum):
    Free = 1
    CompilingChecker = 2
    Compiling = 4
    Testing = 8
