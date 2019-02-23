import os
from typing import Dict, Optional

from models.language import Language


class CommandProvider:
    _storage: Dict[str, Language]

    def __init__(self):
        self._storage = dict()

    def get_run_command(self, filename: str) -> Optional[str]:
        language = self._get_language_by_filename(filename)
        if language is None:
            return None
        command = language.run_command.replace('<filename>', filename)
        return command

    def get_compile_command(self, filename) -> Optional[str]:
        language = self._get_language_by_filename(filename)
        if language is None:
            return None
        command = language.compile_command.replace('<filename>', filename)
        return command

    def add_languages(self, *data) -> None:
        for entry in data:
            language = Language.from_dict(entry)
            self._storage[language.extension] = language

    def _get_language_by_filename(self, filename: str) -> Language:
        _, file_extension = os.path.splitext(filename)
        language = self._storage.get(file_extension, None)
        return language

