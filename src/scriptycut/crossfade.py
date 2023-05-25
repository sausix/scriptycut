# -*- coding: utf-8 -*-

from scriptycut.clip import Clip
from scriptycut.common import Layer
from scriptycut.cache import ClipCachePref


class Crossfade(Clip):
    def __init(self, duration: float, options, clip1: Clip, clip2: Clip, layer=Layer.AV, cachepref=ClipCachePref.ALWAYS):
        if not clip1.has_video:
            raise TypeError("clip1 does not have video data.")
        if not clip2.has_video:
            raise TypeError("clip2 does not have video data.")

        if duration > clip1.duration:
            raise ValueError("Duration of the first clip is smaller than the effect duration.")

        if duration > clip2.duration:
            raise ValueError("Duration of the second clip is smaller than the effect duration.")

        self._clip1 = clip1
        self._clip2 = clip2
        self._duration = duration
        self._layer = layer
        self._options = options

        Clip.__init__(self, cachepref)

    @property
    def duration(self) -> float:
        return self._duration

    def _repr_data(self) -> str:
        return f"{self._duration}s:{self._options}:{self._clip1!r}->{self._clip2!r}@{self._layer.name}"
