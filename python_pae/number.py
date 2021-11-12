"""
This module defines the unsigned number types for our PAE encoding scheme.

.. (c) 2021 Matthias Valvekens
"""

import struct
from typing import IO

from .abstract import PAEType

__all__ = [
    'PAENumberType', 'PAE_UCHAR', 'PAE_USHORT', 'PAE_UINT', 'PAE_ULLONG'
]

_STRUCT_NUMS = 'BHIQ'


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

    def __repr__(self):
        nickname = ''
        if 0 <= self.value <= 3:
            nickname = f" ({['UCHAR', 'USHORT', 'UINT', 'ULLONG'][self.value]})"

        return f'<uint{8 * 2 ** self.value}{nickname}>'


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
