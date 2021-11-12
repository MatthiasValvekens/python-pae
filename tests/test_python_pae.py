"""
PAE encoding/decoding tests.

.. (c) 2021 Matthias Valvekens
"""

import struct
from io import BytesIO
from typing import IO

import pytest

from python_pae import (
    pae_encode, unmarshal, marshal, pae_encode_multiple,
    PAEDecodeError
)
from python_pae.abstract import PAEType
from python_pae.number import PAE_USHORT, PAE_ULLONG, PAE_UCHAR, PAE_UINT, \
    PAENumberType
from python_pae.encode import write_prefixed, PAEListSettings
from python_pae.pae_types import PAEBytes, PAEHomogeneousList, \
    PAEHeterogeneousList, PAEString

# Default list encoding settings for our tests
NO_CONST_PREFIX = PAEListSettings(
    size_type=PAE_USHORT, prefix_if_constant=False
)
WITH_CONST_PREFIX = PAEListSettings(
    size_type=PAE_USHORT, prefix_if_constant=True
)


@pytest.mark.parametrize('inp,expected_out', [
    ([b'12', b'345'], b'\x02\x00\x02\x0012\x03\x00345'),
    ([], b'\x00\x00'),
    ([b'123', b'45', b'67', b'89'],
     b'\x04\x00\x03\x00123\x02\x0045\x02\x0067\x02\x0089'),
])
def test_encode_bytes(inp, expected_out):
    encoded = pae_encode(inp, size_t=PAE_USHORT)
    assert encoded == expected_out


@pytest.mark.parametrize('inp,expected_out', [
    ([b'12', b'345'],
     b'\x02\x00\x00\x00\x02\x00\x00\x0012\x03\x00\x00\x00345'),
    ([], b'\x00\x00\x00\x00'),
    ([b'123', b'45', b'67', b'89'],
     b'\x04\x00\x00\x00\x03\x00\x00\x00123'
     b'\x02\x00\x00\x0045\x02\x00\x00\x0067\x02\x00\x00\x0089'),
])
def test_encode_bytes_uint(inp, expected_out):
    encoded = pae_encode(inp, size_t=PAE_UINT)
    assert encoded == expected_out


@pytest.mark.parametrize('inp,expected_out', [
    ([b'12', b'345'],
     b'\x02\x00\x00\x00\x02\x0012\x03\x00345'),
    ([], b'\x00\x00\x00\x00'),
    ([b'123', b'45', b'67', b'89'],
     b'\x04\x00\x00\x00\x03\x00123'
     b'\x02\x0045\x02\x0067\x02\x0089'),
])
def test_encode_bytes_mix(inp, expected_out):
    lst_type = PAEHomogeneousList(
        PAEBytes(),
        PAEListSettings(size_type=PAE_UINT, length_type=PAE_USHORT,)
    )
    encoded = marshal(inp, lst_type)
    assert encoded == expected_out


@pytest.mark.parametrize('expected_out,inp', [
    ([b'12', b'345'], b'\x02\x00\x02\x0012\x03\x00345'),
    ([], b'\x00\x00'),
    ([b'123', b'45', b'67', b'89'],
     b'\x04\x00\x03\x00123\x02\x0045\x02\x0067\x02\x0089'),
])
def test_decode_bytes(inp, expected_out):
    lst_type = PAEHomogeneousList(PAEBytes(), WITH_CONST_PREFIX)
    assert unmarshal(inp, lst_type) == expected_out


@pytest.mark.parametrize('expected_out,inp', [
    ([b'12', b'345'],
     b'\x02\x00\x00\x00\x02\x0012\x03\x00345'),
    ([], b'\x00\x00\x00\x00'),
    ([b'123', b'45', b'67', b'89'],
     b'\x04\x00\x00\x00\x03\x00123'
     b'\x02\x0045\x02\x0067\x02\x0089'),
])
def test_decode_bytes_mix(inp, expected_out):
    lst_type = PAEHomogeneousList(
        PAEBytes(),
        PAEListSettings(
            size_type=PAE_UINT,
            length_type=PAE_USHORT
        )
    )
    assert unmarshal(inp, lst_type) == expected_out


