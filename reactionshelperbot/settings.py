import io
import json
import logging

_log = logging.getLogger(__name__)


class Settings:
    def __init__(self):
        self.reactions = list()
        self.channels = list()
        self.command_prefix = '$'
        self.processing_reaction = '⏳'

    def __str__(self):
        return json.dumps(self, cls=SettingsEncoder, indent=2)

    def save(self, filename: str):
        with io.open(filename, 'w', encoding='utf-8') as file:
            file.write(str(self))

    @staticmethod
    def load(filename: str) -> 'Settings':
        with io.open(filename, 'r', encoding='utf-8') as file:
            json_data = file.read()
            data = Settings()
            data.__dict__ = json.loads(json_data)
            return data

    @staticmethod
    def load_or_create(filename: str) -> 'Settings':
        try:
            return Settings.load(filename)
        except (FileNotFoundError, json.JSONDecodeError):
            return Settings()


class SettingsEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Settings):
            return o.__dict__
        return json.JSONEncoder.default(self, o)
