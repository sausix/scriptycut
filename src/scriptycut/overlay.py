# -*- coding: utf-8 -*-

from scriptycut.clip import Clip

# https://www.abyssale.com/generate-video/ffmpeg-overlay-image-on-video

class Overlay(Clip):
    """
ffmpeg -i input.mp3 -filter_complex \
"[0:a]avectorscope=s=640x518[left]; \
 [0:a]showspectrum=mode=separate:color=intensity:scale=cbrt:s=640x518[right]; \
 [0:a]showwaves=s=1280x202:mode=line[bottom]; \
 [left][right]hstack[top]; \
 [top][bottom]vstack,drawtext=fontfile=/usr/share/fonts/TTF/Vera.ttf:fontcolor=white:x=10:y=10:text='\"Song Title\" by Artist'[out]" \
-map "[out]" -map 0:a -c:v libx264 -preset fast -crf 18 -c:a copy output.mkv

Overlay with webcam
ffmpeg -f x11grab -video_size 1680x1050 -framerate 30 -i :0.0 \
-f v4l2 -video_size 320x240 -framerate 30 -i /dev/video0 \
-f alsa -ac 2 -i hw:0,0 -filter_complex \
"[0:v]scale=1024:-1,setpts=PTS-STARTPTS[bg]; \
 [1:v]scale=120:-1,setpts=PTS-STARTPTS[fg]; \
 [bg][fg]overlay=W-w-10:10,format=yuv420p[v]"
-map "[v]" -map 2:a -c:v libx264 -preset veryfast \
-b:v 3000k -maxrate 3000k -bufsize 4000k -c:a aac -b:a 160k -ar 44100 \
-f flv rtmp://live.twitch.tv/app/<stream key>

    """
    def __init__(self, clip_bottom: Clip, clip_top: Clip, options):
        if not clip_bottom.has_video:
            raise RuntimeError("clip_bottom does not containing a video stream.")
        if not clip_top.has_video:
            raise RuntimeError("clip_top does not containing a video stream.")

        self.__clip_bottom = clip_bottom
        self.__clip_top = clip_top
        self.__options = options

        Clip.__init__(self, True, clip_bottom.has_audio or clip_top.has_audio,
                      max(clip_bottom.duration, clip_top.duration))

    @property
    def clip_bottom(self) -> Clip:
        return self.__clip_bottom

    @property
    def clip_top(self) -> Clip:
        return self.__clip_top

    def _repr_data(self) -> str:
        return f"{self.__clip_bottom}↙↗{self.__clip_top}:{self.__options}"
