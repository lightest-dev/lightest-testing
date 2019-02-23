class Limits:
    max_memory: int
    compilation_time: float

    def __init__(self):
        self.compilation_time = 0.0
        self.max_memory = 0

    @classmethod
    def from_json(cls, data):
        s = cls()
        s.compilation_time = data['compilationTime']
        s.max_memory = data['maxMemory'] * 2**20
        return s
