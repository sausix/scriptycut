# -*- coding: utf-8 -*-

from json import loads
from pathlib import Path
from typing import Optional
from functools import cached_property

from scriptycut.clip import Clip
from scriptycut.common import Pathlike, Layer
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
        probe_info = self.cachedir / "probe.txt"

        if self._sourcefile.is_file():
            # File exists
            stat_info = self._sourcefile.stat()
            self._filemoddate = stat_info.st_mtime_ns
            self._filesize = stat_info.st_size
            probe_res = ffprobe.probe(sourcefile, raise_error=False)
            probe_info.write_text(probe_res or "Probe failed.")
            data = probe_res and loads(probe_res) or {}

        else:
            # Missing source file
            self._filemoddate = 0
            self._filesize = 0
            probe_info.write_text("File was missing.")
            data = {}

        self._format: dict = data.get("format", {})
        self._all_streams = tuple(data.get("streams", ()))
        self._video_streams: tuple[dict, ...] = tuple(s for s in self._all_streams if isinstance(s, dict) and s.get("codec_type", None) == "video")
        self._audio_streams: tuple[dict, ...] = tuple(s for s in self._all_streams if isinstance(s, dict) and s.get("codec_type", None) == "audio")

        # Is master clip
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

        if found_video and found_audio:
            layer = Layer.AV
        elif found_video :
            layer = Layer.V
        elif found_audio:
            layer = Layer.A
        else:
            layer = Layer.NONE
        Clip.__init__(self, only_layer=layer)

    def video(self) -> Optional["Clip"]:
        if self.effective_layer == Layer.V:
            # It's pure video already
            return self

        if self.effective_layer == Layer.AV:
            # Split stream from AV
            return FileClip(self._sourcefile, video_streamindex=self._video_streamindex, master=self._master)

        return None

    def audio(self) -> Optional["Clip"]:
        if self.effective_layer == Layer.A:
            # It's pure audio already
            return self

        if self.effective_layer == Layer.AV:
            # Split stream from AV
            return FileClip(self._sourcefile, audio_streamindex=self._video_streamindex, master=self._master)

        return None

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
    def all_streams_info(self) -> tuple[dict, ...]:
        return self._all_streams

    @property
    def duration(self) -> Optional[float]:
        # Get from format/container
        dur_info = self._format.get("duration")
        if isinstance(dur_info, float):
            return dur_info
        return None

    @cached_property
    def flags(self) -> set[ClipFlags]:
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

    def unique_repr_str(self) -> str:
        extra = ""

        if self.has_video and self._video_streamindex != 0:
            # If there's at least one video stream and the first is not selected
            extra += f":v={self._video_streamindex}"

        if self.has_audio and self._audio_streamindex != 0:
            # If there's at least one audio stream and the first is not selected
            extra += f":a={self._audio_streamindex}"

        return f"{'[Master]' if self._master else ''}{self._sourcefile}{extra}"
