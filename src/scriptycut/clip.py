# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from typing import Optional, Set, Tuple, Union
from collections.abc import Iterable, Sequence, Generator
from functools import cached_property
from itertools import chain

from scriptycut.cache import Cache, ClipCachePref
from scriptycut.common import Pathlike
from scriptycut.fftools import FFMPEG
from scriptycut.clipflags import ClipFlags


class Clip(metaclass=ABCMeta):
    """
    The base class representing audio and/or video over a time span from a source.
    Clip and their derived subclasses are always immutable!
    """

    # Class constants
    RENDER_NEEDS_FRAMEINDEX = False
    RENDER_NEEDS_CLIPTIME = False
    RENDER_NEEDS_ABSTIME = False
    CACHE_PREF = ClipCachePref.DEPENDS_ASK_INSTANCE  # Subclasses can define a default behaviour

    # Class variables
    _root_cache: Optional[Cache] = None

    @classmethod
    def set_root_cache(cls, cache: Cache):
        """Defines the root cache of a Clip or a subclass for all derived classes and instances"""
        cls._root_cache = cache

    def __init__(self, cachepref: ClipCachePref):
        if self._root_cache is None:
            # Create a global cache in Clip
            Clip._root_cache = Cache()

        self._cachepref = self.CACHE_PREF if cachepref is ClipCachePref.CLASS_DEFAULT else cachepref

        # Provide unique cache name
        self.cachedir = self._root_cache.get_item_folder(
            self.__class__.__name__,
            f"{self.av_info_str}:{self._repr_data()}"
        )

        self._video_fps: Optional[float] = None

    @property
    def has_video(self) -> bool:
        """Shorthand property if clip or a subclip has video"""
        return ClipFlags.HasVideo in self.flags

    @property
    def has_audio(self) -> bool:
        """Shorthand property if clip or a subclip has audio"""
        return ClipFlags.HasAudio in self.flags

    @property
    def flags(self) -> Set[ClipFlags]:
        """The clip can report his an his subclips' flags"""
        return {ClipFlags.MissingResource}

    @property
    def video_fps(self) -> Optional[float]:
        return self._video_fps

    @property
    def duration(self) -> float:
        """
        Duration in seconds which should be fixed.
        Could be overridden and calculated on demand. Cache it if possible.
        :return: Length of the Clip in seconds
        """
        return 0.

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
        Allows simple concatenation of clips: clip1 + clip2
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

    # __iter__ : subclips?

    def __getitem__(self, item):
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

    def scale_fit(self,
                  width: int = None, height: int = None,
                  from_master=False, keep_aspect=True, center=True, custom: str = None,
                  cachepref=ClipCachePref.DEPENDS_ASK_INSTANCE):
        """
        Scales and fits a Clip (or a ClipSequence equally) to a common resolution.
        Helper/wrapper function using transform()
        :param width:
        :param height:
        :param from_master: Use width and height from a containing master clip.
        :param keep_aspect: Keep aspect ratio of clips. Add black bars.
        :param center:
        :param custom:
        :param cachepref: Caching policy
        :return:
        """

        from scriptycut.transform import ScaleFit
        return ScaleFit(self, width, height, from_master, keep_aspect, center, custom, cachepref)

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
        return f"<{self.__class__.__name__}{self.av_info_str}:{self._repr_data()}>"


class ClipSequence(Clip):
    """
    Full reencode
    ffmpeg -i opening.mkv -i episode.mkv -i ending.mkv
        -filter_complex "[0:v] [0:a] [1:v] [1:a] [2:v] [2:a] concat=n=3:v=1:a=1 [v] [a]"
        -map "[v]" -map "[a]" output.mkv

    Concat Demux
    cat mylist.txt
    file '/path/to/file1'
    file '/path/to/file2'
    file '/path/to/file3'

    ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.mp4
    """

    auto_flatten = True  # Should be True by default. Else clip1 + clip2 + clip3 creates a tree structure.

    def __init__(self, clips: Iterable[Clip], auto_flatten: bool = None, cachepref=ClipCachePref.DEPENDS_ASK_INSTANCE):
        if auto_flatten or (auto_flatten is None and self.auto_flatten):
            self._clips = tuple(self._flatten_subclips(clips))
        else:
            self._clips = tuple(clips)

        if len(self._clips) == 0:
            raise ValueError("Empty ClipSequences are not allowed.")

        Clip.__init__(self, cachepref)

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
        clip_flags = (c.flags for c in self._clips)
        # return set().union(chain.from_iterable(clip_flags)) | {ClipFlags.HasSequence}
        return set(chain.from_iterable(clip_flags)) | {ClipFlags.HasSequence}  # TODO: OK?

    @cached_property
    def duration(self) -> float:
        return sum(c.duration for c in self._clips)

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
    def __init__(self, clip: Clip, count: int, cachepref=ClipCachePref.DEPENDS_ASK_INSTANCE):
        if not isinstance(count, int) or count<1:
            raise ValueError("Count must be int >= 1")

        self._clip = clip
        self._count = count
        ClipSequence.__init__(self, [clip] * count, cachepref)

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
