# -*- coding: utf-8 -*-

from enum import Enum, auto

# class ClipFlag:
#     def __init__(self):
#         if type(self) is ClipFlag:
#             raise TypeError("You should not initialize a ClipFlag instance directly.")

class ClipFlags(Enum):
    HasVideo = auto()
    HasAudio = auto()
    HasSequence = auto()
    MissingResource = auto()
