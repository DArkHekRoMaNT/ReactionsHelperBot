import logging
import os

from .bot import ReactionsHelper
from .logger import setup_logger
from .settings import Settings

_log = logging.getLogger('reactionshelperbot')


def main():
    setup_logger()
    config_filepath = os.path.join(os.path.expanduser('~'), '.reactionshelperbot.json')
    config = Settings.load_or_create(config_filepath)
    config.save(config_filepath)
    bot = ReactionsHelper(config_filepath=config_filepath, config=config)
    bot.run_with_token()


if __name__ == '__main__':
    main()
