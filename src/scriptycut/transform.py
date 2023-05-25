# -*- coding: utf-8 -*-

"""
Basic transformations for clips.
Probably needed to match resolutions between clips.
"""

from scriptycut.clip import Clip
from scriptycut.cache import ClipCachePref
from scriptycut.clipflags import ClipFlags


def _check_options(options: str) -> str:
    """
    Check if options are valid
    """
    return options


# -vf scale=iw*2:ih*2:flags=neighbor -c:v libx264 -preset slow -crf 18
class Transform(Clip):
    """
    Transforms a clip or all containing subclips like RepeatClip and ClipSequences by a common rule

    Shortcuts:
        letterbox (keep aspect, add bars)
        full (destroys aspect ratio, no bars)
        fullaspect (keep aspect but may crop pixels)

    Restrictions:
        aspect=[keep]/destination/float

    Move:
        vcenter
        hcenter

    Set border positions:
        top= (move down)
        bottom= (move up)
        left= (move right)
        right= (move left)
    """

    def __init__(self, clip: Clip, options: str, cachepref=ClipCachePref.ALWAYS):
        if not ClipFlags.HasVideo in clip.flags:
            raise RuntimeError("Transform only works for clips containing a video stream.")

        self._clip = clip
        self._options = _check_options(options)
        Clip.__init__(self, cachepref)

    @property
    def clip(self) -> Clip:
        return self._clip

    def _repr_data(self) -> str:
        return f"{self._clip}:{self._options}"
