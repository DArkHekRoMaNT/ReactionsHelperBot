import logging


def setup_logger():
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    file_handler = logging.FileHandler(
        filename='discord.log',
        encoding='utf-8',
        mode='w'
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    logging.getLogger('discord').setLevel(logging.DEBUG)
    logging.getLogger('reactionshelperbot').addHandler(stream_handler)
