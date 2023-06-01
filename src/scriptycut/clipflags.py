# -*- coding: utf-8 -*-

from enum import Enum, auto


class ClipFlags(Enum):
    """
    Flags for Clip instances which can get inherited.
    Should help on decisions for container clips.
    """
    HasVideo = auto()  # Clip or at least one subclip has a video stream
    HasAudio = auto()  # Clip or at least one subclip has an audio stream
    HasSequence = auto()  # Clip or a subclip is a container of other subclips.
    MissingResource = auto()  # Clip or a subclip has at least one missing resource
    FileResource = auto()  # Clip or a subclip reads directly from a file

    HasMasterClip = auto()  # Clip or a subclip is marked as master. Prefer its format for rendering.
    HasAlpha = auto()

    HasFixFPS = auto()
    HasFixResolution = auto()