@pytest.mark.parametrize('inp,expected_out', [
    ([(b'12', PAEBytes()), (b'345', PAEBytes())],
     b'\x02\x00\x02\x0012\x03\x00345'),
    ([(1, PAE_UINT), (b'1234', PAEBytes())],
     b'\x02\x00\x04\x00\x01\x00\x00\x00\x04\x001234'),
    ([], b'\x00\x00'),
])
def test_encode_heterogeneous(inp, expected_out):
    encoded = pae_encode_multiple(inp, size_t=PAE_USHORT)
    assert encoded == expected_out


TEST_ENCODE_HETEROGENEOUS_NO_PREFIX = [
    ([b'12', b'345'],
     [PAEBytes(), PAEBytes()],
     b'\x02\x00\x02\x0012\x03\x00345'),
    ([1, b'1234'],
     [PAE_UINT, PAEBytes()],
     b'\x02\x00\x01\x00\x00\x00\x04\x001234'),
    ([1, b'', b'1234'],
     [PAE_UINT, PAEBytes(), PAEBytes()],
     b'\x03\x00\x01\x00\x00\x00\x00\x00\x04\x001234'),
]


@pytest.mark.parametrize('inp,types,expected_out',
                         TEST_ENCODE_HETEROGENEOUS_NO_PREFIX)
def test_encode_heterogeneous_const_no_prefix(inp, types, expected_out):
    lst_type = PAEHeterogeneousList(
        component_types=types, settings=NO_CONST_PREFIX
    )
    encoded = marshal(inp, lst_type)
    assert encoded == expected_out


@pytest.mark.parametrize('expected_out,types,inp', [
    ([b'12', b'345'],
     [PAEBytes(), PAEBytes()],
     b'\x02\x00\x02\x0012\x03\x00345'),
    ([1, b'1234'],
     [PAE_UINT, PAEBytes()],
     b'\x02\x00\x04\x00\x01\x00\x00\x00\x04\x001234'),
    ([1, b'', b'1234'],
     [PAE_UINT, PAEBytes(), PAEBytes()],
     b'\x03\x00\x04\x00\x01\x00\x00\x00\x00\x00\x04\x001234'),
])
def test_decode_heterogeneous(inp, types, expected_out):
    lst_type = PAEHeterogeneousList(
        component_types=types, settings=WITH_CONST_PREFIX
    )
    decoded = unmarshal(inp, lst_type)
    assert decoded == expected_out


@pytest.mark.parametrize('expected_out,types,inp',
                         TEST_ENCODE_HETEROGENEOUS_NO_PREFIX)
def test_decode_heterogeneous_const_no_prefix(inp, types, expected_out):
    lst_type = PAEHeterogeneousList(
        component_types=types, settings=NO_CONST_PREFIX
    )
    decoded = unmarshal(inp, lst_type)
    assert decoded == expected_out


@pytest.mark.parametrize('inp,pae_type', [
    (b'\x02\x00\x01\x00\x00\x00\x05',
     PAEHeterogeneousList(
         component_types=[PAE_UINT, PAEBytes()],
         settings=NO_CONST_PREFIX)),
    (b'\x01\x00\x00',
     PAEHomogeneousList(PAEBytes(), settings=NO_CONST_PREFIX))
])
def test_decode_length_prefix_error(inp, pae_type):
    with pytest.raises(PAEDecodeError, match='Failed to read length'):
        unmarshal(inp, pae_type)


