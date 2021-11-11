"""
This module defines the basic abstract building blocks of the API.

.. (c) 2021 Matthias Valvekens
"""

import struct
from typing import IO, Generic, TypeVar, Optional

__all__ = [
    'PAEType', 'PAENumberType', 'PAEDecodeError',
    'PAE_UCHAR', 'PAE_USHORT', 'PAE_UINT', 'PAE_ULLONG'
]


_STRUCT_NUMS = 'BHIQ'


class PAEDecodeError(ValueError):
    """Raised if an error occurs during PAE decoding."""
    pass


T = TypeVar('T')


class PAEType(Generic[T]):
    """
    Provides a serialisation implementation for a particular type of values.
    """

    constant_length: Optional[int] = None
    """
    If not ``None``, the output length of the :meth:`write` method
    must always be equal to the value of this property.

    Length prefixes for types with a fixed byte length can optionally be
    omitted.
    """

    def write(self, value: T, stream: IO) -> int:
        """
        Serialise and write a value to a stream, length prefix *not* included.

        :param value:
            The value to write.
        :param stream:
            The stream to write to.
        :return:
            The number of bytes written.
        """
        raise NotImplementedError

    def read(self, stream: IO, length: int) -> T:
        """
        Read a value from a stream, length prefix *not* included, and decode it.

        :param stream:
            The stream to write to.
        :param length:
            The expected length of the content to be read.
        :return:
            The decoded value.
        """
        raise NotImplementedError


class PAENumberType(PAEType[int]):
    """
    Encodes various unsigned integer types.
    All are encoded in little-endian order.
    """

    def __init__(self, value):
        self.value = value

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


PAE_UCHAR = PAENumberType(0)
"""
Unsigned char, encodes to a single byte.
"""

PAE_USHORT = PAENumberType(1)
"""
Unsigned short, encodes to two bytes.
"""

PAE_UINT = PAENumberType(2)
"""
Unsigned int, encodes to four bytes.
"""

PAE_ULLONG = PAENumberType(3)
"""
Unsigned (long) long, encodes to eight bytes.
"""
