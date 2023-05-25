# -*- coding: utf-8 -*-

from scriptycut.clip import Clip

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
    def __init__(self, clip: Clip, options):
        if not clip.has_video:
            raise RuntimeError("Transform only works for clips containing a video stream.")

        self.__clip = clip
        Clip.__init__(self, True, clip.has_audio, clip.duration)

    @property
    def clip(self) -> Clip:
        return self.__clip

    def _repr_data(self) -> str:
        return f"{self.__clip}:"
