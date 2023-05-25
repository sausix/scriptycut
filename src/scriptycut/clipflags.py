# -*- coding: utf-8 -*-

from enum import Enum, auto

# class ClipFlag:
#     def __init__(self):
#         if type(self) is ClipFlag:
#             raise TypeError("You should not initialize a ClipFlag instance directly.")

class ClipFlags(Enum):
    """
    Flags for Clip instances which can get inherited.
    Should help on decisions for container clips.
    """
    HasVideo = auto()  # Clip or at least one subclip has a video stream
    HasAudio = auto()  # Clip or at least one subclip has an audio stream
    HasSequence = auto()  # Clip or a subclip is a container of other subclips.
    MissingResource = auto()  # Clip or a subclip has at least one missing resource

    HasMasterClip = auto()  # Clip or a subclip is marked as master. Prefer its format for rendering.


    HasFixFPS = auto()
    HasFixResolution = auto()
