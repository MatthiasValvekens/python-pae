import pytest

from python_pae import (
    pae_encode, PAENumberType, unmarshal, marshal, pae_encode_multiple
)
from python_pae.pae_types import PAEBytes, PAEHomogeneousList, \
    PAEHeterogeneousList


@pytest.mark.parametrize('inp,expected_out', [
    ([b'12', b'345'], b'\x02\x00\x02\x0012\x03\x00345'),
    ([], b'\x00\x00'),
    ([b'123', b'45', b'67', b'89'],
     b'\x04\x00\x03\x00123\x02\x0045\x02\x0067\x02\x0089'),
])
def test_encode_bytes(inp, expected_out):
    encoded = pae_encode(inp, size_t=PAENumberType.USHORT)
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
    encoded = pae_encode(inp, size_t=PAENumberType.UINT)
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
        PAEBytes(), size_type=PAENumberType.UINT,
        length_type=PAENumberType.USHORT
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
    lst_type = PAEHomogeneousList(PAEBytes(), size_type=PAENumberType.USHORT)
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
        PAEBytes(), size_type=PAENumberType.UINT,
        length_type=PAENumberType.USHORT)
    assert unmarshal(inp, lst_type) == expected_out


@pytest.mark.parametrize('inp,expected_out', [
    ([(b'12', PAEBytes()), (b'345', PAEBytes())],
     b'\x02\x00\x02\x0012\x03\x00345'),
    ([(1, PAENumberType.UINT), (b'1234', PAEBytes())],
     b'\x02\x00\x01\x00\x00\x00\x04\x001234'),
    ([], b'\x00\x00'),
])
def test_encode_heterogeneous(inp, expected_out):
    encoded = pae_encode_multiple(inp, size_t=PAENumberType.USHORT)
    assert encoded == expected_out


@pytest.mark.parametrize('expected_out,types,inp', [
    ([b'12', b'345'],
     [PAEBytes(), PAEBytes()],
     b'\x02\x00\x02\x0012\x03\x00345'),
    ([1, b'1234'],
     [PAENumberType.UINT, PAEBytes()],
     b'\x02\x00\x01\x00\x00\x00\x04\x001234'),
])
def test_decode_heterogeneous(inp, types, expected_out):
    lst_type = PAEHeterogeneousList(
        component_types=types, size_type=PAENumberType.USHORT,
    )
    decoded = unmarshal(inp, lst_type)
    assert decoded == expected_out
