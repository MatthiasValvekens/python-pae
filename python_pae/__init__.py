"""
This is the main entry point for the PAE encoding/decoding API.

.. (c) 2021 Matthias Valvekens
"""


__version__ = '0.1.0'

from typing import List

from .pae_types import PAEBytes, PAEHomogeneousList, PAEHeterogeneousList
from .encode import marshal, unmarshal, PAEListSettings
from .abstract import PAEDecodeError
from .number import PAENumberType, PAE_ULLONG

__all__ = [
    'pae_encode', 'pae_encode_multiple',
    'marshal', 'unmarshal', 'PAEListSettings',
    'PAEDecodeError',
]


def pae_encode(lst: List[bytes], size_t: PAENumberType = PAE_ULLONG) -> bytes:
    """
    Encode a list of byte strings in PAE.

    .. note::
        By default, this function produces output that is compatible with
        PASETO PAE.

    :param lst:
        A list of byte strings.
    :param size_t:
        Numeric type to use for the list's size and its members' length
        prefixes.
    :return:
        The PAE-encoded list as a byte string.
    """

    settings = PAEListSettings(size_type=size_t)
    lst_type = PAEHomogeneousList(PAEBytes(), settings=settings)
    return marshal(lst, lst_type)


def pae_encode_multiple(value_type_pairs,
                        size_t: PAENumberType = PAE_ULLONG) -> bytes:
    """
    Encode a list of multiple typed values in PAE.

    :param value_type_pairs:
        A list of tuples of the form ``(v, t)``, where ``v`` is a value,
        and ``t`` is a :class:`~python_pae.abstract.PAEType` implementation
        for that value type.
    :param size_t:
        Numeric type to use for the list's size and its members' length
        prefixes.
    :return:
        The PAE-encoded list as a byte string.
    """

    settings = PAEListSettings(size_type=size_t)
    if value_type_pairs:
        values, types = zip(*value_type_pairs)
    else:
        values = types = ()
    lst_type = PAEHeterogeneousList(types, settings=settings)
    return marshal(values, lst_type)
