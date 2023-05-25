# -*- coding: utf-8 -*-

from dataclasses import dataclass, fields


@dataclass
class Format:
    codec_name: str
    codec_type: str
    codec_tag_string: str
    profile: str
    time_base: str

    @classmethod
    def from_stream_info(cls, si: dict) -> "Format":
        codec_type = si.get("codec_type")
        subcls = _mapping.get(codec_type)
        if subcls is None:
            raise ValueError("Unknown codec type. Only video and audio are supported.")

        return subcls.from_stream_info(si)

    @classmethod
    def filter_si_dict(cls, si: dict):
        return {key: value for key, value in si.items() if key in (f.name for f in fields(cls))}

@dataclass
class VideoFormat(Format):
    width: int
    height: int
    coded_width: int
    coded_height: int
    pix_fmt: str
    r_frame_rate: str
    level: int

    @classmethod
    def from_stream_info(cls, si: dict) -> "VideoFormat":
        return cls(**cls.filter_si_dict(si))

@dataclass
class AudioFormat(Format):
    channels: int
    channel_layout: str
    sample_fmt: str
    sample_rate: str

    @classmethod
    def from_stream_info(cls, si: dict) -> "AudioFormat":
        return cls(**cls.filter_si_dict(si))


_mapping = {"video": VideoFormat, "audio": AudioFormat}

import scriptycut.formats.h264
