from typing import List, TypeVar, IO

from .abstract import PAEType, PAENumberType, PAEDecodeError
from .encode import write_prefixed, read_pae_coro, PAEListSettings

__all__ = [
    'PAEBytes', 'PAEString',
    'PAENumberType', 'PAEHomogeneousList', 'PAEHeterogeneousList',
    'DEFAULT_HMG_LIST_SETTINGS', 'DEFAULT_HTRG_LIST_SETTINGS'
]


class PAEBytes(PAEType[bytes]):

    def write(self, value: bytes, stream: IO) -> int:
        return stream.write(value)

    def read(self, stream: IO, length: int) -> bytes:
        return stream.read(length)


class PAEString(PAEType[str]):

    def write(self, value: str, stream: IO) -> int:
        return stream.write(value.encode('utf8'))

    def read(self, stream: IO, length: int) -> str:
        return stream.read(length).decode('utf8')


S = TypeVar('S')

DEFAULT_HMG_LIST_SETTINGS = PAEListSettings(prefix_if_constant=False)


class PAEHomogeneousList(PAEType[List[S]]):
    """
    Homogeneous list of length-prefixed items.
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


class PAEHeterogeneousList(PAEType[list]):
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
