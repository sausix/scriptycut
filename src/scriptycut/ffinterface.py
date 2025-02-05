# -*- coding: utf-8 -*-

from typing import Optional, Iterable, Union, Generator, Iterator, Any
from pathlib import Path
from types import GeneratorType

PathLike = Union[str, bytes, Path]
SupportedTypes = PathLike | int | float | str
ArgumentTypes = Optional[SupportedTypes | Iterable[SupportedTypes]]


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

class ClioIOCache:



class FFArgs:
    def __init__(self, args: ArgumentTypes):
        self._args = tuple(unpack_args(args))

    def args(self) -> tuple[str, ...]:
        return self._argsv


class GeneralArgs(FFArgs):
    """
    These arguments appear first on the command line
    """


class FFargInput(FFArgs):
    def __init__(self, input_file: PathLike, input_args: ArgumentTypes = None):
        FFArgs.__init__(self, tuple(unpack_args(input_args)) + ("-i", input_file))


class FFargOutput(FFArgs):
    def __init__(self, output_file: PathLike, input_args: ArgumentTypes = None):
        FFArgs.__init__(self, tuple(unpack_args(input_args)) + ("-i", input_file))


FFArgsInterface = Union[FFArgs, Iterable[FFArgs]]


# data = [1, 2, ["a", "b"], 4, 5]
# print(list(unpack_args(data)))

