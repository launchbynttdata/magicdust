# Required by python
import logging


def get_logger(name):
    logging.basicConfig(format="[%(levelname)s] %(asctime)s [%(name)s]  %(message)10s")
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
