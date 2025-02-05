# -*- coding: utf-8 -*-

from typing import Union, Optional
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
            self._numerator = int(fps)
            self._denominator = 1
        elif isinstance(fps, str):
            if "/" in fps:
                n_s, d_s = fps.split("/", maxsplit=1)
            else:
                n_s = fps
                d_s = "1"
            self._numerator = int(n_s)
            self._denominator = int(d_s)

        else:
            raise TypeError("FPS must be defined exactly. Define them as int or fractional representation in a string.")

        self._as_float = self._numerator / self._denominator

    @property
    def as_float(self) -> float:
        return self._as_float

    @property
    def frame_time(self) -> float:
        """
        Frame time in seconds (float).
        Be careful with floats and further calculations.
        """
        return self._denominator / self._numerator

    @property
    def numerator(self) -> int:
        return self._numerator

    @property
    def denominator(self) -> int:
        return self._denominator

    def __eq__(self, other):
        pass


class ClipClassMeta:
    def __init__(self,
                 version: Union[int, str, None] = None,
                 name: Optional[str] = None,
                 description="Unnamed Clip class",
                 author: Optional[str] = None,
                 documentation: Optional[str] = None,
                 source_url: Optional[str] = None
                 ):
        self.version = version
        self.name = name
        self.description = description
        self.author = author
        self.documentation = documentation
        self.source_url = source_url
