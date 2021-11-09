__version__ = '0.1.0'

from typing import List

from .pae_types import PAEBytes, PAEHomogeneousList, PAEHeterogeneousList
from .encode import marshal, unmarshal
from .abstract import PAEDecodeError, PAENumberType

__all__ = [
    'pae_encode', 'pae_encode_multiple',
    'marshal', 'unmarshal', 'PAEDecodeError',
    'PAENumberType'
]


def pae_encode(lst: List[bytes],
               size_t: PAENumberType = PAENumberType.ULLONG) -> bytes:
    lst_type = PAEHomogeneousList(PAEBytes(), size_type=size_t)
    return marshal(lst, lst_type)


def pae_encode_multiple(value_type_pairs,
                        size_t: PAENumberType = PAENumberType.ULLONG) -> bytes:
    if value_type_pairs:
        values, types = zip(*value_type_pairs)
    else:
        values = types = ()
    lst_type = PAEHeterogeneousList(types, size_type=size_t)
    return marshal(values, lst_type)
