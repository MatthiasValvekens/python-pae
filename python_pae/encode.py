import os
import struct
from dataclasses import dataclass
from io import BytesIO
from typing import IO, TypeVar, Optional

from .abstract import PAEType, PAENumberType, PAEDecodeError

__all__ = [
    'marshal', 'unmarshal',
    'write_prefixed', 'read_prefixed_coro', 'read_pae_coro',
    'PAEListSettings'
]


@dataclass(frozen=True)
class PAEListSettings:
    size_type: PAENumberType = PAENumberType.ULLONG
    length_type: Optional[PAENumberType] = None
    prefix_if_constant: bool = True


T = TypeVar('T')


def write_prefixed(value: T, pae_type: PAEType[T],
                   stream: IO, length_type: PAENumberType,
                   prefix_if_constant: bool = True):
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
    return _read_with_errh(pae_type, BytesIO(packed), length=len(packed))


def read_pae_coro(stream: IO,
                  settings: PAEListSettings,
                  expected_length=None):
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
        part_len: int = next(part_coro)
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
        next_pae_type = yield next(part_coro)
