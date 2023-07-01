# -*- coding: utf-8 -*-

"""
Slicing a Clip by frames, seconds.

Multiple slices possible:
clip[0:10,5.:6.,-1.]
Frame 0-9, seconds 5 to 6, last second
"""

from typing import Union

from scriptycut.clip import Clip

def _prepare_slice(slice_info: Union[slice, tuple[slice, ...]], clip_duration: float):
    # Check bounds etc. Calculate duration.
    # Prevent steps and reverse video?
    return slice_info, 0.


class Slice(Clip):
    def __init__(self, clip: Clip, slice_info: Union[slice, tuple[slice, ...]]):
        self._clip = clip
        self._slice_info, self._duration = _prepare_slice(slice_info, clip.duration)
        Clip.__init__(self)

    @property
    def clip(self) -> Clip:
        return self._clip

    @property
    def slice(self):
        return self._slice_info

    def duration(self) -> float:
        return self._duration

    def _repr_data(self) -> str:
        return f"{self._clip}↹{self._slice_info!r}"
