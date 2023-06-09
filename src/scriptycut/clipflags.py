# -*- coding: utf-8 -*-

from enum import Enum, auto
from typing import Set, Iterable, Union
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
    IsMasterClip = auto()  # Clip is marked as master. Prefer its format for rendering.
    HasDefinedFormat = auto()  # Clip has a preferred format (from file etc)

    # Inherit from subclips
    ContainsMasterClip = auto()  # Clip or a subclip is marked as master. Prefer its format for rendering.
    HasMissingResources = auto()  # Clip or a subclip has at least one missing resource
    HasSequence = auto()  # Clip or a subclip is a container of other subclips.

    @classmethod
    def merge_from_clips(cls, *clips,
                         include: Union[Iterable["ClipFlags"], "ClipFlags"] = None,
                         exclude: Union[Iterable["ClipFlags"], "ClipFlags"] = None,
                         append: Union[Iterable["ClipFlags"], "ClipFlags"] = None) -> Set:
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

        if append:
            if isinstance(append, ClipFlags):
                append_set = {append}
            else:
                append_set = set(append)
        else:
            append_set = set()

        if include is not None:
            if isinstance(include, ClipFlags):
                merged.discard(include)
            else:
                merged.intersection_update(include)

        if exclude is not None:
            if isinstance(exclude, ClipFlags):
                exclude_set = {exclude}
            else:
                exclude_set = set(exclude)

            if append_set.intersection(exclude_set):
                raise RuntimeError("You can't exclude and append the same items.")

            merged.difference_update(exclude_set)

        return merged.union(append_set)
