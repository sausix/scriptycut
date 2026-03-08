# -*- coding: utf-8 -*-

import logging
import functools
from abc import ABCMeta, abstractmethod
from typing import Optional, Type, TypeVar, Any, overload
from collections.abc import Iterable, Generator
from itertools import chain
from pathlib import Path

from scriptycut.cache import Cache
from scriptycut.common import FPS, Layer, ClipState, default_metrics, VideoResolution
from scriptycut.fftools import FFMPEG
from scriptycut.clipflags import ClipFlags
from scriptycut.frame import Frame


T = TypeVar("T", bound="Clip")

logger = logging.getLogger("scriptycut")


class ClipError(Exception):
    pass


class ClipMeta(ABCMeta):
    """
    This meta class provides cached singleton instances per unique configuration of Clip subclasses.
    """
    _cache = {}

    def __call__(cls: Type[T], *args, **kwargs) -> T:
        # Create a new clip instance, may be temporarily.
        clip_instance: T = ABCMeta.__call__(cls, *args, **kwargs)

        # definition_str is only available after Clip.__init__()
        # Different args may still point to the same Clip config so just using args and kwargs is not enough.
        key = f"{cls.__name__}_{clip_instance.definition_str}"

        # Check cache
        if key in cls._cache:
            # Matching instance found.
            #
            return ClipMeta._cache[key]

        # Cache and return new instance
        ClipMeta._cache[key] = clip_instance

        # Instance number counting
        nr = cls._instance_counter.get(cls, 0) + 1
        cls._instance_counter[cls] = nr  # Initialize or increase instance number.

        if clip_instance.name is None:  # Unnamed
            # Set an appropriate instance name
            clip_instance.name = clip_instance.name_hint() or f"{cls.__name__}-{nr}"

        return clip_instance


class ClipBase(metaclass=ABCMeta):
    """
    All abstract methods required by Clip subclasses
    """

    # Descriptive meta information about a subclass.
    # Version is important for caching. Each version will retain its own cache.
    meta_name: str = "Unnamed Clip class"
    meta_description: str = "Does nothing yet"
    meta_version: int | str = 0
    meta_source_url: str = ""
    meta_doc_url: str = ""

    @abstractmethod
    def audio(self) -> Optional["Clip"]:
        """Return a audio only clip (if available), None or itself if already representing audio only"""

    @abstractmethod
    def video(self) -> Optional["Clip"]:
        """Return a video only clip (if available), None or itself if already representing video only"""

    @property
    @abstractmethod
    def definition_str(self) -> str:
        """
        Clips are immutable for caching.
        Always reflect all settings for a subclass instance into this function.
        Keep the result constant! Remember: Clips are immutable.
        """


