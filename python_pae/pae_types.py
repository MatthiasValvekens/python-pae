from typing import List, TypeVar, IO

from .abstract import PAEType, PAENumberType
from .encode import write_prefixed, read_pae_coro


__all__ = [
    'PAEBytes', 'PAENumberType', 'PAEHomogeneousList', 'PAEHeterogeneousList'
]


class PAEBytes(PAEType[bytes]):

    def write(self, value: bytes, stream: IO) -> int:
        return stream.write(value)

    def read(self, stream: IO, length: int) -> bytes:
        return stream.read(length)


S = TypeVar('S')


class PAEHomogeneousList(PAEType[List[S]]):
    """
    Homogeneous list of length-prefixed items.
    """

    def __init__(self, child_type: PAEType[S], size_type: PAENumberType,
                 length_type: PAENumberType = None):
        self.child_type = child_type
        self.size_type = size_type
        self.length_type = length_type or size_type

    def write(self, value: List[S], stream: IO) -> int:
        count = self.size_type.write(len(value), stream)
        for item in value:
            count += write_prefixed(
                item, self.child_type, stream,
                length_type=self.length_type
            )
        return count

    def read(self, stream: IO, length: int) -> List[S]:
        coro = read_pae_coro(
            stream, size_type=self.size_type, length_type=self.length_type,
            expected_length=length
        )
        part_count = next(coro)
        result = [None] * part_count
        # I suppose [coro.send(self.child_type) for _ in coro] would also work,
        # but that just feels evil.
        for ix in range(part_count):
            result[ix] = coro.send(self.child_type)
        return result


class PAEHeterogeneousList(PAEType[list]):
    def __init__(self, component_types: List[PAEType], size_type: PAENumberType,
                 length_type: PAENumberType = None):
        self.component_types = component_types
        self.size_type = size_type
        self.length_type = length_type or size_type

    def write(self, value: list, stream: IO) -> int:
        count = self.size_type.write(len(value), stream)
        if len(value) != len(self.component_types):
            raise ValueError(
                f"Wrong number of components, expected "
                f"{len(self.component_types)} but got {len(value)}."
            )
        for item, pae_type in zip(value, self.component_types):
            count += write_prefixed(
                item, pae_type, stream, length_type=self.length_type
            )
        return count

    def read(self, stream: IO, length: int) -> list:
        coro = read_pae_coro(
            stream, size_type=self.size_type, length_type=self.length_type,
            expected_length=length
        )
        part_count = next(coro)
        if len(self.component_types) != part_count:
            raise ValueError(
                f"Wrong number of components, expected "
                f"{len(self.component_types)} but got {part_count}."
            )
        result = [None] * part_count
        for ix, pae_type in enumerate(self.component_types):
            result[ix] = coro.send(pae_type)
        return result
