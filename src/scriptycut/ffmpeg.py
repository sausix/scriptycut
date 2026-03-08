# -*- coding: utf-8 -*-

"""
Classes and functions to interface ffmpeg executables
"""

import re
import subprocess

from os import environ
from typing import Optional, Union, Mapping, Iterable, Generator
from functools import cached_property
from pathlib import Path

from scriptycut.common import Pathlike, startupinfo_show_window
from scriptycut.jobthreads import JobThread


PathLike = Union[str, bytes, Path]
SupportedTypes = PathLike | int | float | str
ArgumentTypes = Optional[SupportedTypes | Iterable[SupportedTypes]]


FFMPEG_CMD_DEFAULT = environ.get("FFMPEG", "ffmpeg")
FFPROBE_CMD_DEFAULT = environ.get("FFPROBE", "ffprobe")
FFPLAY_CMD_DEFAULT = environ.get("FFPLAY", "ffplay")

# Generic options: https://ffmpeg.org/ffmpeg.html#toc-Main-options

# https://opensource.com/article/17/6/ffmpeg-convert-media-file-formats
RE_FILTER = re.compile(r" (.{3}) ([^ ]+) +([AVN|]+)->([^ ]+) +(.*)\n")
RE_PIX_FORMATS = re.compile(r"IO(.{3}) ([^ ]+) +([0-9]+) +([0-9]+) +(.*)\n")
RE_CODECS = re.compile(r" (.{6}) ([^ ]+) +(.*)\n")


def escape(s: str) -> str:
    e = s.replace("\\", r"\\")
    e = e.replace("'", r"\'")
    return f"'{e}'"


def unpack_args(arg: ArgumentTypes) -> Generator[str, None, None]:
    if isinstance(arg, (list, tuple)):
        for a in arg:
            yield from unpack_args(a)

    elif arg is not None:
        yield str(arg)


class Process:
    _running_processes: list["Process"] = []

    def __init__(self,
                 cmd: Union[str, Path],
                 args: Iterable[str],
                 text: bool,
                 cwd: Optional[Path] = None,
                 env: Optional[Mapping[str, str]] = None,
                 ):
        self._text = text
        self._cmd = Path(cmd)
        self._cwd = cwd
        self._env = dict(env) if env is not None else None
        self._args = args
        self._running = False
        self._stderr: Optional[str] = None
        self._returncode: Optional[int] = None

    def run_return_stdout(self, raise_err: bool = True) -> Union[str, bytes, None]:
        # Run process as one shot and return stdout.
        if self in self._running_processes:
            raise RuntimeError("Process is already running.")

        self._running_processes.append(self)

        try:
            res = subprocess.run(
                args=(self._cmd, *self._args),
                capture_output=True,
                text=self._text,
                check=raise_err,
                cwd=str(self._cwd) if self._cwd is not None else None,
                env=self._env,
                startupinfo=startupinfo_show_window()
            )
            self._stderr = res.stderr
            self._returncode = res.returncode
            return res.stdout
        finally:
            self._running_processes.remove(self)

    def run_threaded(self):
        pass

    def progress(self) -> Optional[float]:
        """
        Return the progress from 0. to 1.
        Implement this function in a specific subclass
        :return:
        """

    def kill(self):
        pass

    @property
    def running(self) -> bool:
        return self._running

    @property
    def stderr(self) -> Optional[str]:
        return self._stderr

    @property
    def returncode(self) -> Optional[int]:
        return self._returncode


