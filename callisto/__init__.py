# -*- coding: utf-8 -*-

import logging

logging_fmt = "%(asctime)s %(levelname)s %(name)s :%(message)s"
logging.basicConfig(level=logging.DEBUG, format=logging_fmt)


def get_logger(name):
    return logging.getLogger(name)
