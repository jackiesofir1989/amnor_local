from datetime import datetime, time
from typing import List, Optional, Tuple, Any, Union

import yaml
from fastapi_utils.api_model import APIModel
from pydantic import validator

from utils import modbus
from .event import Event
from .mixer_table import MixerTable
from .schedule import Schedule
from .sensor import Sensor


class Group(APIModel):
    address: int
    start_of_day: time
    end_of_day: time
    temp_mid: int
    max_current: List[int]
    blink_vector: List[int]
    mixing_table: MixerTable
    schedule: Union[str, Schedule]
    sensor: Optional[Sensor]
    group_offset: int = 240
    calculated_ppfd: float = 0.0

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.schedule = self.load_schedule()

    def load_schedule(self) -> Schedule:
        import yaml
        from devices.event import Event
        ROOT_FOLDER = 'config/schedules_profiles.yaml'
        with open(ROOT_FOLDER) as _f:
            profile = yaml.load(_f, Loader=yaml.FullLoader)[self.schedule]
            events = [Event(*event) for event in profile]
            return Schedule(events=events)

    @classmethod
    @validator('max_current')
    def max_current_check(cls, max_current: List[int]):
        _min, _max = 0, 2000
        if len(max_current) != 8:
            raise ValueError('Max current list must be 8 values long')
        for v in max_current:
            if not _min <= v <= _max:
                raise ValueError(f'Current values must be in values {_min} to {_max}')
        return max_current

    @classmethod
    @validator('blink_vector')
    def blink_vector_check(cls, blink_vector: List[int]):
        _min, _max = 10, 100
        _min1, _max1 = 0, 2400
        if len(blink_vector) != 9:
            raise ValueError('Max current list must be 9 values long')
        for v in blink_vector[:-1]:
            if not _min <= v <= _max:
                raise ValueError(f'Blink values must be in values {_min} to {_max}')
        if not _min1 <= blink_vector[8] <= _max1:
            raise ValueError(f'Frequency value must be in values {_min1} to {_max1}')
        return blink_vector

    @classmethod
    @validator('start_of_day', 'end_of_day', pre=True)
    def parse_time(cls, value):
        return datetime.strptime(value, '%H:%M:%S').time()

    def __str__(self):
        return f"Group {self.address}"

    def is_start_of_day(self) -> bool:
        current_time = datetime.now().time()
        if self.start_of_day <= current_time <= self.end_of_day:
            return True
        return False

    @staticmethod
    def get_schedule(**kwargs):
        with open('schedules_profiles.yaml') as f:
            dictionary = yaml.load(f, Loader=yaml.FullLoader)
        schedules = dictionary['schedules']
        for schedule in schedules:
            if schedule['name'] == kwargs.get('schedule_name'):
                return schedule
        raise Exception('Schedule must exist - could not found the existing name.')

    def get_sensor(self) -> Optional[Sensor]:
        if self.sensor:
            return self.sensor
        return None

    def is_sensor(self, sensor_address) -> bool:
        if self.sensor and self.sensor.address == sensor_address:
            return True
        return False

    def get_brightness_based_on_sensor(self) -> Optional[int]:
        if self.sensor:
            sensor_light_moles = self.sensor.ppfd
            event = self.schedule.get_current_event()
            brightness_calculated = self.mixing_table.get_brightness(event, sensor_light_moles)
            return brightness_calculated
        return None

    def test_brightness_based_on_sensor(self, light_moles_measured) -> int:
        event = self.schedule.get_current_event()
        brightness_calculated = self.mixing_table.get_brightness(event, light_moles_measured)
        return brightness_calculated

    def get_current_output_vector(self, brightness: int = None) -> Tuple[Event, List[int], float]:
        event = self.schedule.get_current_event()
        if brightness is None:
            brightness = event.brightness
        output_light_vector, self.calculated_ppfd = self.mixing_table.get_output_light_vector(event.colors, brightness)
        return event, output_light_vector, self.calculated_ppfd

    def set_light_level(self, output_light_level_vector: List[int]) -> bytes:
        return modbus.amnor_modbus_r_w_registers(
            address=self.address + self.group_offset, opcode=40201, params=output_light_level_vector, is_query=False)

    def set_duty_cycle(self) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address + self.group_offset, opcode=40217, params=self.blink_vector, is_query=False)

    def set_temp_mid(self) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address + self.group_offset, opcode=40263, params=[self.temp_mid], is_query=False)

    def set_max_current(self) -> bytes:
        return modbus.amnor_modbus_r_w_registers(address=self.address + self.group_offset, opcode=40255, params=self.max_current, is_query=False)
