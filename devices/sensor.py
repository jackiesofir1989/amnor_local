import logging

from fastapi_utils.api_model import APIModel
from pydantic import validator

from utils import modbus


class Sensor(APIModel):
    address: int
    ppfd: float = 0.0
    _min_address: int = 230  # has to be 235-239, #comm params buadrate 19200
    _max_address: int = 234

    def __repr__(self):
        return f'Sensor {self.address} - PPFD {self.ppfd}'

    def __str__(self):
        return f'Sensor {self.address} - PPFD {self.ppfd}'

    @classmethod
    @validator('address')
    def address_must_be_in_range(cls, address: int) -> int:
        if not cls._min_address <= address <= cls._max_address:
            raise ValueError(f'must be between {cls._min_address} and {cls._max_address}')
        return address

    def identify(cls, raw_data: bytes) -> bool:
        address = int(raw_data[3])
        if cls._min_address <= address <= cls._max_address:
            return True
        return False

    def request_light_level(self) -> bytes:
        return modbus.modbus_read_registers(self.address, 40, 1)

    def response_light_level(self, msg: bytes) -> dict:
        _dict = modbus.modbus_read_response(msg)
        if self.address != _dict['address']:
            raise Exception('This is not my response!')
        return _dict

    def parse_raw_data(self, gw_sn: str, raw_data: bytes) -> dict:
        """parse the response from modbus packet, the light level is returned as calibrated
        output µmol m⁻² s⁻¹ (shifted one decimal point to the left)"""
        logging.debug(raw_data)
        parsed_dict = self.response_light_level(raw_data[3:-1])
        self.ppfd = parsed_dict['values'][0] / 10
        if self.ppfd > 6000:
            self.ppfd = 0.0
        d = {'address': self.address, 'ppfd': self.ppfd, 'gw_sn': gw_sn}
        logging.warning(self.__str__())
        return d
