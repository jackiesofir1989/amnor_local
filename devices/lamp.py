import logging
from datetime import datetime
from typing import List, Optional

from fastapi_utils.api_model import APIModel
from pydantic import validator

from devices.group import Group
from routes.lamp import LampLogCreate
from utils import modbus


class Lamp(APIModel):
    address: int
    location: List[int]
    group_membership: List[int]
    group: Optional[Group] = None
    lamp_log: LampLogCreate = LampLogCreate()
    _min_address: int = 1  # has to be 235-239, #comm params buadrate 19200
    _max_address: int = 239
    timestamp: datetime = datetime.now()

    @classmethod
    @validator('address')
    def address_must_be_in_range(cls, address: int) -> int:
        if not cls._min_address <= address <= cls._max_address:
            raise ValueError(f'must be between {cls._min_address} and {cls._max_address}')
        return address

    @classmethod
    @validator('group_membership', pre=True)
    def check_group_membership(cls, group_membership: List[int]) -> List[int]:
        # returns non duplicated sorted list
        min_group_membership: int = 1
        max_group_membership: int = 16
        for g in group_membership:
            if not min_group_membership <= g <= max_group_membership:
                raise ValueError(f'must be between {min_group_membership} and {max_group_membership}')
        return sorted(list(dict.fromkeys(group_membership)))

    # noinspection PyMethodParameters
    def identify(cls, raw_data: bytes) -> bool:
        address = int(raw_data[9])
        if cls._min_address <= address <= cls._max_address:
            return True
        return False

    def __str__(self):
        return f"Lamp {self.address}"

    def set_light_level(self, output_light_level_vector: List[int]) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40201, params=output_light_level_vector, is_query=False)

    def set_duty_cycle(self, duty_cycle_vector: List[int]) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40217, params=duty_cycle_vector, is_query=False)

    def get_information_a(self, register_amount=54) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40201, params=[register_amount], is_query=True)

    def get_information_b(self, register_amount=8) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40255, params=[register_amount], is_query=True)

    def get_information_c(self, register_amount=3) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40163, params=[register_amount], is_query=True)

    def set_max_temp(self, max_temp: int) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40163, params=[max_temp], is_query=False)

    def set_rf_net_id(self, net_id: int) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40164, params=[net_id], is_query=False)

    def set_group_membership(self, group_membership: List[int]) -> bytes:
        group_membership_int = sum(group_membership)
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40165, params=[group_membership_int], is_query=False)

    def set_channel_max_current(self, max_i: List[int]) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address, opcode=40255, params=max_i, is_query=False)

    def parse_raw_data(self, gw_sn: str, raw_data: bytes) -> Optional[dict]:
        self.lamp_log.parse_raw_data(gw_sn, raw_data)
        if self.is_all_information_gathered():
            self.lamp_log.calc_all_information(self.group, self.timestamp)
            self.timestamp = datetime.now()
            logging.warning(self.lamp_log)
            return self.lamp_log.dict()
        return None

    def is_all_information_gathered(self) -> bool:
        if self.lamp_log.temp_mid and self.group and self.lamp_log.voltage and self.lamp_log.max_current:
            return True
        return False

    def has_group_membership(self) -> bool:
        if self.lamp_log.group_membership:
            return True
        return False

    def is_group_missing(self) -> bool:
        """Checks if the read group is not equal to the wanted one"""
        if not self.has_group_membership():
            return False
        if self.lamp_log.group_membership != self.group_membership:
            return True
        return False

    def has_max_i(self) -> bool:
        if self.lamp_log.max_current:
            return True
        return False

    def set_group(self, group: Group) -> None:
        self.group = group