@pytest.mark.parametrize('inp,pae_type', [
    (b'\x02\x00\x01\x00\x00\x00\x05\x00123',
     PAEHeterogeneousList(
         component_types=[PAE_UINT, PAEBytes()],
         settings=WITH_CONST_PREFIX)),
    (b'\x01\x00\x01\x00',
     PAEHomogeneousList(PAEBytes(), settings=NO_CONST_PREFIX))
])
def test_decode_payload_too_short(inp, pae_type):
    with pytest.raises(PAEDecodeError, match='Expected.*next item'):
        unmarshal(inp, pae_type)


@pytest.mark.parametrize('inp,pae_type', [
    (b'\x02\x00\x01\x00\x00\x00\x05\x00123456',
     PAEHeterogeneousList(
         component_types=[PAE_UINT, PAEBytes()],
         settings=NO_CONST_PREFIX)),
    (b'\x01\x00\x00\x001',
     PAEHomogeneousList(PAEBytes(), settings=NO_CONST_PREFIX))
])
def test_decode_payload_too_long(inp, pae_type):
    with pytest.raises(PAEDecodeError, match='trailing data'):
        unmarshal(inp, pae_type)


@pytest.mark.parametrize('inp,pae_type', [
    (b'\x01',
     PAEHeterogeneousList(
         component_types=[PAE_UINT, PAEBytes()],
         settings=NO_CONST_PREFIX)),
    (b'\x01',
     PAEHomogeneousList(PAEBytes(), settings=NO_CONST_PREFIX)),
    (b'\x01\x001', PAE_ULLONG),
])
def test_payload_invalid(inp, pae_type):
    with pytest.raises(PAEDecodeError, match='Failed to read value'):
        unmarshal(inp, pae_type)


@pytest.mark.parametrize('inp,pae_type', [
    (b'\x01\x00\x01\x00\x00\x00',
     PAEHeterogeneousList(
         component_types=[PAE_UINT, PAEBytes()],
         settings=NO_CONST_PREFIX)),
    (b'\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00',
     PAEHeterogeneousList(
         component_types=[PAE_UINT, PAEBytes()],
         settings=NO_CONST_PREFIX)),
])
def test_decode_wrong_component_count(inp, pae_type):
    with pytest.raises(PAEDecodeError, match='Wrong number of components'):
        unmarshal(inp, pae_type)


def test_encode_wrong_component_count():
    with pytest.raises(ValueError, match='Wrong number of components'):
        PAEHeterogeneousList(
            component_types=[PAE_UINT, PAEBytes()],
            settings=NO_CONST_PREFIX).write([1, b'2', 3], BytesIO())


def test_encode_wrong_output_length_reported():
    class WeirdType(PAEType[int]):
        # wrong length
        constant_length = 1

        def write(self, value: int, stream: IO) -> int:
            return stream.write(struct.pack('<H', value))

        def read(self, stream: IO, length: int) -> int:
            raise NotImplementedError

    with pytest.raises(IOError, match='but wrote'):
        write_prefixed(
            10, WeirdType(), BytesIO(),
            length_type=PAE_USHORT,
            prefix_if_constant=False
        )


