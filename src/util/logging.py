import logging
import os

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

ANSI_WHITE = '\033[37m'
ANSI_RESET = '\033[0m'


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(level=LOG_LEVEL)

    formatter = logging.Formatter(f'{ANSI_WHITE}%(levelname)s [%(asctime)s] %(filename)s: %(message)s{ANSI_RESET}',
                                  '%Y-%m-%d %H:%M:%S')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
