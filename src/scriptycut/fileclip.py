# -*- coding: utf-8 -*-

from json import loads
from pathlib import Path
from typing import Optional, Tuple, Set
from functools import cached_property

from scriptycut.clip import Clip
from scriptycut.cache import ClipCachePref
from scriptycut.common import Pathlike
from scriptycut.formats import VideoFormat, AudioFormat
from scriptycut.fftools import FFPROBE
from scriptycut.clipflags import ClipFlags


ffprobe = FFPROBE()


class FileClip(Clip):
    """
    Clip based on a file on disk.
    """
    def __init__(self, sourcefile: Pathlike,
                 video_streamindex: Optional[int] = 0,
                 audio_streamindex: Optional[int] = 0,
                 master=False):

        """
        :param sourcefile:        Source file for the clip
        :param video_streamindex: Choose a different video stream in the file.
                                  Usually 0 (the first). None: disable video
        :param audio_streamindex: Choose a different audio stream in the file.
                                  Usually 0 (the first). Multiple languages may exists.
                                  None: disable audio
        :param master:            Use codecs in this file as preferred master format.
                                  Can prevent unnecessary reencodings unless transformations and filters are applied.
        """

        self._sourcefile = Path(sourcefile)

        probe_res = ffprobe.probe(sourcefile, error=False)  # File may be missing or not

        data = {} if probe_res is None else loads(probe_res)

        self._format: dict = data.get("format", {})
        self._all_streams = tuple(data.get("streams", ()))
        self._video_streams = tuple(s for s in self._all_streams if s.get("codec_type", None) == "video")
        self._audio_streams = tuple(s for s in self._all_streams if s.get("codec_type", None) == "audio")
        self._master = master

        # Find specified streams
        found_video = video_streamindex is not None and 0 <= video_streamindex < len(self._video_streams)
        found_audio = audio_streamindex is not None and 0 <= audio_streamindex < len(self._audio_streams)
        self._video_streamindex: Optional[int] = video_streamindex if found_video else None
        self._audio_streamindex: Optional[int] = audio_streamindex if found_audio else None

        self._video_format: Optional[VideoFormat] = None
        if found_video:
            self._video_format = VideoFormat.from_stream_info(self._video_streams[video_streamindex])

        self._audio_format: Optional[AudioFormat] = None
        if found_audio:
            self._audio_format = AudioFormat.from_stream_info(self._audio_streams[audio_streamindex])

        Clip.__init__(self, ClipCachePref.NEVER)

        probe_info = self.cachedir / "probe.txt"
        probe_info.write_text(probe_res or "")

    def sourcefile(self) -> Path:
        return self._sourcefile

    @property
    def video_streamindex(self) -> Optional[int]:
        return self._video_streamindex

    @property
    def audio_streamindex(self) -> Optional[int]:
        return self._audio_streamindex

    @property
    def video_format(self) -> Optional[VideoFormat]:
        return self._video_format

    @property
    def audio_format(self) -> Optional[AudioFormat]:
        return self._audio_format

    @property
    def all_streams_info(self) -> Tuple[dict]:
        return self._all_streams

    @cached_property
    def duration(self) -> float:
        # Get from format/container
        return float(self._format.get("duration", 0.))

    @cached_property
    def flags(self) -> Set[ClipFlags]:
        f = {ClipFlags.FromFileResource, ClipFlags.HasDefinedFormat}

        if self._video_streamindex is not None:
            f.add(ClipFlags.HasVideo)

        if self._audio_streamindex is not None:
            f.add(ClipFlags.HasAudio)

        if self._video_streamindex is None and self._audio_streamindex is None:
            f.add(ClipFlags.HasMissingResources)

        if self._master:
            f.add(ClipFlags.ContainsMasterClip)
            f.add(ClipFlags.IsMasterClip)

        return f

    def _repr_data(self) -> str:
        extra = ""
        if self.has_video and self._video_streamindex != 0:
            # If there's at least one video stream and the first is not selected
            extra += f":v={self._video_streamindex}"

        if self.has_audio and self._audio_streamindex != 0:
            # If there's at least one audio stream and the first is not selected
            extra += f":a={self._audio_streamindex}"

        return f"{'[Master]' if self._master else ''}{self._sourcefile}{extra}"
