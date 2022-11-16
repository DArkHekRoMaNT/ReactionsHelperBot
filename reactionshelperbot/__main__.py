import logging
import os

from dotenv import load_dotenv

from .bot import ReactionsHelper
from .logger import setup_logger
from .settings import Settings

_log = logging.getLogger('reactionshelperbot')


def main():
    setup_logger()

    load_dotenv()
    token = os.getenv('REACTIONS_HELPER_TOKEN')
    if not token:
        _log.error('Token is not found. Specify REACTIONS_HELPER_TOKEN '
                   'in environment variables or .env file')
        return

    config_filepath = os.path.join(os.path.expanduser('~'), '.reactionshelperbot.json')
    config = Settings.load_or_create(config_filepath)
    config.save(config_filepath)
    bot = ReactionsHelper(config_filepath=config_filepath, config=config)
    bot.run(token)


if __name__ == '__main__':
    main()
