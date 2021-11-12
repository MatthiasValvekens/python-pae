"""
This module defines helper functions and coroutines for encoding and decoding
PAE values.

.. (c) 2021 Matthias Valvekens
"""

import os
import struct
from dataclasses import dataclass
from io import BytesIO
from typing import IO, TypeVar, Optional

from .abstract import PAEType, PAEDecodeError

from .number import PAENumberType, PAE_ULLONG

__all__ = [
    'marshal', 'unmarshal',
    'write_prefixed', 'read_prefixed_coro', 'read_pae_coro',
    'PAEListSettings'
]


@dataclass(frozen=True)
class PAEListSettings:
    """
    List encoding settings. The defaults represent the PASETO version of PAE.
    """

    size_type: PAENumberType = PAE_ULLONG
    """
    Numeric type to use for the list size.

    .. note::
        The default is a 64-bit integer for compatibility with PASETO PAE.
    """

    length_type: Optional[PAENumberType] = None
    """
    Numeric type to use for the length prefixes of the list items.

    .. note::
        If unspecified, will be the same as :attr:`size_type`.
    """

    prefix_if_constant: bool = True
    """
    Flag toggling whether to apply the length prefix if the type
    being written or read is a fixed-width type. Defaults to ``True``.
    """


T = TypeVar('T')


def write_prefixed(value: T, pae_type: PAEType[T],
                   stream: IO, length_type: PAENumberType,
                   prefix_if_constant: bool = True) -> int:
    """
    Write a value to a stream, prefixed with the length of the serialised
    payload.

    .. note::
        The output stream must be seekable for this to work.

    :param value:
        The value to write.
    :param pae_type:
        The :class:`.PAEType` that provides the serialisation logic.
    :param stream:
        The output stream to write to.
    :param length_type:
        Numeric type to use for the length prefix.
    :param prefix_if_constant:
        Flag toggling whether to apply the length prefix if the type
        being written is a fixed-width type.
        Defaults to ``True``.
    :return:
        The number of bytes written (including the length prefix, if present).
    """
    if pae_type.constant_length is not None and not prefix_if_constant:
        # length is constant -> no prefix necessary
        total_written = pae_type.write(value, stream)
        if total_written != pae_type.constant_length:
            raise IOError(
                f"Expected to write {pae_type.constant_length} bytes,"
                f"but wrote {total_written}."
            )
        return total_written

    pref_len = length_type.constant_length
    stream.write(bytes(pref_len))  # placeholder
    total_written = pae_type.write(value, stream)
    # backtrack to fill in length prefix
    stream.seek(-total_written - pref_len, os.SEEK_CUR)
    stream.write(length_type.pack(total_written))
    stream.seek(total_written, os.SEEK_CUR)
    return total_written + pref_len


def marshal(value: T, pae_type: PAEType[T]) -> bytes:
    """
    Serialise a value into bytes.

    :param value:
        The value to be processed.
    :param pae_type:
        The :class:`.PAEType` that provides the serialisation logic.
    :return:
        A byte string representing the value passed in.
    """
    out = BytesIO()
    pae_type.write(value, out)
    return out.getvalue()


def _read_with_errh(pae_type, stream, length):
    try:
        value = pae_type.read(stream, length)
    except PAEDecodeError:
        raise
    except (IOError, ValueError, struct.error) as e:
        raise PAEDecodeError(
            f"Failed to read value for PAE type {pae_type}"
        ) from e
    return value


def read_prefixed_coro(pae_type: PAEType[T], stream: IO,
                       length_type: PAENumberType,
                       prefix_if_constant: bool = True):
    """
    Coroutine that reads and parses a length-prefixed value.
    The coroutine yields at most twice.
    First, the expected length is yielded. Next, the value is decoded
    and yielded.

    .. note::
        The idea is that the caller can abort the parse based on the length
        value.

    :param pae_type:
        The :class:`.PAEType` that provides the deserialisation logic.
    :param stream:
        The stream to read from.
    :param length_type:
        Numeric type to use for the length prefix.
    :param prefix_if_constant:
        Flag toggling whether to expect a length prefix if the type
        being read is a fixed-width type. Defaults to ``True``.
    :raises python_pae.PAEDecodeError:
        if an error occurs in the decoding process.
    :return:
        A generator object.
    """
    if prefix_if_constant or pae_type.constant_length is None:
        pref_length = length_type.constant_length
        try:
            length = length_type.unpack(stream.read(pref_length))
        except (IOError, ValueError, struct.error) as e:
            raise PAEDecodeError(
                f"Failed to read length prefix for value of type {pae_type}"
            ) from e
        total_length = pref_length + length
    else:
        length = total_length = pae_type.constant_length
    yield total_length

    yield _read_with_errh(pae_type, stream, length)


def unmarshal(packed: bytes, pae_type: PAEType[T]) -> T:
    """
    Decode a byte string back into a value.
    Inverse operation of :func:`marshal`.

    :param packed:
        The byte string to be processed.
    :param pae_type:
        The :class:`.PAEType` that provides the deserialisation logic.
    :return:
        A decoded value.
    :raises python_pae.PAEDecodeError:
        if an error occurs in the decoding process.
    """
    return _read_with_errh(pae_type, BytesIO(packed), length=len(packed))


def read_pae_coro(stream: IO, settings: PAEListSettings, expected_length=None):
    """
    Coroutine to read a (possibly heterogeneous) PAE-encoded list.

    The protocol is as follows:

        1. First, the coroutine parses and yields the number of list elements.
        2. Then, the caller should ``.send()`` in a :class:`.PAEType` object,
           after which the coroutine will yield a value.
        3. Repeat step 2 for each element of the list.

    The coroutine-based approach allows for a degree of freedom in the schema
    (e.g. optional fields), while still parsing on an on-demand basis.

    :param stream:
        The stream to read from.
    :param settings:
        List encoding settings.
    :param expected_length:
        The expected byte length of the encoded list payload.
        If ``None``, the length is not enforced.
    :raises python_pae.PAEDecodeError:
        if an error occurs in the decoding process.
    :return:
        A generator object.
    """
    size_t = settings.size_type
    length_t = settings.length_type or size_t
    part_count = size_t.read(stream, size_t.constant_length)
    bytes_read = size_t.constant_length
    next_pae_type: PAEType
    # noinspection PyTypeChecker
    next_pae_type = yield part_count
    for ix in range(part_count):
        part_coro = read_prefixed_coro(
            next_pae_type, stream, length_t,
            prefix_if_constant=settings.prefix_if_constant
        )
        try:
            part_len: int = next(part_coro)
        except StopIteration as e:  # pragma: nocover
            raise RuntimeError("Coroutine protocol violation") from e
        bytes_read += part_len
        if expected_length is not None:
            if bytes_read > expected_length:
                raise PAEDecodeError(
                    f"Expected a payload of length {expected_length}; next "
                    f"item too long: would need at least {bytes_read}"
                )
            elif ix == part_count - 1 and bytes_read != expected_length:
                # before yielding the last item, check for trailing data
                raise PAEDecodeError(
                    f"Expected a payload of length {expected_length},"
                    f"but read {bytes_read} bytes; trailing data."
                )
        try:
            next_pae_type = yield next(part_coro)
        except StopIteration as e:  # pragma: nocover
            raise RuntimeError("Coroutine protocol violation") from e
