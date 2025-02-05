# -*- coding: utf-8 -*-

from typing import Optional

from scriptycut.clip import Libavfilter
from scriptycut.common import Layer


class TestSrc(Libavfilter):
    # ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 -preset slow -crf 22 x264-720p30.mkv

    def __init__(self, duration: float, width: int, height: int):
        Libavfilter.__init__(self,
                             f"testsrc=duration={duration}:size={width}x{height}:rate={self._fps_hint.as_float}",
                             duration)

    @property
    def duration(self) -> float:
        return self._duration

    def _repr_data(self) -> str:
        return f"{self._duration}"


class ColorClip(Libavfilter):
    # https://ffmpeg.org/ffmpeg-utils.html#color-syntax
    # ffplay -f lavfi color=c=pink

    def __init__(self, duration: float, width: int, height: int, color: str):
        Libavfilter.__init__(self, f"color=duration={duration}:s={width}x{height}:c={color}", duration)

    @property
    def duration(self) -> float:
        return self._duration

    def _repr_data(self) -> str:
        return f"{self._duration}"


# https://ffmpeg.org/ffmpeg-filters.html#toc-Examples-151
# ffplay -f lavfi life=s=300x200:mold=10:r=60:ratio=0.1:death_color=#C83232:life_color=#00ff00,scale=1200:800:flags=16


# ffplay -hide_banner -autoexit -f lavfi sierpinski=s=800x600:type=triangle:seed=0,trim=duration=5

# ??? ffplay -hide_banner -autoexit -f lavfi zoneplate=ku=512:kv=0:kt2=0:kx2=256:s=wvga:xo=-426:kt=11

# ffplay -hide_banner -autoexit -f lavfi mandelbrot=r=60:s=640x480,trim=duration=5