class Clip(ClipBase, metaclass=ClipMeta):  # noqa, PyCharm highlights missing abstract methods here.
    """
    The base class representing audio and/or video over a time span from a source.
    Instances of derived subclasses are always immutable!
    """

    # Set of available Clip subclasses.
    _clip_classes: set[Type["Clip"]] = set()

    # Keep track of instance initializations counts per subclass, mostly for auto naming.
    _instance_counter: dict[Type["Clip"], int] = {}

    # Internal class variables
    _cache: Optional[Cache] = None

    # Default cache file names
    cache_video_file_name = "clip-video.ffv1"  # Lossless video format
    cache_audio_file_name = "clip-audio.wav"
    cache_av_file_name = "clip.mkv"

    # Default values globally or per Clip class. Mostly for generative Clips like FPS.
    # These values are being merged with specialized values from render calls.
    _default_metrics: Optional[dict[str, Any]] = default_metrics

    _instance_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )

    def __init_subclass__(cls):
        # Register known Clip subclasses.
        cls._clip_classes.add(cls)

    def name_hint(self) -> Optional[str]:  # noqa, it's an instance method.
        # Clips can return a better name recommendation. A file name for example.
        return None

    @classmethod
    def set_cache(cls, cache: Cache):
        """Defines the cache of the Clip class or a specific subclass for all derived classes and instances"""
        cls._cache = cache

    def __init__(self, only_layer: Layer = Layer.AV):
        if type(self) is Clip:
            raise NotImplementedError("A bare Clip can't be initialized. Use a specific subclass.")

        self._name: Optional[str] = None

        # Just output/process these layers
        self._layer_filter = only_layer

        # Check and create global cache
        if self._cache is None:
            # Missing cache.
            # Create a new global cache in Clip class
            Clip.set_cache(Cache())

        if self._cache is None:
            raise RuntimeError("Could not create cache instance.")

        # Get unique cache folder name
        self._cache_dir = self._cache.get_item_folder(
            classname=self.__class__.__name__,
            version=self.__class__.meta_version,
            item_definition=f"{self.definition_str}"
        )

        # Logging
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}.{self.instance_number}")
        self._logger.setLevel(logging.DEBUG)
        self._logfile = self._cache_dir / "log.txt"
        self._loghandler = logging.FileHandler(self._logfile, encoding="utf-8")
        self._loghandler.setFormatter(self._instance_formatter)
        self._logger.addHandler(self._loghandler)
        self.log = self._logger.log
        self.info = self._logger.info
        self.debug = self._logger.debug
        self.warn = self._logger.warning
        self.err = self._logger.error

        self.info(
            "=== Clip class: %s",
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            self.instance_number,
        )

        self.info("Name: %s", self.meta_name)
        self.info("Description: %s", self.meta_description)
        self.info("Version: %s", self.meta_version)
        self.info("Source URL: %s", self.meta_source_url)
        self.info("Documentation URL: %s", self.meta_doc_url)
        self.info(
            "--- Clip instance: %s",
            f"{self.__class__.__module__}.{self.__class__.__name__}.{self.instance_number}",
            self.instance_number,
        )

        # Name: Define short name for logging, progress naming, etc.
        self._name_file = self._cache_dir / "_name.txt"

        if self._name_file.exists():
            # Read name from file
            self._name = self._name_file.read_text()

        self.info("Name: %s", self._name or "[None]")
        self.info("Definition: %s", self.definition_str)
        self.info("AV Info: %s", self.av_info_str)
        self.info("Cache directory: %s", self._cache_dir)

        # Clip related attributes
        self._state = ClipState.Initialized

    @property
    def instance_number(self) -> int:
        """
        Returns a sequential number of the instance based on its Clip class
        """
        return self._instance_counter[self.__class__]

    @property
    def state(self) -> ClipState:
        return self._state

    def _set_state(self, new_state: ClipState):
        self.info("New Clip state: %s", new_state)
        self._state = new_state

    @property
    def cache_dir(self) -> Path:
        """Directory dedicated to this exact immutable clip instance."""
        return self._cache_dir

    def file_path(self) -> Path:
        """
        Returns a file path which points to an existing source file or to a location in the cache folder.
        If pointing to the cache then the file may not exist (yet)
        :return: Path to a file which points to a resource.
        """

    def file_path_blocking(self) -> Path:
        """
        Returns a file path which points to an existing source file or to a location in the cache folder.
        If the resource has not been rendered then this function blocks until the file is ready.
        :return: Path to a file which points to a resource.
        """

    @property
    def name(self) -> Optional[str]:
        """
        Name of the clip instance
        :return: Returns the human readable name of the clip instance.
        """
        return self._name

    @name.setter
    def name(self, new_name: str):
        """
        Sets a new name to the clip instance
        :new_name: The new name as string.
        """
        self._name = new_name
        self._name_file.write_text(new_name)
        self.info("New instance name: %s", new_name)

    @property
    def effective_layer(self) -> Layer:
        """
        Returns the effectively available layer mask of the clip.
        :return: The layer_filter argument provided to __init__ combined with actually available layers of the source.
        """
        flags = self.flags  # Calculate flags of clip once

        if ClipFlags.HasAudio in flags and ClipFlags.HasVideo in flags and self._layer_filter == Layer.AV:
            return Layer.AV
        elif (ClipFlags.HasVideo in flags) and (self._layer_filter & Layer.V):
            return Layer.V
        elif (ClipFlags.HasAudio in flags) and (self._layer_filter & Layer.A):
            return Layer.A
        else:
            return Layer.NONE

    @property
    def layer_filter(self) -> Layer:
        """
        Returns the requested layer mask of the clip.
        :return: The layer_filter argument provided to __init__.
        """
        return self._layer_filter

    @property
    def has_video(self) -> bool:
        """Shorthand property if clip or a subclip has video"""
        return bool(self.effective_layer & Layer.V)

    @property
    def has_audio(self) -> bool:
        """Shorthand property if clip or a subclip has audio"""
        return bool(self.effective_layer & Layer.A)

    @property
    def has_audiovideo(self) -> bool:
        """Shorthand property if clip or a subclip has audio and video"""
        return bool(self.effective_layer & Layer.AV)

    @property
    def flags(self) -> set[ClipFlags]:
        """
        A clip instance can report a set of flags.
        Each Clip should compose a representative set of ClipFlags merged from potentional subclips.
        """
        return {ClipFlags.HasMissingResources}

    @property
    def duration(self) -> Optional[float]:
        """
        Duration in seconds which should be fixed.
        Could be overridden and calculated on demand. Cache it if possible.
        :return: Length of the Clip in seconds
        """
        # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
        return None

    def metrics(self, with_base_defaults=True) -> dict[str, Any]:
        if with_base_defaults:
            return self._default_metrics or {}
        else:
            return {}

    def __hash__(self):
        """Hash based on repr. Not safe as permanent caching key"""
        return hash(self.definition_str)

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

    @overload
    def __getitem__(self, _pos: float) -> Frame:
        """
        Returns a still image from within the video clip
        :param _pos: Position in seconds within the Clip
        :return: A still image
        """

    @overload
    def __getitem__(self, _range: slice) -> Clip:
        pass

    def __getitem__(self, pos_or_range):
        pass

    # def transform(self, options: str) -> "Clip":
    #     # TODO Basic transformations
    #     from scriptycut.transform import Transform
    #     return Transform(self, options)

    # def overlay(self, other_overlay_clip: "Clip", options) -> "Clip":
    #     # TODO Overlays with clips
    #     from scriptycut.overlay import Overlay
    #     return Overlay(self, other_overlay_clip, options)
    #
    # def scale(self,
    #           width: int = None, height: int = None,
    #           keep_aspect=True, center=True, custom: str = None):
    #     """
    #     Scales a Clip.
    #     Helper/wrapper function using transform()
    #     :param width:
    #     :param height:
    #     :param keep_aspect: Keep aspect ratio of clips. Add black bars.
    #     :param center:
    #     :param custom:
    #     :return:
    #     """
    #
    #     from scriptycut.transform import Scale
    #     return Scale(self, width, height, keep_aspect, center, custom)

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

    @property
    def av_info_str(self) -> str:
        """Quick stream present indication (if not [AV]): [A], [V], [Missing]"""
        if ClipFlags.HasMissingResources in self.flags:
            return "[Incomplete]"

        if self.effective_layer is Layer.AV:
            return ""  # Audio + Video is default, so omit

        if self.effective_layer is Layer.V:
            return "[V]"

        if self.effective_layer is Layer.A:
            return "[A]"

        return "[NonAV]"

    def __repr__(self):
        return self.definition_str_full

    @property
    def definition_str_full(self) -> str:
        return f"{self.__class__.__name__}({self.definition_str})[{self.av_info_str}]"


