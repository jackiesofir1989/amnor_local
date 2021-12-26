import logging
from queue import PriorityQueue
from typing import List, Optional, Any, Tuple

from fastapi_utils.api_model import APIModel

from utils import modbus
from utils.message import Command, GWTypes
from .blower import Blower
from .group import Group
from .lamp import Lamp
from .sensor import Sensor


class Gateway(APIModel):

    serial_number: str
    hops: int
    net: int
    last_lamp_read_index: int = 0
    last_lamp_not_important_read_index: int = 0
    lamps: List[Lamp]
    blowers: List[Blower]
    groups: List[Group]
    queue: Optional[PriorityQueue]

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.queue = PriorityQueue()

    class Config:
        arbitrary_types_allowed = True

    def __str__(self):
        return f'Gateway {self.serial_number}'

    def set_net(self, net):
        from task_manager.worker import add_to_gw_queue
        self.net = net
        add_to_gw_queue(
            serial_number=self.serial_number,
            description=GWTypes.send_new_net,
            data=[net],
        )

    def set_hops(self, hops):
        from task_manager.worker import add_to_gw_queue
        self.hops = hops
        add_to_gw_queue(
            serial_number=self.serial_number,
            description=GWTypes.send_new_hops,
            data=[hops],
        )

    def set_call_address(self, call_address: List[int]):
        from task_manager.worker import add_to_gw_queue
        add_to_gw_queue(
            serial_number=self.serial_number,
            description=GWTypes.send_new_call_address,
            data=call_address,
        )

    def set_mixer_table_to_lamps_by_group(self, group: Group):
        """set the mixing table to the lamps assigned group"""
        for lamp in self.lamps:
            if group.address in lamp.group_membership:
                lamp.set_group(group)

    def find_device(self, raw_data):
        device_type, address = modbus.get_device_type_and_address(raw_data)
        device = None
        if device_type == 'Lamp':
            device = self.find_lamp(address)
        elif device_type == 'Sensor':
            device = self.find_sensor(address)
        elif device_type == 'Blower':
            device = self.find_blower(address)
        if not device:
            return False, None, None, None
        return True, device, device_type, address

    def find_lamp(self, address: int) -> Optional[Lamp]:
        for lamp in self.lamps:
            if lamp.address == address:
                return lamp
        # raise Exception(f'Lamp {address} was not found')
        return None

    def find_sensor(self, address: int) -> Optional[Sensor]:
        for gr in self.groups:
            sensor = gr.get_sensor()
            if sensor and sensor.address == address:
                return sensor
        return None

    def find_blower(self, address: int) -> Optional[Blower]:
        for blower in self.blowers:
            if blower.address == address:
                return blower
        return None

    def add_lamp(self, **kwargs):
        self.lamps.append(Lamp(**kwargs))

    def delete_lamp(self, address: int):
        self.lamps = [_l for _l in self.lamps if _l.address == address]

    def add_to_queue(self, command: Command):
        if self.queue.qsize() <= 50:
            item = (command.priority, command)
            self.queue.put(item)
            # print(f'{datetime.datetime.now()}, {command}')

    def pull_from_queue(self) -> Tuple[int, Optional[Command]]:
        return self.queue.get_nowait()

    def get_command(self) -> Optional[Command]:
        if self.queue.empty():
            return None
        priority, command = self.pull_from_queue()
        return command

    def get_next_lamp(self) -> Optional[Lamp]:
        if self.lamps and self.queue.qsize() == 0:
            if self.last_lamp_read_index == len(self.lamps):
                self.last_lamp_read_index = 0
            lamp = self.lamps[self.last_lamp_read_index]
            self.last_lamp_read_index += 1
            return lamp
        return None

    def get_next_lamp_non_important_read(self) -> Optional[Lamp]:
        if self.lamps:
            if self.last_lamp_not_important_read_index == len(self.lamps):
                self.last_lamp_not_important_read_index = 0
            lamp = self.lamps[self.last_lamp_not_important_read_index]
            self.last_lamp_not_important_read_index += 1
            return lamp
        return None
