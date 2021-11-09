import os
from io import BytesIO
from typing import IO, TypeVar


from .abstract import PAEType, PAENumberType, PAEDecodeError

__all__ = [
    'marshal', 'unmarshal',
    'write_prefixed', 'read_prefixed_coro', 'read_pae_coro'
]

T = TypeVar('T')


def write_prefixed(value: T, pae_type: PAEType[T],
                   stream: IO, length_type: PAENumberType):
    if pae_type.constant_length is not None:
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


def read_prefixed_coro(pae_type: PAEType[T], stream: IO,
                       length_type: PAENumberType):
    if pae_type.constant_length is None:
        pref_length = length_type.constant_length
        try:
            length = length_type.unpack(stream.read(pref_length))
        except (IOError, ValueError):
            raise PAEDecodeError(
                f"Failed to read length prefix for value of type {pae_type}"
            )
        total_length = pref_length + length
    else:
        length = total_length = pae_type.constant_length
    yield total_length

    try:
        value = pae_type.read(stream, length)
    except (IOError, ValueError):
        raise PAEDecodeError(f"Failed to read value for PAE type {pae_type}")
    yield value


def unmarshal(packed: bytes, pae_type: PAEType[T]) -> T:
    return pae_type.read(BytesIO(packed), length=len(packed))


def read_pae_coro(stream: IO,
                  size_type: PAENumberType, length_type: PAENumberType,
                  expected_length=None):
    part_count = size_type.read(stream, size_type.constant_length)
    bytes_read = size_type.constant_length
    next_pae_type: PAEType
    # noinspection PyTypeChecker
    next_pae_type = yield part_count
    for _ in range(part_count):
        part_coro = read_prefixed_coro(next_pae_type, stream, length_type)
        part_len: int = next(part_coro)
        bytes_read += part_len
        if expected_length is not None and bytes_read > expected_length:
            raise PAEDecodeError(
                f"Expected a payload of length {expected_length}; next item "
                f"too long: would need at least {bytes_read}"
            )
        next_pae_type = yield next(part_coro)
    if expected_length is not None and bytes_read != expected_length:
        raise ValueError(
            f"Expected a payload of length {expected_length},"
            f"but read {bytes_read} bytes."
        )
