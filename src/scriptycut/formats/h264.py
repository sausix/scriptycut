# -*- coding: utf-8 -*-

from enum import StrEnum, auto
from dataclasses import dataclass

from scriptycut.formats import VideoFormat


class Preset(StrEnum):
    ultrafast = auto()
    superfast = auto()
    veryfast = auto()
    faster = auto()
    fast = auto()
    medium = auto()
    slow = auto()
    slower = auto()
    veryslow = auto()


class Tune(StrEnum):
    film = auto()
    animation = auto()
    grain = auto()
    stillimage = auto()
    fastdecode = auto()
    zerolatency = auto()

class Profile(StrEnum):
    baseline = auto()
    main = auto()
    high = auto()
    high10 = auto()
    high422 = auto()
    high444 = auto()

#
# @dataclass
# class h264Encoding(VideoFormat):
#
#
# def h264(crf=23, color_depth=8, preset=Preset.medium, tune=Tune.film, profile=Profile.main) -> dict:
#     """
#     :param crf: 0=lossless, 23=default, 51=worst
#     :param color_depth: 8, 10
#     :param preset: Compression quality. Slower is better bitrate or besser quality per encoding time
#     :param tune: Optimize for video type or special encoding usage
#     :param profile: Optimize for video type or special encoding usage
#     :return: h.264 VideoFormat instance
#     """


# -c:v libx264 -preset slow -crf 22
# -c:v libx264 -preset slow -crf 18 -c:a copy -pix_fmt yuv420p
# -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -pix_fmt yuv420p

# -pix_fmt yuv420p as an output option. Most (or perhaps all) non-FFmpeg based players do not support proper decoding of YUV 4:2:2 or YUV 4:4:4.
