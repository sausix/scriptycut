# -*- coding: utf-8 -*-

import logging
from abc import ABCMeta, abstractmethod
from typing import Optional, Set, Tuple, Union, Dict
from collections.abc import Iterable, Sequence, Generator
from functools import cached_property
from itertools import chain
from pathlib import Path

from scriptycut.cache import Cache
from scriptycut.common import Pathlike, FPS, Layer
from scriptycut.fftools import FFMPEG, FFargs
from scriptycut.clipflags import ClipFlags

logger = logging.getLogger('scriptycut')


class Clip(metaclass=ABCMeta):
    """
    The base class representing audio and/or video over a time span from a source.
    Clip and their derived subclasses are always immutable!
    """

    # Heavy processing should be cached especially on multiple renders
    CACHE_ENABLE = True  # Disable when caching is really unnecessary (direct reading from file at least)
    CACHE_BY_BACKEND = True  # If CACHE_ENABLE = True), the backend will automatically
                             # take care of creating and offering a cache file

    # By default, streams are consistent with the input options.
    # Set to True on random based streams, live streams, cam/mic inputs, variable lengths etc.
    INCONSISTENT_STREAMDATA = False

    # Class variables
    _root_cache: Optional[Cache] = None
    _fps_hint: Optional[FPS] = None

    _autonaming: Dict[str, int] = {}  # Keep track of instance initializations counts per subclass

    @classmethod
    def set_root_cache(cls, cache: Cache):
        """Defines the root cache of a Clip or a subclass for all derived classes and instances"""
        cls._root_cache = cache

    @classmethod
    def set_fps_hint(cls, fps_hint: Union[str, int, FPS]):
        """
        Defines a default FPS value, for generative clips.
        FPS can vary in most container formats anyway. So just a hint if a Clip want it.
        """

        if isinstance(fps_hint, FPS):
            cls._fps_hint = fps_hint
        else:
            cls._fps_hint = FPS(fps_hint)

    def __init__(self):
        # Update instance count per subclass
        clsname = self.__class__.__name__
        nr = self._autonaming.get(clsname, 0) + 1
        self._autonaming[clsname] = nr

        # autoname: Define short name for logging, progress naming, etc.
        self._autoname = f"{clsname}_{nr}"

        # Check global cache
        if self._root_cache is None:
            # Create a global cache in Clip
            Clip._root_cache = Cache()

        # Get unique cache folder name
        self.cachedir = self._root_cache.get_item_folder(
            self.__class__.__name__,
            f"{self.av_info_str}:{self._repr_data()}"
        )

        # Put current autoname in cache
        autoname_file = self.cachedir / "_autoname.txt"
        autoname_file.write_text(self._autoname)

        # Clip related attributes
        self._video_fps: Optional[FPS] = None
        self._cached = False

    @property
    def has_video(self) -> bool:
        """Shorthand property if clip or a subclip has video"""
        return ClipFlags.HasVideo in self.flags

    @property
    def has_audio(self) -> bool:
        """Shorthand property if clip or a subclip has audio"""
        return ClipFlags.HasAudio in self.flags

    @property
    def available_av_layer(self) -> Layer:
        f = self.flags

        if {ClipFlags.HasVideo, ClipFlags.HasAudio}.issubset(f):
            return Layer.AV
        elif ClipFlags.HasVideo in f:
            return Layer.V
        elif ClipFlags.HasAudio in f:
            return Layer.A
        else:
            return Layer.NONE

    @property
    def flags(self) -> Set[ClipFlags]:
        """
        A clip instance can report a set of flags.
        Each Clip should compose a representative set of ClipFlags merged from potentional subclips.
        """
        return {ClipFlags.HasMissingResources}

    @property
    def video_fps(self) -> Optional[FPS]:
        return self._video_fps

    @property
    def duration(self) -> float:
        """
        Duration in seconds which should be fixed.
        Could be overridden and calculated on demand. Cache it if possible.
        :return: Length of the Clip in seconds
        """
        return 0.

    @property
    def video_resolution(self) -> Optional[Tuple[int, int]]:
        """
        Returns a resolution if known by Clip
        :return: tuple(width, height)
        """
        return None

    # Too ambigious
    # def __len__(self):
    #     """
    #     A plain Clip instance is quite useless. Most Clip subclasses represent 1 clip if not even more.
    #     This is not the duration or frame count!
    #     """
    #     return 0 if type(self) is Clip else 1

    def __hash__(self):
        """Hash based on repr. Not safe as permanent caching key"""
        return hash(repr(self))

    def __add__(self, other: "Clip"):
        """
        Allows simple concatenation of clips: clip1 + clip2 + ...
        :param other: The Clip played after this one
        """
        if not isinstance(other, Clip):
            raise TypeError("You can only add Clip instances as shorthand for concatenation.")
        return ClipSequence((self, other))

    def __mul__(self, count: int):
        """
        Allows clip repeating: this_clip * 2
        :param count: Number of repeats of this clip.
        """
        if not isinstance(count, int):
            raise TypeError("You can only multiply a Clip by an integer as shorthand for looping.")
        if count < 1:
            raise ValueError("count must be at least 1")
        return RepeatClip(self, count)

    def __getitem__(self, item):
        # TODO Rethink?
        if isinstance(item, int):
            pass  # get a frame by framenumber

        if isinstance(item, float):
            pass  # get a frame at second

        if isinstance(item, (slice, tuple)):
            from scriptycut.slice import Slice
            return Slice(self, item)

    # def transform(self, options: str) -> "Clip":
    #     # TODO Basic transformations
    #     from scriptycut.transform import Transform
    #     return Transform(self, options)

    def overlay(self, other_clip: "Clip", options) -> "Clip":
        # TODO Overlays with clips
        from scriptycut.overlay import Overlay
        return Overlay(self, other_clip, options)

    def scale(self,
              width: int = None, height: int = None,
              keep_aspect=True, center=True, custom: str = None):
        """
        Scales a Clip.
        Helper/wrapper function using transform()
        :param width:
        :param height:
        :param keep_aspect: Keep aspect ratio of clips. Add black bars.
        :param center:
        :param custom:
        :return:
        """

        from scriptycut.transform import Scale
        return Scale(self, width, height, keep_aspect, center, custom)


    def ffmpeg_args(self, prefer_cache=True) -> FFargs:
        pass

    def render_cache(self, force_update_existing=False):
        if not self.CACHE_USE:
            return

        if self._cached:
            # The Clip is already cached
            return

        if self.has_video:
            cached_video_file = self.cachedir / "video.ffv1"
        if self.has_audio:
            cached_audio_file = self.cachedir / "audio.flac"

        self.render()


    def render(self, file: Pathlike, **encoding_kwargs):
        # TODO: Render interface, format incompatibility handling
        input_args = ()
        output_args = ()

        f = FFMPEG()
        render_thread = f.run_threaded(self.cachedir, *input_args, *output_args, file)
        render_thread.join_if_alive()
        # -progress progressinfo.txt

    def iter_sequenced_clips(self) -> Generator["Clip", None, None]:
        """
        Iterates all clips in sequence order as played.
        Does yield itself if it's not a sequence.
        :return: Generator yielding clips
        """
        yield self

    def iter_all_clips(self) -> Generator["Clip", None, None]:
        """
        Iterates over all clips, including overlays, etc.
        Basically all Clips which would normally merge into single ones.
        Order should be: Dependencies first.
        :return: Generator yielding all containing clips
        """
        yield self

    @abstractmethod
    def _repr_data(self) -> str:
        """
        Clips are immutable for caching.
        Always reflect all settings for a subclass instance into this function.
        """
        return "[useless empty clip]"

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warn(self, msg):
        pass

    def err(self, msg):
        pass

    @property
    def av_info_str(self) -> str:
        """Quick stream present indication (if not [AV]): [A], [V], [Missing]"""
        if ClipFlags.HasVideo in self.flags and ClipFlags.HasAudio in self.flags:
            return ""  # Audio + Video is default, so omit

        if ClipFlags.HasVideo in self.flags:
            return "[V]"

        if ClipFlags.HasAudio in self.flags:
            return "[A]"

        return "[Missing]"

    def __repr__(self):
        return f"<{self._autoname}{self.av_info_str}:{self._repr_data()}>"


