# -*- coding: utf-8 -*-

from typing import Union
from pathlib import Path
from sys import platform
from enum import IntFlag, auto
from os import environ


Pathlike = Union[Path, str]


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


class FPS:
    """
    Representation of a framerate (fps).
    Floats are bad here... Avoid as input?

    int: 60
    str: "30000/1001"
    """
    def __init__(self, fps: Union[int, str]):
        self._fps = fps

        if isinstance(fps, int):
            self._as_float = float(fps)
        elif isinstance(fps, str):
            pass
        else:
            raise TypeError("FPS must be defined exactly. Define them as int or fractional representation in a string.")

    def as_float(self) -> float:
        return self._as_float

    def __eq__(self, other):
        pass
