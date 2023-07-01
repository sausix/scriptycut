# -*- coding: utf-8 -*-

from typing import Optional

from scriptycut.clip import Clip
from scriptycut.common import Layer


class Crossfade(Clip):
    """
    Creates a crossfade of by specific duration. Does not include the non crossfading parts of the source clips.
    Clips can be added later. Especially for use in ClipSequences.
    """
    # TODO crossfade to images/colors support here?
    def __init__(self, duration: float, options, layer=Layer.AV, clip1: Clip = None, clip2: Clip = None):
        if (clip1 is None) != (clip2 is None):
            raise RuntimeError("Specify either both clips at the same time or None of them to use a Crossfade as template.")

        if clip1 and clip2:
            # Complete Crossface instance.

            # Check durations
            if duration > clip1.duration:
                raise ValueError("Duration of the first clip is smaller than the effect duration.")

            if duration > clip2.duration:
                raise ValueError("Duration of the second clip is smaller than the effect duration.")

        self._clip1 = clip1
        self._clip2 = clip2
        self._duration = duration
        self._layer = layer
        self._options = options

        Clip.__init__(self)

    def with_clips(self, clip1: Clip, clip2: Clip) -> "Crossfade":
        """
        Creates as NEW Crossfade instance with same config but with other clips.
        :param clip1: First Clip
        :param clip2: Second Clip
        :return: New Crossfade instance containing the overlap of the two clips
        """
        return Crossfade(self._duration, self._options, self._layer, clip1, clip2)

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def clip1(self) -> Optional[Clip]:
        return self._clip1

    @property
    def clip2(self) -> Optional[Clip]:
        return self._clip2

    @property
    def options(self):
        return self._options

    @property
    def layer(self) -> Layer:
        return self._layer

    def _repr_data(self) -> str:
        return f"{self._duration}s:{self._options}:{self._clip1!r}->{self._clip2!r}@{self._layer.name}"