class ClipSequence(Clip):
    """
    """

    auto_flatten = True  # Should be True by default. Else clip1 + clip2 + clip3 creates a tree structure.

    def __init__(self, clips: Iterable[Clip], auto_flatten: bool = None):
        if auto_flatten or (auto_flatten is None and self.auto_flatten):
            self._clips = tuple(self._flatten_subclips(clips))
        else:
            self._clips = tuple(clips)

        if len(self._clips) == 0:
            raise ValueError("Empty ClipSequences are not allowed.")

        Clip.__init__(self)

    @staticmethod
    def _flatten_subclips(clips: Iterable[Clip]):
        for clip in clips:
            if isinstance(clip, ClipSequence):
                # Balance up
                yield from clip._clips
            else:
                # Just append
                yield clip

    @cached_property
    def flags(self) -> Set[ClipFlags]:
        return ClipFlags.merge_from_clips(self._clips, append=ClipFlags.HasSequence)

    @cached_property
    def duration(self) -> float:
        return sum(c.duration for c in self._clips)

    def match_resolutions(self,
                          width: int = None, height: int = None,
                          from_master=False, keep_aspect=True, center=True, custom: str = None):
        """
        Scales and fits a ClipSequence equally to a common resolution.
        Helper/wrapper function using transform()
        :param width:
        :param height:
        :param from_master: Use width and height from a containing master clip.
        :param keep_aspect: Keep aspect ratio of clips. Add black bars.
        :param center:
        :param custom:
        :return:
        """

        if from_master:
            if ClipFlags.ContainsMasterClip not in self.flags:
                raise RuntimeError("from_master requires one subclip clip to be flagged as master.")

            master_clips = tuple(c for c in self.iter_sequenced_clips() if ClipFlags.IsMasterClip)
            if not master_clips:
                raise RuntimeError("No master clip found.")


        from scriptycut.transform import Scale

        scaled_clips = []
        for c in self.iter_sequenced_clips():
            if not c.has_video:
                # No video to scale
                scaled_clips.append(c)

        return ClipSequence(scaled_clips, auto_flatten=False)

    def iter_sequenced_clips(self) -> Generator[Clip, None, None]:
        """Just resolve sequences in play order. May return the same clip multiple times."""
        yield from chain.from_iterable(c.iter_sequenced_clips() for c in self._clips)
        # Do not yield the sequence itself

    def iter_all_clips(self) -> Generator[Clip, None, None]:
        """Resolve all subclips in sequences. May return clips multiple times."""
        yield from chain.from_iterable(c.iter_all_clips() for c in self._clips)
        yield self  # Yield the sequence also at last.

    def _repr_data(self) -> str:
        return f"⇻{self._clips}"


class RepeatClip(ClipSequence):
    def __init__(self, clip: Clip, count: int):
        if not isinstance(count, int) or count<1:
            raise ValueError("Count must be int >= 1")

        self._clip = clip
        self._count = count
        ClipSequence.__init__(self, [clip] * count, True)

    @property
    def clip(self) -> Clip:
        return self._clip

    @property
    def count(self) -> int:
        return self._count

    def iter_all_clips(self) -> Generator[Clip, None, None]:
        """Iter over all subclips of the repeated clip once."""
        yield from self._clip.iter_all_clips()  # Yields self._clip already
        yield self

    def _repr_data(self) -> str:
        return f"{self._count}×{self._clip!r}"