class FFtool:
    """
    Access to FFmpeg and their tools
    """
    GENERAL_ARGS = ("-hide_banner", )
    CODECS_ARGS = "-v", "error", "-codecs"
    VERSION_ARGS = "-v", "error", "-version"
    FILTER_ARGS = "-v", "error", "-filters"
    PIXFMT_ARGS = "-v", "error", "-pix_fmts"

    def __init__(self, tool_path: Path):
        self.tool_path = tool_path
        p = Process(text=True, cmd=self.tool_path, args=(*self.GENERAL_ARGS, *self.VERSION_ARGS))
        self.tool_version = p.run_return_stdout(True)

    @cached_property
    def filters(self):
        # " T.C acrusher          A->A       Reduce audio bit resolution.\n"
        timeline_support = set()
        slice_support = set()
        command_support = set()
        cat_video = set()
        cat_audio = set()
        input_type: dict[str, str] = {}  # key, supported input types
        output_type: dict[str, str] = {}  # key, supported output types
        description: dict[str, str] = {}  # key, description
        filter_info = dict(timeline_support=timeline_support,
                           slice_support=slice_support,
                           command_support=command_support,
                           cat_video=cat_video,
                           cat_audio=cat_audio,
                           input_type=input_type,
                           output_type=output_type,
                           description=description
                           )

        found_first = False  # Silently ignore top of filter info output
        p = Process(text=True, cmd=self.tool_path, args=(*self.GENERAL_ARGS, *self.FILTER_ARGS))
        for line in p.run_return_stdout(True) or "":
            m = RE_FILTER.match(line)
            if not m:
                if found_first:
                    print("Could not parse codec line: " + line)
                continue

            found_first = True

            # Get data from regex match
            flags, key, itype, otype, name = m.groups()

            if "A" in itype or "N" in itype:
                cat_audio.add(key)
            elif "V" in itype or "N" in itype:
                cat_video.add(key)
            elif "|" in itype and "A" in otype:
                cat_audio.add(key)
            elif "|" in itype and "V" in otype:
                cat_video.add(key)
            else:
                continue

            if "T" in flags:
                timeline_support.add(key)
            if "S" in flags:
                slice_support.add(key)
            if "C" in flags:
                command_support.add(key)

            # Remember details
            input_type[key] = itype
            output_type[key] = otype

            description[key] = name

        return filter_info

    @cached_property
    def pix_fmts(self):
        # "IO... yuv422p                3             16      8-8-8\n"

        paletted = set()
        bitstream = set()
        details: dict[str, tuple[int, int, str]] = {}  # key, num components (channels), bit per pixel, bit depths
        pix_fmts_info = dict(paletted=paletted,
                             bitstream=bitstream,
                             details=details)

        p = Process(text=True, cmd=self.tool_path, args=(*self.GENERAL_ARGS, *self.PIXFMT_ARGS))
        for line in p.run_return_stdout(True) or "":
            m = RE_PIX_FORMATS.match(line)
            if not m:
                continue

            # Get data from regex match
            flags, key, nc, bpp, bit_depths = m.groups()

            if "P" in flags:
                paletted.add(key)

            if "B" in flags:
                bitstream.add(key)

            details[key] = int(nc), int(bpp), bit_depths

        return pix_fmts_info

    @cached_property
    def codecs(self):
        # " DES... xsub                 XSUB\n"
        decode = set()
        encode = set()
        video = set()
        audio = set()
        lossy = set()
        lossless = set()
        intra_frame_only = set()
        description: dict[str, str] = {}  # key, description
        codec_info = dict(decode=decode,
                          encode=encode,
                          video=video,
                          audio=audio,
                          lossy=lossy,
                          lossless=lossless,
                          intra_frame_only=intra_frame_only,
                          description=description
                          )

        capture = False  # To skip the first lines until the mark
        p = Process(text=True, cmd=self.tool_path, args=(*self.GENERAL_ARGS, *self.CODECS_ARGS))
        for line in p.run_return_stdout(True) or "":
            if "-------" in line:
                capture = True
                continue

            if not capture:
                continue

            m = RE_CODECS.match(line)
            if not m:
                print("Could not parse codec line: " + line)
                continue

            # Get data from regex match
            flags, key, name = m.groups()

            if "V" in flags:
                video.add(key)
            elif "A" in flags:
                audio.add(key)
            else:
                # Ignore specials for now
                continue

            if "D" in flags:
                decode.add(key)
            if "E" in flags:
                encode.add(key)
            if "I" in flags:
                intra_frame_only.add(key)

            if "L" in flags:
                lossy.add(key)
            if "S" in flags:
                lossless.add(key)

            description[key] = name

        return codec_info


class FFMPEG(FFtool):
    """

    """
    FFMPEG_ARGS = "-nostdin", "-y"
    # Progress https://stackoverflow.com/a/43980180/3149622

    def __init__(self, tool_path=FFMPEG_CMD_DEFAULT):
        FFtool.__init__(self, tool_path)

    def run_threaded(self, cache_path: Pathlike, *args) -> JobThread:
        return JobThread([self.cmd, *self.GENERAL_ARGS, *self.FFMPEG_ARGS, *args], cwd=cache_path, autorun=True)

        p = Process(text=True, cmd=self.tool_path, args=(*self.GENERAL_ARGS, *self.FFMPEG_ARGS))
        self.tool_version = p.run_return_stdout(True)

    def preview_qt(self):
        pass

    @staticmethod
    def testvideo_args(seconds=10, resolution=(1280, 720), fps=30) -> list[str]:
        return ["-f", "lavfi", "-i", f"testsrc=duration={seconds}:size={resolution[0]}x{resolution[1]}:rate={fps}"]

    @staticmethod
    def cache_output_args(output_file: Pathlike, resolution: tuple[int, int] = None, fps: float = None, alpha: bool = None) -> list[str]:
        """
        yuv420p yuva420p yuva422p yuv444p yuva444p yuv440p yuv422p yuv411p yuv410p bgr0 bgra yuv420p16le yuv422p16le
        yuv444p16le yuv444p9le yuv422p9le yuv420p9le yuv420p10le yuv422p10le yuv444p10le yuv420p12le yuv422p12le
        yuv444p12le yuva444p16le yuva422p16le yuva420p16le yuva444p10le yuva422p10le yuva420p10le yuva444p9le
        yuva422p9le yuva420p9le gray16le gray gbrp9le gbrp10le gbrp12le gbrp14le gbrap10le gbrap12le ya8 gray10le
        gray12le gbrp16le rgb48le gbrap16le rgba64le gray9le yuv420p14le yuv422p14le yuv444p14le yuv440p10le yuv440p12le
        """
        return ["-vcodec", "ffv1"]


class FFPROBE(FFtool):
    PROBE_ARGS = "-v", "error", "-print_format", "json", "-show_format", "-show_streams", "-show_data_hash", "CRC32"

    def __init__(self, tool_path=FFPROBE_CMD_DEFAULT):
        FFtool.__init__(self, tool_path)

    def probe(self, file: Pathlike, raise_error=True) -> Optional[str]:
        p = Process(text=True, cmd=self.tool_path, args=(*self.GENERAL_ARGS, *self.PROBE_ARGS, file))

        stdout = p.run_return_stdout(raise_error)
        if p.returncode:
            return None
        return stdout


class FFPLAY(FFtool):
    """
    Player output. Previewing clips etc.
    """

    PLAY_ARGS = ("-autoexit", )

    def __init__(self, cmd=FFPLAY_CMD_DEFAULT):
        FFtool.__init__(self, cmd)

    def play(self, args: list[str]):
        JobThread([self.cmd, *self.GENERAL_ARGS, *self.PLAY_ARGS, *args], autorun=True)

    def play_file(self, file: Pathlike):
        self.play([file])

    def play_test(self):
        self.play(FFMPEG.testvideo_args(10, (1280, 720), 30))
