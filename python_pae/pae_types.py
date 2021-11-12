"""
This module defines the serialisation logic for a number of basic types.

.. (c) 2021 Matthias Valvekens
"""

from typing import List, TypeVar, IO

from .abstract import PAEType, PAEDecodeError
from .number import (
    PAENumberType, PAE_UCHAR, PAE_USHORT, PAE_UINT, PAE_ULLONG
)
from .encode import write_prefixed, read_pae_coro, PAEListSettings

__all__ = [
    'PAEBytes', 'PAEString',
    'PAENumberType', 'PAEHomogeneousList', 'PAEHeterogeneousList',
    'DEFAULT_HMG_LIST_SETTINGS', 'DEFAULT_HTRG_LIST_SETTINGS',
    'PAE_UCHAR', 'PAE_USHORT', 'PAE_UINT', 'PAE_ULLONG'
]


class PAEBytes(PAEType[bytes]):
    """
    Represents a raw byte string, encoded as the identity.
    """

    def write(self, value: bytes, stream: IO) -> int:
        return stream.write(value)

    def read(self, stream: IO, length: int) -> bytes:
        return stream.read(length)


class PAEString(PAEType[str]):
    """
    Represents a text string, encoded in UTF-8.
    """

    def write(self, value: str, stream: IO) -> int:
        return stream.write(value.encode('utf8'))

    def read(self, stream: IO, length: int) -> str:
        return stream.read(length).decode('utf8')


S = TypeVar('S')

DEFAULT_HMG_LIST_SETTINGS = PAEListSettings(prefix_if_constant=False)
"""
Default list settings for homogeneous lists.
"""


class PAEHomogeneousList(PAEType[List[S]]):
    """
    Homogeneous list of length-prefixed items.

    :param child_type:
        The type of the list's elements.

    :param settings:
        Encoding settings for the list.
    """

    def __init__(self, child_type: PAEType[S],
                 settings: PAEListSettings = DEFAULT_HMG_LIST_SETTINGS):
        self.child_type = child_type
        self.settings = settings

    def write(self, value: List[S], stream: IO) -> int:
        settings = self.settings
        size_t = settings.size_type
        count = size_t.write(len(value), stream)
        for item in value:
            count += write_prefixed(
                item, self.child_type, stream,
                length_type=settings.length_type or size_t,
                prefix_if_constant=settings.prefix_if_constant
            )
        return count

    def read(self, stream: IO, length: int) -> List[S]:
        coro = read_pae_coro(stream, self.settings, expected_length=length)
        part_count = next(coro)
        result = [None] * part_count
        # I suppose [coro.send(self.child_type) for _ in coro] would also work,
        # but that just feels evil.
        for ix in range(part_count):
            result[ix] = coro.send(self.child_type)
        return result


DEFAULT_HTRG_LIST_SETTINGS = PAEListSettings(prefix_if_constant=True)
"""
Default list settings for heterogeneous lists.
"""


class PAEHeterogeneousList(PAEType[list]):
    """
    Heterogeneous, fixed-length list of length-prefixed items, or a tuple.

    :param component_types:
        The list of types that appear as the list's components, in order.

    :param settings:
        Encoding settings for the list.
    """

    def __init__(self, component_types: List[PAEType],
                 settings: PAEListSettings = DEFAULT_HTRG_LIST_SETTINGS):
        self.component_types = component_types
        self.settings = settings

    def write(self, value: list, stream: IO) -> int:
        settings = self.settings
        size_t = settings.size_type
        count = size_t.write(len(value), stream)
        if len(value) != len(self.component_types):
            raise ValueError(
                f"Wrong number of components, expected "
                f"{len(self.component_types)} but got {len(value)}."
            )
        for item, pae_type in zip(value, self.component_types):
            count += write_prefixed(
                item, pae_type, stream,
                length_type=settings.length_type or size_t,
                prefix_if_constant=settings.prefix_if_constant
            )
        return count

    def read(self, stream: IO, length: int) -> list:
        coro = read_pae_coro(
            stream, settings=self.settings, expected_length=length
        )
        part_count = next(coro)
        if len(self.component_types) != part_count:
            raise PAEDecodeError(
                f"Wrong number of components, expected "
                f"{len(self.component_types)} but got {part_count}."
            )
        result = [None] * part_count
        for ix, pae_type in enumerate(self.component_types):
            result[ix] = coro.send(pae_type)
        return result
