import logging
from typing import Optional, List

from fastapi import Body, HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from starlette import status

from devices.gateway import Gateway
from devices.system import sys
from routes.alert_event import AlertEvent, AlertEventCreate
from routes.blower import Blower, BlowerCreate
from routes.lamp import Lamp, LampLogCreate
from routes.sensor import Sensor, SensorCreate
from task_manager import worker
from utils import modbus
from utils.db import async_session
from utils.message import RawData, Command

router = InferringRouter(tags=["Transport"])


@cbv(router)
class Transport:
    """
    0-229 lamps single address,
    230-234 sensors
    235-239 blowers
    240-254 lamps group
    255 all
    """

    @router.post("/transport/response/{serial_number}", include_in_schema=False)
    async def response(self, *, serial_number: str, response_model: RawData):
        gw = sys.get_gw(serial_number)
        if not gw:
            await self.submit_a_log(f'Gateway {serial_number}', 'ERROR', f"Dose not exist in the database")
            return {'msg': f'Gateway {serial_number} Dose not exist in the database'}
        if not response_model.data:
            pass
        else:
            raw_data = bytearray(response_model.data)
            await self.handle_device(gw, raw_data)
        command: Optional[Command] = gw.get_command()
        if command:
            await self.submit_a_log(str(gw), 'INFO', command)
            c_d = command.dict()
            c_d.pop('data_bytes')
            return c_d
        else:
            return {'msg': 'No data to return'}

    @router.post("/transport/set_gw_net/")
    async def set_gw_net(self, serial_number: str, net_id: int):
        """Set the channel of the gateway to transmit, lamp should be in the same channel if they need to listen."""
        # for what ever reason value 0 doesn't work
        if not 1 < net_id < 256:
            raise ValueError('Values must be [0-255]')
        gw = self.check_valid_gw(serial_number)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set GW Net to {net_id}', data_bytes=bytes(net_id)))

    @router.post("/transport/set_gw_hops/")
    async def set_gw_hops(self, serial_number: str, hops: int):
        """Set the gateway network retransmission rate. 
        Lower number, the faster the network is going to respond, but the smaller area of communication."""

        if not 1 <= hops <= 32:
            raise ValueError('Values must be [1-32]')
        gw = self.check_valid_gw(serial_number)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set GW Hops to {hops}', data_bytes=bytes(hops)))

    @router.post("/transport/set_light_level_to_lamp/")
    async def set_light_level_to_lamp(self, serial_number: str, lamp_address: int,
                                      light_level_array: List[int] = Body(..., example=[0, 0, 0, 0, 0, 0, 0, 0])):
        """Set the light level of channel in a lamp each value is from 0 to 1000"""
        gw = self.check_valid_gw(serial_number)
        byte_array = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40201, params=light_level_array, is_query=False)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set lamp {lamp_address} to {light_level_array}',
                                data_bytes=byte_array))

    @router.post("/transport/set_duty_cycle_to_lamp/")
    async def set_duty_cycle_to_lamp(self, serial_number: str, lamp_address: int,
                                     duty_cycle_array: List[int] = Body(..., example=[0, 0, 0, 0, 0, 0, 0, 0, 0])):
        """Set the blink rate of a channel in lamp each value is from 10 to 100(Steps of 10) and the last value is frequency of blinking"""
        gw = self.check_valid_gw(serial_number)
        byte_array = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40217, params=duty_cycle_array, is_query=False)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set lamp {lamp_address} to duty cycle {duty_cycle_array}',
                                data_bytes=byte_array))

    @router.post("/transport/set_max_current_to_lamp/")
    async def set_max_current_to_lamp(self, serial_number: str, lamp_address: int,
                                      max_current_array: List[int] = Body(..., example=[0, 0, 0, 0, 0, 0, 0, 0])):
        """Set the max current of a channel in lamp each value is from 0 to 1400 in milli-amps"""
        gw = self.check_valid_gw(serial_number)
        byte_array = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40255, params=max_current_array, is_query=False)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set lamp {lamp_address} to max current {max_current_array}',
                                data_bytes=byte_array))

    @router.post("/transport/change_address_to_sensor/")
    async def change_address_to_sensor(self, serial_number: str, from_address: int, to: int):
        """Set new address the sensor"""
        gw = self.check_valid_gw(serial_number)
        byte_array = modbus.modbus_write_request(address=from_address, start_data_address=48, values=[to])
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set Sensor {from_address} to {to}',
                                data_bytes=byte_array))

    @router.post("/transport/set_rf_net_id_to_lamp/")
    async def set_rf_net_id_to_lamp(self, serial_number: str, lamp_address: int, net_id: int):
        """Set the lamp channel"""
        gw = self.check_valid_gw(serial_number)
        byte_array = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40164, params=[net_id], is_query=False)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set lamp {lamp_address} to net id {net_id}',
                                data_bytes=byte_array))
        
    @router.post("/transport/read_status_from_lamp/")
    async def read_status_from_lamp(self, serial_number: str, lamp_address: int):
        """Reads all parameters from a requested lamp"""
        gw = self.check_valid_gw(serial_number)
        a = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40201, params=[54], is_query=True)
        b = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40255, params=[8], is_query=True)
        c = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40163, params=[3], is_query=True)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Read lamp {lamp_address} status part a', data_bytes=a))
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Read lamp {lamp_address} status part b', data_bytes=b))
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Read lamp {lamp_address} status part c', data_bytes=c))

    @router.post("/transport/set_max_temp_to_lamp/")
    async def set_max_temp_to_lamp(self, serial_number: str, lamp_address: int, max_temp: int):
        """Set the lamp max temp,
        This temperature the lamp will try to stay around,
        Higher than the specified temperature the lamp will lower the power output."""
        gw = self.check_valid_gw(serial_number)
        byte_array = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40163, params=[max_temp], is_query=False)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set lamp {lamp_address} to max temp {max_temp}',
                                data_bytes=byte_array))
        
    @router.post("/transport/set_group_membership_to_lamp/")
    async def set_group_membership_to_lamp(self, serial_number: str, lamp_address: int, 
                                           group_membership: List[int] = Body(..., example=[1, 2, 3])):
        """Set the lamp group membership,
        The groups should be specified in a list,
        e.g [1,2,3] for groups 1 2 3 in the lamp specified"""
        gw = self.check_valid_gw(serial_number)
        group_membership_int = sum(group_membership)
        byte_array = modbus.amnor_modbus_r_w_registers(address=lamp_address, opcode=40165, params=[group_membership_int], is_query=False)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set lamp {lamp_address} to groups {group_membership}',
                                data_bytes=byte_array))
        
    @router.post("/transport/read_sensor/")
    async def read_sensor(self, serial_number: str, address: int):
        """Checks for communication from the sensor"""
        gw = self.check_valid_gw(serial_number)
        byte_array = modbus.modbus_read_registers(address, 40, 1)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Read Sensor {address}',
                                data_bytes=byte_array))

    @router.post("/transport/set_gw_call_address/")
    async def set_gw_call_address(self, serial_number: str, call_address: str):
        """Set the URL that the gateway will call format is *.*.*.*:*"""

        ipv4, port = call_address.split(':')
        _ = [int(i) for i in ipv4.split('.')]
        int(port)
        gw = self.check_valid_gw(serial_number)
        gw.add_to_queue(Command(priority=0, owner=str(gw), description=f'Set GW Call address to {call_address}', 
                                data_bytes=bytes(call_address.encode('utf-8'))))

    async def handle_device(self, gw, raw_data):
        device_found, device, device_type, address = gw.find_device(raw_data)
        if not device_found:
            return self.submit_a_log(str(gw), 'ERROR', f'{device_type} {address} dose not exist')
        device_data = device.parse_raw_data(gw.serial_number, raw_data)
        async with async_session() as session:
            async with session.begin():
                if device_type == 'Lamp' and device_data:
                    item = LampLogCreate(**device_data)
                    await Lamp(session).create_item(item=item)
                    return item
                if device_type == 'Sensor' and device_data:
                    item = SensorCreate(**device_data)
                    await Sensor(session).create_item(item=item)
                    worker.set_light_level_from_sensor_callback(device)
                    return item
                if device_type == 'Blower':
                    item = BlowerCreate(**device_data)
                    await Blower(session).create_item(item=item)
                    return item

    @staticmethod
    def check_valid_gw(serial_number: str) -> Gateway:
        gw = sys.get_gw(serial_number)
        if not gw:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Gateway {serial_number} dose not exist')
        return gw
    
    @staticmethod
    async def submit_a_log(owner: str, log_level: str, description):
        alert_event = AlertEventCreate(owner=owner, log_level=log_level, description=str(description))
        logging.warning(str(alert_event))
        async with async_session() as session:
            async with session.begin():
                item = await AlertEvent(session).create_item(item=alert_event)
                return item
