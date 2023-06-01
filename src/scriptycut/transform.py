# -*- coding: utf-8 -*-

"""
Basic transformations for clips.
Probably needed to match resolutions between clips.
"""

from collections.abc import Generator

from scriptycut.clip import Clip
from scriptycut.cache import ClipCachePref
from scriptycut.clipflags import ClipFlags


def _check_options(options: str) -> str:
    """
    Check if options are valid
    """
    return options


# TODO: Transform and ScaleFit both?
# -vf scale=iw*2:ih*2:flags=neighbor -c:v libx264 -preset slow -crf 18
# class Transform(Clip):
#     """
#     Transforms a clip or all containing subclips like RepeatClip and ClipSequences by a common rule
#
#     Shortcuts:
#         letterbox (keep aspect, add bars)
#         full (destroys aspect ratio, no bars)
#         fullaspect (keep aspect but may crop pixels)
#
#     Restrictions:
#         aspect=[keep]/destination/float
#
#     Move:
#         vcenter
#         hcenter
#
#     Set border positions:
#         top= (move down)
#         bottom= (move up)
#         left= (move right)
#         right= (move left)
#     """
#
#     def __init__(self, clip: Clip, options: str, cachepref=ClipCachePref.ALWAYS):
#         if not ClipFlags.HasVideo in clip.flags:
#             raise RuntimeError("Transform only works for clips containing a video stream.")
#
#         self._clip = clip
#         self._options = _check_options(options)
#         Clip.__init__(self, cachepref)
#
#     @property
#     def clip(self) -> Clip:
#         return self._clip
#
#     def _repr_data(self) -> str:
#         return f"{self._clip}:{self._options}"


class ScaleFit(Clip):
    """
    Simple scaling or fitting of Clips.
    Especially needed to combine clips or ClipSequences by a common resolution of sequences.
    """

    def __init__(self, clip: Clip,
                 width: int = None, height: int = None,
                 from_master=False, keep_aspect=True, center=True, custom: str = None,
                 cachepref=ClipCachePref.ALWAYS):

        if custom:
            if any((width, height, from_master, keep_aspect)):
                raise TypeError("When specifying 'custom', other arguments are not allowed.")



        self._clip = clip
        self._options = None
        Clip.__init__(self, cachepref)

    @property
    def clip(self) -> Clip:
        return self._clip

    # def iter_sequenced_clips(self) -> Generator[Clip, None, None]:
    #     yield from self._clip.iter_sequenced_clips()

    def iter_all_clips(self) -> Generator[Clip, None, None]:
        yield from self._clip.iter_all_clips()
        yield self

    def _repr_data(self) -> str:
        return f"{self._clip}:{self._options}"
