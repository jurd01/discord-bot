import logging
import os

DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

RESET = '\033[0m'

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = [f'\033[3{i}m' for i in range(8)]

_LEVEL_COLORS = {
    'DEBUG': CYAN,
    'INFO': GREEN,
    'WARNING': YELLOW,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class ColorFormatter(logging.Formatter):
    def __init__(self):
        thread = ' tid=%(thread)s' if LOG_LEVEL == 'DEBUG' else ''
        super().__init__(f'{BLUE}[%(asctime)s]%(filename)s{thread} : %(levelname)s %(message)s{RESET}',
                         DATETIME_FMT)

    def format(self, record):
        level = record.levelname
        color = _LEVEL_COLORS[level]
        record.levelname = color + record.levelname

        # weird bug in formatter ->
        return logging.Formatter.format(self, record)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(level=LOG_LEVEL)

    formatter = ColorFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
