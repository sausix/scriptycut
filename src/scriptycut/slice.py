# -*- coding: utf-8 -*-

from typing import Union

from scriptycut.clip import Clip

def _prepare_slice(slice_info, duration: float):
    pass


class Slice(Clip):
    def __init__(self, clip: Clip, slice_info: Union[slice, tuple[slice, ...]]):
        self.__clip = clip
        self.__slice_info = _prepare_slice(slice_info, clip.duration)
        Clip.__init__(self, clip.has_video, clip.has_audio, clip.duration)

    @property
    def clip(self) -> Clip:
        return self.__clip

    @property
    def slice(self):
        return self.__slice_info

    def _repr_data(self) -> str:
        return f"{self.__clip}↹{self.__slice_info!r}"
