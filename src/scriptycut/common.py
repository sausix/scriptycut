# -*- coding: utf-8 -*-

import subprocess
from typing import Union, Optional
from pathlib import Path
from sys import platform
from enum import IntFlag, auto
from os import environ


Pathlike = Union[Path, str]


threads_num = int(environ.get("THREADS", "1"))


def startupinfo_show_window(show=False) -> Optional[subprocess.STARTUPINFO]:
    if platform == "win32":
        return subprocess.STARTUPINFO(
            dwFlags=subprocess.STARTF_USESHOWWINDOW,
            wShowWindow=int(show)
        )
    return None


class Layer(IntFlag):
    NONE = 0
    A = 1
    V = 2
    AV = A + V


class ClipState(IntFlag):
    Initialized = 0
    Caching = auto()
    Ready = auto()
    Error = auto()


class FPS:
    """
    Representation of a framerate (fps).
    Floats are bad here... Avoid as input?

    int: 60
    str: "30000/1001"
    """
    def __init__(self, fps: Union[int, str], allow_vfr: bool):
        self._fps = fps
        self._vfr = allow_vfr

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


class VideoResolution:
    def __init__(self, width: int, height: int):
        self._width: int = width
        self._height: int = height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def as_tuple(self) -> tuple[int, int]:
        return self._width, self._height


# Used as defaults for generative Clips
default_metrics = dict(
    video=dict(
        fps=FPS(24, allow_vfr=False),
    ),
    audio=dict(
        channels=2,
    )
)
