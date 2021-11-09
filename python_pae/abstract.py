import enum
import struct
from typing import IO, Generic, TypeVar

__all__ = [
    'PAEType', 'PAENumberType',
    'PAEDecodeError',
]

_STRUCT_NUMS = 'BHIQ'


class PAEDecodeError(ValueError):
    pass


T = TypeVar('T')


class PAEType(Generic[T]):
    constant_length = None

    def write(self, value: T, stream: IO) -> int:
        raise NotImplementedError

    def read(self, stream: IO, length: int) -> T:
        raise NotImplementedError


class PAENumberType(PAEType[int], enum.Enum):
    UCHAR = 0
    USHORT = 1
    UINT = 2
    ULLONG = 3

    @property
    def constant_length(self):
        return 2 ** self.value

    def unpack(self, packed: bytes):
        return struct.unpack(f'<{_STRUCT_NUMS[self.value]}', packed)[0]

    def pack(self, value: int):
        return struct.pack(f'<{_STRUCT_NUMS[self.value]}', value)

    def write(self, value: int, stream: IO) -> int:
        return stream.write(self.pack(value))

    def read(self, stream: IO, length: int) -> int:
        return self.unpack(stream.read(self.constant_length))
