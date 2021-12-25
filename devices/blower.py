import struct
from typing import Optional
from fastapi_utils.api_model import APIModel
from pydantic import validator
from utils import modbus


class Blower(APIModel):
    address: int  # 9600 buadrate
    is_on: Optional[int]
    _min_address: int = 235  # has to be 235-239, #comm params buadrate 19200
    _max_address: int = 239

    @classmethod
    @validator('address')
    def address_must_be_in_range(cls, address: int) -> int:
        if not cls._min_address <= address <= cls._max_address:
            raise ValueError(f'must be between {cls._min_address} and {cls._max_address}')
        return address

    @classmethod
    def identify(cls, raw_data: bytes) -> bool:
        address = int(raw_data[3])
        if cls._min_address <= address <= cls._max_address:
            return True
        return False

    def __repr__(self):
        return f"Blower {self.address}"

    def set_state(self, state: bool) -> bytes:
        if state:
            value = 1  # active - forward
        else:
            value = 5  # stop
        return modbus.modbus_write_single_register(self.address, 2000, value)

    def request_state(self) -> bytes:
        return modbus.modbus_read_registers(self.address, 3000, 1)

    def parse_is_on(self) -> str:
        if self.is_on == 1:
            return 'Blower is On'
        if self.is_on == 2:
            return 'Blower is in reverse state!, FIX IMMEDIATELY'
        if self.is_on == 3:
            return 'Blower is Off'
        else:
            return 'Unknown'

    def parse_raw_data(self, gw_sn: str, raw_data: bytes):
        raw_data = raw_data[3:-3]
        address, msg_len, is_on = struct.unpack_from('BBH', raw_data)
        self.is_on = is_on
        return {'address': address, 'is_on': is_on, 'gw_sn': gw_sn}

    def change_address(self, destination_address: int) -> bytes:
        self.address = destination_address
        return modbus.modbus_write_request(address=self.address, start_data_address=48, values=[destination_address])
