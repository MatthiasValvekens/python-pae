"""
This module defines the basic abstract building blocks of the API.

.. (c) 2021 Matthias Valvekens
"""

from typing import IO, Generic, TypeVar, Optional

__all__ = [
    'PAEType', 'PAEDecodeError',
]


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
