import pytest

from python_pae import pae_encode, PAENumberType, unmarshal, marshal
from python_pae.pae_types import PAEBytes, PAEHomogeneousList


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