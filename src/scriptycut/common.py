# -*- coding: utf-8 -*-

from typing import Union
from pathlib import Path
from sys import platform
from enum import IntFlag, auto
from os import environ


Pathlike = Union[Path, str]
FPS = Union[int, float, str]


threads_num = int(environ.get("THREADS", "1"))


def popen_config(show_window: bool) -> dict:
    # TODO: Really needed?
    kwargs = {}

    if platform.startswith("win"):
        from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW
        si = STARTUPINFO()
        si.dwFlags |= STARTF_USESHOWWINDOW
        si.wShowWindow = int(show_window)
        kwargs["startupinfo"] = si

    return kwargs


class Layer(IntFlag):
    NONE = 0
    A = auto()
    V = auto()
    AV = A + V
