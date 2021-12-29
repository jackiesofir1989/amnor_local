import logging
from typing import List

from devices.sensor import Sensor
from devices.system import sys
from utils.message import Command, GWTypes

"""
    Priority Levels - Lower Value higher Priority:
        0. Client Frontend requests.
        1. Set Light Level
        1. Set Blowers state
        2. Query Sensor
        3. Read Information
"""


def add_to_gw_queue(serial_number: str, description: GWTypes, data: List[int]):
    """This will handle client request to set values asap"""
    gw = sys.get_gw(serial_number)
    if not gw:
        return f'Gateway {serial_number} dose not exist'
    cmd = Command(priority=0, owner=str(gw), description=description.name, data_bytes=bytes(data))
    if cmd:
        gw.add_to_queue(cmd)
    return cmd


def set_group_settings():
    for gw in sys.get_all_gateways():
        for group in gw.groups:
            gw.set_mixer_table_to_lamps_by_group(group)
            commands = [
                ('Set Blink Vector', group.set_max_current()),
                ('Set Max Current Vector', group.set_max_current()),
                ('Set Blink Vector', group.set_duty_cycle())
            ]
            for description, data_bytes in commands:
                gw.add_to_queue(Command(priority=0, owner=str(group), description=description, data_bytes=data_bytes))


def add_a_lamp_group_membership():
    """This will scan all lamps to check if they are configured to the wanted group"""
    for gw in sys.get_all_gateways():
        for lamp in gw.lamps:
            if lamp.is_group_missing():
                gw.add_to_queue(Command(priority=1, owner=str(lamp), description='Set Group Membership',
                                        data_bytes=lamp.set_group_membership(lamp.group_membership)))


def add_a_lamp_query_to_queue():
    """This will add to all gateways outgoing queue a running lamp query."""
    for gw in sys.get_all_gateways():
        lamp = gw.get_next_lamp()
        if not lamp:
            continue
        commands = [
            ('Get Main Parameters', lamp.get_information_a())
        ]
        if not lamp.has_max_i():
            commands.append(('Get Max Current', lamp.get_information_b()))
        if not lamp.has_group_membership():
            commands.append(('Get RF, Group and Temp Params', lamp.get_information_c()))
        for description, data_bytes in commands:
            gw.add_to_queue(Command(priority=3, owner=str(lamp), description=description, data_bytes=data_bytes))


def add_a_lamp_non_important_query_to_queue():
    """This will add to all gateways outgoing queue a running lamp query."""
    for gw in sys.get_all_gateways():
        lamp = gw.get_next_lamp_non_important_read()
        commands = []
        if lamp.has_max_i():
            commands.append(('Get Max Current', lamp.get_information_b()))
        if lamp.has_group_membership():
            commands.append(('Get RF, Group and Temp Params', lamp.get_information_c()))
        for description, data_bytes in commands:
            gw.add_to_queue(Command(priority=3, owner=str(lamp), description=description, data_bytes=data_bytes))


def add_a_sensor_query_to_queue():
    """
    This will add to all gateways outgoing queue a sensor read,
    if there is no sensor it will add current group light profile.
    """
    for gw in sys.get_all_gateways():
        for group in gw.groups:
            sensor = group.get_sensor()
            if sensor:
                gw.add_to_queue(Command(priority=1, owner=str(sensor), description='Get PPFD', data_bytes=sensor.request_light_level()))
            else:
                if not group.is_scheduler_enabled():
                    return
                event, output_light_vector, surface_micro_moles = group.get_current_output_vector()
                packet = group.set_light_level(output_light_vector)
                gw.add_to_queue(Command(priority=2, owner=str(group), description=f'{event}, Set Light Level {output_light_vector}',
                                        data_bytes=packet))


def set_light_level_from_sensor_callback(sensor: Sensor):
    """
    This will send a group light control vector based on sensor read
    """
    for gw in sys.get_all_gateways():
        for group in gw.groups:
            if group.is_sensor(sensor.address):
                if not group.is_scheduler_enabled():
                    return
                brightness = group.get_brightness_based_on_sensor()
                event, output_light_vector, surface_micro_moles = group.get_current_output_vector(brightness=brightness)
                logging.critical(f'\n{gw} - {group} - {event}\nCalculated\nOutput Light Level: {output_light_vector}, Brightness calculated: {brightness}, Moles calculated: {surface_micro_moles}')
                packet = group.set_light_level(output_light_vector)
                gw.add_to_queue(Command(priority=2, owner=str(group), description=f'{event}, Set Light Level {output_light_vector}',
                                        data_bytes=packet))


def set_a_blower_to_queue():
    """
    This will add to all gateways outgoing queue a blower set,
    based on start of day and end of day.
    """
    for gw in sys.get_all_gateways():
        for group in gw.groups:
            state = group.is_start_of_day()
            for blower in gw.blowers:
                if blower.is_on != state:
                    packet = blower.request_state()
                    gw.add_to_queue(Command(priority=1, owner=str(group), description=f'Read Blower State', data_bytes=packet))
                    packet = blower.set_state(state)
                    gw.add_to_queue(Command(priority=1, owner=str(group), description=f'Set Blower to {state}', data_bytes=packet))