class ClipSequence(Clip):
    """
    """
    auto_flatten = True  # Should be True by default. Else clip1 + clip2 + clip3 creates a tree structure.

    def __init__(self, clips: Iterable[Clip], auto_flatten: bool = None):
        if auto_flatten or (auto_flatten is None and self.auto_flatten):
            self._clips: tuple[Clip, ...] = tuple(self._flatten_subclips(clips))
        else:
            self._clips: tuple[Clip, ...] = tuple(clips)

        if len(self._clips) == 0:
            raise ValueError("Empty ClipSequences are not allowed.")

        Clip.__init__(self)

    def audio(self) -> Optional["Clip"]:
        pass  # TODO

    def video(self) -> Optional["Clip"]:
        pass  # TODO

    @staticmethod
    def _flatten_subclips(clips: Iterable[Clip]):
        for clip in clips:
            if isinstance(clip, ClipSequence):
                # Balance up
                yield from clip._clips
            else:
                # Just append
                yield clip

    @functools.cached_property
    def flags(self) -> set[ClipFlags]:
        return ClipFlags.merge_from_clips(self._clips, append=ClipFlags.HasSequence)

    @functools.cached_property
    def duration(self) -> Optional[float]:
        total_duration = 0.
        for c in self._clips:
            duration = c.duration
            if duration is None:
                # If one duration is unknown, the sum is unknown tooo.
                return None
            total_duration = total_duration + duration

        return total_duration

    def match_resolutions(self,
                          resolution: VideoResolution = None,
                          keep_aspect=True, center=True, custom: str = None):
        """
        Scales and fits a ClipSequence equally to a common resolution.
        Helper/wrapper function using transform()
        :param resolution: A specific resolution for the video.
        :param keep_aspect: Keep aspect ratio of clips. Add letterboxing if needed.
        :param center:
        :param custom:
        :return:
        """

        from scriptycut.clips.transform import Scale

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

    @property
    def definition_str(self) -> str:
        return repr(self._clips)


class RepeatClip(ClipSequence):
    def __init__(self, clip: Clip, count: int):
        if not isinstance(count, int) or count < 1:
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

    @property
    def definition_str(self) -> str:
        return f"{self._count}×{self._clip!r}"


class Libavfilter(Clip):
    """
    Create clips by ffmpeg's lavfi device
    https://ffmpeg.org/ffmpeg-devices.html#Examples-5
    """

    @property
    def definition_str(self) -> str:
        return repr((self._inputs, self._filtergraph))

    def __init__(self, filtergraph: str, duration: float, inputs: Clip | Iterable[Clip]):
        self._filtergraph = filtergraph
        self._duration = duration
        self._inputs = inputs

        Clip.__init__(self)

    def audio(self) -> Optional["Clip"]:
        pass  # TODO

    def video(self) -> Optional["Clip"]:
        pass  # TODO

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def filtergraph(self):
        return self._filtergraph

    def _repr_data(self) -> str:
        return f"{self._duration}"
