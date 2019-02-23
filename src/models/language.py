class Language:
    extension: str
    run_command: str
    compile_command: str

    def __init__(self):
        self.compile_command = ''
        self.run_command = ''
        self.extension = ''

    @classmethod
    def from_dict(cls, data):
        s = cls()
        s.compile_command = data['compileCommand']
        s.run_command = data['runCommand']
        s.extension = data['extension']
        return s
