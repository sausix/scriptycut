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
    HasVideo = auto()
    HasAudio = auto()
    HasSequence = auto()
    MissingResource = auto()
