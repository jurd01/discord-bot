import logging
import os

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

logger = logging.getLogger()
logger.setLevel(level='DEBUG')

logger.addHandler(logging.StreamHandler())  # print to stdout
