import logging


def setup_logger():
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logging.getLogger('discord').setLevel(logging.DEBUG)
    logging.getLogger('reactionshelperbot').addHandler(stream_handler)
