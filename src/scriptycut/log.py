# -*- coding: utf-8 -*-

import logging
from os import environ

_filename = environ.get("LOGFILE")
_loglevel = environ.get("LOGLEVEL", logging.WARNING)

logging.basicConfig(
    filename=_filename,
    level=_loglevel,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
