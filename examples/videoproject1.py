#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scriptycut.clip import Clip
from scriptycut.fileclip import FileClip
from scriptycut.image import ImageFromFile, ImageClip
from scriptycut.cache import Cache
from scriptycut.fftools import FFPLAY
from scriptycut.transform import Transform
from scriptycut.crossfade import Crossfade


# Define cache before first Clip instance or else it will
#   be created implicitly as "cwd/cache"
cache = Cache("/tmp/project.cache", discard_missing=True)  # Or define a non volatile place
# discard_missing should be True on project caches (default)
#   and False on global caches for multiple projects.

# Assign the cache to the base class for all clips
Clip.set_root_cache(cache)

# Project constants
fps = 60
resolution = 1920, 1080

# Static sources
intro = FileClip("/home/user/intro.mpv")  # Missing
outro = FileClip("outro.mpv")  # Missing

# Images
agenda = ImageFromFile("/home/as/Screenshot_20201207_064554.png")
# print(agenda.size)
# print(agenda.format)

# Video files
video1 = FileClip("/home/as/Rick Astley - Never Gonna Give You Up.mp4", master_format=True)
# master_format: This format will be preferred for other clips.
print(video1)  # <FileClip:/home/as/Rick Astley - Never Gonna Give You Up.mp4>
print(video1.video_format)  # VideoFormat(codec_name='av1', codec_type='video', codec_tag_string='av01', profile='Main', time_base='1/12800', width=1920, height=1080, coded_width=1920, coded_height=1080, pix_fmt='yuv420p', r_frame_rate='25/1', level=8)
print(video1.audio_format)  # AudioFormat(codec_name='aac', codec_type='audio', codec_tag_string='mp4a', profile='LC', time_base='1/44100', channels=2, channel_layout='stereo', sample_fmt='fltp', sample_rate='44100')


video2 = FileClip("testmedia/x264-1080p60.mkv")
print(video2)  # <FileClip[V]:testmedia/x264-1080p60.mkv>
print(video2.video_format)  # VideoFormat(codec_name='h264', codec_type='video', codec_tag_string='[0][0][0][0]', profile='High 4:4:4 Predictive', time_base='1/1000', width=1920, height=1080, coded_width=1920, coded_height=1080, pix_fmt='yuv444p', r_frame_rate='60/1', level=50)
print(video2.audio_format)  # None


# Do some simple magic with clips
mainvideo = video1 * 2 + video2

def make_video_as_always(main: Clip) -> Clip:
    """
    Helper function to compose a full video.
    Just add the main clip
    """

    # ToDo: Crossfades
    # return intro + Crossfade(duration=1) + ImageClip(agenda, 2.) + main + Crossfade(duration=1) + outro
    return intro + ImageClip(agenda, 2.) + main + outro


final_video = make_video_as_always(mainvideo)
print(final_video)  # Gives repr()
# <ClipSequence:⇻(<FileClip[?]:/home/user/intro.mpv>, <ImageClip[V]:2.0s:<ImageFromFile:/home/as/Screenshot_20201207_064554.png>>, <FileClip:/home/as/Rick Astley - Never Gonna Give You Up.mp4>, <FileClip:/home/as/Rick Astley - Never Gonna Give You Up.mp4>, <FileClip[V]:testmedia/x264-1080p60.mkv>, <FileClip[?]:outro.mpv>)>

final_video.render("/tmp/test.mkv", resolution, fps)
# Will use multiple processes
# Make use of cache if available or at least create it for the next run