NESTED_HETEROGENEOUS_TESTS = [
    ([1, [b'abc', b'xyz'], b'1234'],
     [PAE_UINT,
      PAEHomogeneousList(PAEBytes(), settings=WITH_CONST_PREFIX),
      PAEBytes()],
     b'\x03\x00\x04\x00\x01\x00\x00\x00'
     b'\x0c\x00\x02\x00\x03\x00abc\x03\x00xyz'
     b'\x04\x001234'),
    ([1, [b'abc', b'xyz'], 'テスト'],
     [PAE_UINT,
      PAEHomogeneousList(PAEBytes(), settings=WITH_CONST_PREFIX),
      PAEString()],
     b'\x03\x00\x04\x00\x01\x00\x00\x00'
     b'\x0c\x00\x02\x00\x03\x00abc\x03\x00xyz'
     b'\x09\x00\xe3\x83\x86\xe3\x82\xb9\xe3\x83\x88'),
    ([1, [b'', b'xyz'], [], b'1234'],
     [PAE_UINT,
      PAEHomogeneousList(PAEBytes(), settings=WITH_CONST_PREFIX),
      PAEHomogeneousList(PAEBytes(), settings=WITH_CONST_PREFIX),
      PAEBytes()],
     b'\x04\x00\x04\x00\x01\x00\x00\x00'
     b'\x09\x00\x02\x00\x00\x00\x03\x00xyz'
     b'\x02\x00\x00\x00'
     b'\x04\x001234'),
    ([1, [b'', 10, b'xyz'], [1, 2, 3], b'1234'],
     [PAE_UINT,
      PAEHeterogeneousList(
          [PAEBytes(), PAE_USHORT, PAEBytes()],
          settings=WITH_CONST_PREFIX
      ),
      PAEHomogeneousList(PAE_UCHAR, settings=WITH_CONST_PREFIX),
      PAEBytes()],
     b'\x04\x00\x04\x00\x01\x00\x00\x00'
     b'\x0d\x00\x03\x00\x00\x00\x02\x00\x0a\x00\x03\x00xyz'
     b'\x0b\x00\x03\x00\x01\x00\x01\x01\x00\x02\x01\x00\x03'
     b'\x04\x001234'),
    ([1, [b'', 10, b'xyz'], [1, 2, 3], b'1234'],
     [PAE_UINT,
      PAEHeterogeneousList(
          [PAEBytes(), PAE_USHORT, PAEBytes()],
          settings=WITH_CONST_PREFIX
      ),
      PAEHomogeneousList(PAE_UCHAR, settings=NO_CONST_PREFIX),
      PAEBytes()],
     b'\x04\x00\x04\x00\x01\x00\x00\x00'
     b'\x0d\x00\x03\x00\x00\x00\x02\x00\x0a\x00\x03\x00xyz'
     b'\x05\x00\x03\x00\x01\x02\x03'
     b'\x04\x001234'),
    ([1, [b'', 10, b'xyz'], [1, 2, 3], b'1234'],
     [PAE_UINT,
      PAEHeterogeneousList(
          [PAEBytes(), PAE_USHORT, PAEBytes()],
          settings=NO_CONST_PREFIX
      ),
      PAEHomogeneousList(PAE_UCHAR, settings=NO_CONST_PREFIX),
      PAEBytes()],
     b'\x04\x00\x04\x00\x01\x00\x00\x00'
     b'\x0b\x00\x03\x00\x00\x00\x0a\x00\x03\x00xyz'
     b'\x05\x00\x03\x00\x01\x02\x03'
     b'\x04\x001234'),
]


@pytest.mark.parametrize('expected_out,types,inp', NESTED_HETEROGENEOUS_TESTS)
def test_decode_nested(inp, types, expected_out):
    lst_type = PAEHeterogeneousList(
        component_types=types, settings=WITH_CONST_PREFIX
    )
    decoded = unmarshal(inp, lst_type)
    assert decoded == expected_out


@pytest.mark.parametrize('inp,types,expected_out', NESTED_HETEROGENEOUS_TESTS)
def test_encode_nested(inp, types, expected_out):
    encoded = pae_encode_multiple(zip(inp, types), size_t=PAE_USHORT)
    assert encoded == expected_out


def test_illegal_utf_sequence():
    with pytest.raises(PAEDecodeError, match="Failed"):
        unmarshal(b'\xee\xaa', PAEString())


def test_number_str_known():
    assert str(PAE_UCHAR) == '<uint8 (UCHAR)>'
    assert str(PAE_USHORT) == '<uint16 (USHORT)>'
    assert str(PAE_UINT) == '<uint32 (UINT)>'
    assert str(PAE_ULLONG) == '<uint64 (ULLONG)>'


def test_number_str_generic():
    assert str(PAENumberType(4)) == '<uint128>'
