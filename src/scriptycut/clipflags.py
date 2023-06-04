# -*- coding: utf-8 -*-

from enum import Enum, auto
from typing import Set, Iterable
from itertools import chain


class ClipFlags(Enum):
    """
    Flags for Clip instances which can get inherited.
    Should help on decisions for container clips.
    """

    # Clip individual
    HasVideo = auto()  # Clip or at least one subclip has a video stream
    HasAudio = auto()  # Clip or at least one subclip has an audio stream
    HasAlpha = auto()
    FromFileResource = auto()  # Clip or a subclip reads directly from a file
    HasFixFPS = auto()
    HasFixResolution = auto()
    IsMasterClip = auto()  # Clip is marked as master. Prefer its format for rendering.


    # Inherit from subclips
    ContainsMasterClip = auto()  # Clip or a subclip is marked as master. Prefer its format for rendering.
    HasMissingResources = auto()  # Clip or a subclip has at least one missing resource
    HasSequence = auto()  # Clip or a subclip is a container of other subclips.

    @classmethod
    def merge_from_clips(cls, *clips,
                         include: Iterable["ClipFlags"] = None, exclude: Iterable["ClipFlags"] = None,
                         append: Iterable["ClipFlags"] = None) -> Set:
        if include and exclude:
            raise RuntimeError("Including and excluding at the same time is not logical.")

        from scriptycut.clip import Clip
        def unpack_clips(c):
            if isinstance(c, Clip):
                yield c
            elif hasattr(c, "__iter__"):
                for c2 in c:
                    yield from unpack_clips(c2)
            else:
                raise TypeError("Clip or iterable expected.")

        clip_flags = (c.flags for c in unpack_clips(clips))
        merged = set(chain.from_iterable(clip_flags))

        if include is not None:
            merged = merged.intersection(include)

        if exclude is not None:
            merged = merged.difference(exclude)


        return merged
