class File():
    def __init__(self, file_json):
        """Parses json with file description

        Arguments:
            file_json {dict} -- dictionary with filename and type of file
        """
        self.filename = file_json['filename']
        self.type = file_json['fileType']
