import struct
from typing import List


def get_device_type_and_address(raw_data):
    if is_lamp(raw_data):
        return 'Lamp', int(raw_data[9])
    elif is_sensor(raw_data):
        return 'Sensor', int(raw_data[3])
    elif is_blower(raw_data):
        return 'Blower', int(raw_data[3])
    else:
        raise TypeError('Could not parse the incoming information')


def is_lamp(raw_data: bytes) -> bool:
    if raw_data[3:8] == b'\x00\x00\x00\x00\x00':
        return True
    return False


def is_sensor(raw_data: bytes) -> bool:
    address = int(raw_data[3])
    if 230 <= address <= 234:
        return True
    return False


def is_blower(raw_data: bytes) -> bool:
    address = int(raw_data[3])
    if 235 <= address <= 239:
        return True
    return False


def _calc_crc(raw_data: bytes) -> bytes:
    crc = 0xFFFF
    for pos in raw_data:
        crc ^= pos
        for i in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)


def amnor_modbus_r_w_registers(address, opcode: int, params: List[int], is_query: bool) -> bytes:
    msg = struct.pack(f'>{len(params)}H', *[int(i) for i in params])
    if not is_query:
        msg = struct.pack(f'>HB', len(params), 2 * len(params)) + msg
        modbus_opcode = 0x10
    else:
        modbus_opcode = 0x3
    msg = struct.pack(f'>BBH', address, modbus_opcode, opcode) + msg
    msg = struct.pack(">3H", 0, 0, len(msg)) + msg
    msg += _calc_crc(msg)
    msg = add_warp_v209s(msg)
    return msg


def add_warp_v209s(msg: bytes) -> bytes:
    return struct.pack("HB", 2, len(msg)) + msg + b'\x03'


def modbus_read_registers(address: int, start_data_address: int, amount_of_registers_to_read: int) -> bytes:
    function_code = 3  # opcode read
    msg = struct.pack(f'>BB2H', address, function_code, start_data_address, amount_of_registers_to_read)
    msg += _calc_crc(msg)
    msg = add_warp_v209s(msg)
    return msg


def modbus_read_response(msg: bytes) -> dict:
    address, function_code, msg_len = struct.unpack_from('BBB', msg)
    values = struct.unpack_from(f'>{msg_len // 2}H', msg, 3)
    return {'address': address, 'register_count': msg_len // 2, 'values': values}


def modbus_write_single_register(address: int, start_data_address: int, value: int) -> bytes:
    function_code = 6  # opcode single write
    msg = struct.pack('2BH', address, function_code, start_data_address - 1)
    msg += struct.pack(f'H', value)
    msg += _calc_crc(msg)
    msg = add_warp_v209s(msg)
    return msg


def modbus_write_single_response(msg: bytes) -> dict:
    address, function_code, data_address, value, crc = struct.unpack_from('BBHHH', msg)
    return {'address': address, 'data_address': data_address, 'value': value}


def modbus_write_request(address: int, start_data_address: int, values: List[int]) -> bytes:
    amount_of_registers_to_write = len(values)
    function_code = 16  # opcode write
    msg = struct.pack('>2BH', address, function_code, start_data_address)
    msg += struct.pack('>HB', amount_of_registers_to_write, amount_of_registers_to_write * 2)
    for v in values:
        msg += struct.pack('>H', v)
    msg += _calc_crc(msg)
    msg = add_warp_v209s(msg)
    return msg
