# -*- coding: utf-8 -*-

from os import environ
from re import compile
from subprocess import run, Popen, PIPE
from typing import Optional, List, Tuple
from functools import cached_property

from scriptycut.common import Pathlike, FPS
from scriptycut.jobthreads import JobThread


FFMPEG_CMD_DEFAULT = environ.get("FFMPEG", "ffmpeg")
FFPROBE_CMD_DEFAULT = environ.get("FFPROBE", "ffprobe")
FFPLAY_CMD_DEFAULT = environ.get("FFPLAY", "ffplay")


# https://opensource.com/article/17/6/ffmpeg-convert-media-file-formats


VIDEO_CODEC = "-c:v"


class FFtool:
    GENERAL_ARGS = "-hide_banner",
    CODECS_ARGS = "-v", "error", "-codecs"
    VERSION_ARGS = "-v", "error", "-version"
    FILTER_ARGS = "-v", "error", "-filters"
    PIXFMT_ARGS = "-v", "error", "-pix_fmts"

    def __init__(self, cmd: str):
        self.cmd = cmd
        res = run([self.cmd, *self.GENERAL_ARGS, *self.VERSION_ARGS], capture_output=True, timeout=5, text=True)
        if res.returncode != 0:
            raise IOError("Version call failed.")
        self.version = res.stdout

    @cached_property
    def filters(self):
        # " T.C acrusher          A->A       Reduce audio bit resolution.\n"
        regex = compile(r" (.{3}) ([^ ]+) +([AVN|]+)->([^ ]+) +(.*)\n")
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
        with Popen([self.cmd, *self.GENERAL_ARGS, *self.FILTER_ARGS], bufsize=512, stdout=PIPE, text=True,
                   universal_newlines=True) as proc:
            for line in proc.stdout:
                m = regex.match(line)
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
        regex = compile(r"IO(.{3}) ([^ ]+) +([0-9]+) +([0-9]+) +(.*)\n")

        paletted = set()
        bitstream = set()
        details: dict[str, Tuple[int, int, str]] = {}  # key, num components (channels), bit per pixel, bit depths
        pix_fmts_info = dict(paletted=paletted,
                             bitstream=bitstream,
                             details=details)

        with Popen([self.cmd, *self.GENERAL_ARGS, *self.PIXFMT_ARGS], bufsize=512, stdout=PIPE, text=True,
                   universal_newlines=True) as proc:
            for line in proc.stdout:
                m = regex.match(line)
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
        regex = compile(r" (.{6}) ([^ ]+) +(.*)\n")

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
        with Popen([self.cmd, *self.GENERAL_ARGS, *self.CODECS_ARGS], bufsize=512, stdout=PIPE, text=True,
                   universal_newlines=True) as proc:
            for line in proc.stdout:
                if "-------" in line:
                    capture = True
                    continue

                if not capture:
                    continue

                m = regex.match(line)
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
    cat file.mp3 | ffmpeg -f mp3 -i pipe: -c:a pcm_s16le -f s16le pipe:
    cat file.mp3 | ffmpeg -f mp3 -i pipe:3 -c:a pcm_s16le -f s16le pipe:

    ffmpeg -i test.wav -f avi pipe:1 | cat > test.avi

    Windows receive:
    ffmpeg.exe -y -f rawvideo -codec rawvideo -s 640x480 -r 30 -pix_fmt rgb32 -i \\.\pipe\test_pipe -an -c:v libx264 -pix_fmt yuv420p output.mp4
    ffmpeg -r 30 -vcodec rawvideo -f rawvideo -pix_fmt yuv420p -s 1280x720 -i \\.\pipe\test_pipe -an -f rtp rtp://127.0.0.1:9090
    """

    FFMPEG_ARGS = "-nostdin",
    # Progress https://stackoverflow.com/a/43980180/3149622

    def __init__(self, cmd=FFMPEG_CMD_DEFAULT):
        FFtool.__init__(self, cmd)

    def run_threaded(self, cache_path: Pathlike, *args) -> JobThread:
        return JobThread([self.cmd, *self.GENERAL_ARGS, *self.FFMPEG_ARGS, *args], cwd=cache_path, autorun=True)

    @staticmethod
    def testvideo_args(seconds=10, resolution=(1280, 720), fps=30) -> List[str]:
        return ["-f", "lavfi", "-i", f"testsrc=duration={seconds}:size={resolution[0]}x{resolution[1]}:rate={fps}"]

    @staticmethod
    def cache_output_args(output_file: Pathlike, resolution: Tuple[int, int] = None, fps: float = None, alpha: bool = None) ->List[str]:
        """
        yuv420p yuva420p yuva422p yuv444p yuva444p yuv440p yuv422p yuv411p yuv410p bgr0 bgra yuv420p16le yuv422p16le yuv444p16le yuv444p9le yuv422p9le yuv420p9le yuv420p10le yuv422p10le yuv444p10le yuv420p12le yuv422p12le yuv444p12le yuva444p16le yuva422p16le yuva420p16le yuva444p10le yuva422p10le yuva420p10le yuva444p9le yuva422p9le yuva420p9le gray16le gray gbrp9le gbrp10le gbrp12le gbrp14le gbrap10le gbrap12le ya8 gray10le gray12le gbrp16le rgb48le gbrap16le rgba64le gray9le yuv420p14le yuv422p14le yuv444p14le yuv440p10le yuv440p12le
        """
        return ["-vcodec ffv1"]

class FFPROBE(FFtool):
    PROBE_ARGS = "-v", "error", "-print_format", "json", "-show_format", "-show_streams", "-show_data_hash", "CRC32"

    def __init__(self, cmd=FFPROBE_CMD_DEFAULT):
        FFtool.__init__(self, cmd)

    def probe(self, file: Pathlike, error=True) -> Optional[str]:
        res = run([self.cmd, *self.GENERAL_ARGS, *self.PROBE_ARGS, file], capture_output=True, timeout=10, text=True)
        if res.returncode != 0:
            if error:
                raise IOError("ffprobe call failed.")
            else:
                return None
        return res.stdout


class FFPLAY(FFtool):
    PLAY_ARGS = "-autoexit",

    def __init__(self, cmd=FFPLAY_CMD_DEFAULT):
        FFtool.__init__(self, cmd)

    def play(self, args: List[str]):
        JobThread([self.cmd, *self.GENERAL_ARGS, *self.PLAY_ARGS, *args], autorun=True)

    def play_file(self, file: Pathlike):
        self.play([file])

    def play_test(self):
        self.play(FFMPEG.testvideo_args(10, (1280, 720), 30))
