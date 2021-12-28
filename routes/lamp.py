import logging
import struct
from datetime import datetime
from enum import IntFlag
from typing import Optional, List, Any

from fastapi import HTTPException
from fastapi_utils.api_model import APIMessage, APIModel
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy import Column, Integer, DateTime, Float
from sqlalchemy import String, ARRAY
from sqlalchemy.sql import func
from starlette.status import HTTP_404_NOT_FOUND

from devices.group import Group
from devices.mixer_table import MixerTable
from utils.db import Base, ItemID


class LampLogORM(Base):
    __tablename__ = "lamps_data"

    id = Column(Integer, primary_key=True, index=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    gw_sn = Column(String)
    address = Column(Integer)
    light_tx = Column(ARRAY(Integer))
    light_rx = Column(ARRAY(Integer))
    blink_rw = Column(ARRAY(Integer))
    voltage = Column(ARRAY(Float))
    temperature = Column(ARRAY(Float))
    fail = Column(ARRAY(Integer))
    fail_description = Column(ARRAY(String))
    max_current = Column(ARRAY(Integer))
    temp_mid = Column(Integer)
    rf_net = Column(Integer)
    group_membership = Column(ARRAY(Integer))
    power_consumption = Column(Float)
    total_photon_flux = Column(Float)
    par = Column(Float)
    photon_efficiency = Column(Float)
    avg_ppfd = Column(Float)
    blue_ratio = Column(Float)
    green_ratio = Column(Float)
    red_ratio = Column(Float)
    far_red_ratio = Column(Float)
    red_blue_ratio = Column(Float)
    red_far_red_ratio = Column(Float)
    red_and_far_red_blue_ratio = Column(Float)
    desired_ppfd = Column(Float)
    calculated_ppfd = Column(Float)
    sensor_ppfd = Column(Float)
    accumulated_daily_light_integral = Column(Float)


class ChannelFailFlags(IntFlag):
    """defines the error type of light channel"""
    OK = 0
    VOLTAGE_TOO_HIGH = 1
    VOLTAGE_TOO_LOW = 2
    HIGH_TEMPERATURE = 4
    TEMPERATURE_ERROR = 8


class MainChannelFailFlags(IntFlag):
    """defines the error type of main light channel"""
    OK = 0
    VOLTAGE_TOO_HIGH = 1
    VOLTAGE_TOO_LOW = 2
    HIGH_TEMPERATURE = 4
    TEMPERATURE_ERROR = 8
    VCC_OUT_OF_RANGE = 16


class LampLogCreate(APIModel):
    """packs all the lamp log parameters - define by eyal amnor"""
    gw_sn: Optional[str]
    address: Optional[int]
    light_tx: Optional[List[int]]
    light_rx: Optional[List[int]]
    blink_rw: Optional[List[int]]
    voltage: Optional[List[float]]
    temperature: Optional[List[float]]
    fail: Optional[List[int]]
    fail_description: Optional[List[str]]
    max_current: Optional[List[int]]
    temp_mid: Optional[int]
    rf_net: Optional[int]
    group_membership: Optional[List[int]]

    power_consumption: Optional[float]
    total_photon_flux: Optional[float]
    par: Optional[float]
    photon_efficiency: Optional[float]
    avg_ppfd: Optional[float]
    blue_ratio: Optional[float]
    green_ratio: Optional[float]
    red_ratio: Optional[float]
    far_red_ratio: Optional[float]
    red_blue_ratio: Optional[float]
    red_far_red_ratio: Optional[float]
    red_and_far_red_blue_ratio: Optional[float]
    sensor_ppfd: Optional[float]
    desired_ppfd: Optional[float]
    calculated_ppfd: Optional[float]
    accumulated_daily_light_integral: float = 0.0

    @staticmethod
    def parse_fail_bits(channel_index: int, value: int) -> str:
        """translate the error into a string"""
        if channel_index == 8:
            fail_desc = MainChannelFailFlags(value)
        else:
            fail_desc = ChannelFailFlags(value)
        return str(fail_desc).split('.')[1]

    def parse_raw_data(self, gw_sn: str, raw_data: bytes) -> None:
        """
        light_tx - 8 ch - level of requested light intensity
        (0-1000, 0.2 steps)  Addresses - (40201 - 40208)\n
        light_rx - 8 ch - level of actual light intensity
        (0-1000, 0.2 steps)   Addresses - (40209 - 40216)\n
        volt - 8 ch, 48v, 3.3 - level of each ch in volts Addresses - (40226 - 40235)\n
        temp - 8 ch, 48v, 3.3 - level of each ch in celsius Addresses - (40236 - 40245)\n
        fails - 8 ch, main - flags representing the fails on each
        channel Addresses - (40246 - 40254)\n
        max_i - 8 ch - level of maximum current allowed on each
        channel in mA Addresses - (40255 - 40262)\n
        blink_rw - 8 ch, freq - level of duty cycle for each channel (0-90, 10 step),
        freq (0-2400) in hz, Addresses - (40217 - 40225)\n
        temp_mid - set the target temperature Addresses - (40163)\n
        rf_net - set the net idAddresses - (40164)\n
        group_membership - set the group that the lamp belongs to,
        in flags 16 bits.Addresses - (40165)\n
        """
        logging.debug(raw_data.hex(' ').upper())
        raw_data = raw_data[9:-3]  # gets rid of the wrapper and crc
        self.address, _, msg_len = struct.unpack_from('BBB', raw_data)
        self.gw_sn = gw_sn
        # print(address, op_code, msg_len, len(raw_data[3:]), raw_data[3:]. hex(' ').upper())
        if msg_len == 0x6C:  # from 40201-40254
            registers: List[Any] = list(struct.unpack_from(f'>{msg_len // 2}H', raw_data, 3))
            self.light_tx = registers[:8]
            self.light_rx = registers[8:16]
            self.blink_rw = registers[16:25]
            self.voltage = [round(val * 0.1, 2) for val in registers[25:35]]
            self.temperature = registers[35:45]
            self.fail = registers[45:]
            self.fail_description = [self.parse_fail_bits(i, f) for i, f in enumerate(self.fail)]
            logging.info(f'Lamp {self.address}, LightTx {self.light_tx}, LightRx {self.light_rx}, BlinkRw {self.blink_rw},'
                         f'Voltage {self.voltage}, Temperature {self.temperature}, Fails {self.fail}')
        elif msg_len == 0x10:  # from 40255-40262
            registers: List[Any] = list(struct.unpack_from(f'>{msg_len // 2}H', raw_data, 3))
            self.max_current = registers
            logging.info(f'Lamp {self.address}, Max Current {self.max_current}')
        elif msg_len == 0x06:  # from 40163-40165
            registers: List[Any] = list(struct.unpack_from(f'>{msg_len // 2}H', raw_data, 3))
            self.temp_mid, self.rf_net, int_group_membership = registers
            self.group_membership = []
            for i in range(17):
                if int_group_membership & 1:
                    self.group_membership.append(i + 1)
                int_group_membership >>= 1
            logging.info(f'Lamp {self.address}, Temp Mid {self.temp_mid}, Rf Net {self.rf_net}, Group membership: {self.group_membership}')
        else:
            logging.warning(raw_data.hex(' ').upper())

    @staticmethod
    def round_3_digit(value) -> float:
        return round(value, 4)

    def calc_all_information(self, group: Optional[Group], timestamp: datetime) -> None:
        """calculates all the mixer table parameters"""
        if not group:
            return
        mixing_table: MixerTable = group.mixing_table
        table_vals = mixing_table.get_mixer_table_calc(self.light_rx, self.blink_rw, self.voltage, self.max_current)
        self.power_consumption = float(table_vals.FixturePowerConsumption)
        self.total_photon_flux = float(table_vals.TotalFixturePhotonFluxOutput)
        self.par = float(table_vals.FixturePAROutput)
        self.photon_efficiency = float(table_vals.FixturePhotonEfficacy)
        self.avg_ppfd = float(table_vals.AvgPPFDFromOneMeter)
        self.blue_ratio = float(table_vals.BlueToPar)
        self.green_ratio = float(table_vals.GreenToPar)
        self.red_ratio = float(table_vals.RedToPar)
        self.far_red_ratio = float(table_vals.FarRedToPar)
        self.red_blue_ratio = float(table_vals.RedToBlue)
        self.red_far_red_ratio = float(table_vals.RedToFarRed)
        self.red_and_far_red_blue_ratio = float(table_vals.RedAndFarRedToBlue)
        if group.sensor:
            self.sensor_ppfd = group.sensor.ppfd
        self.calculated_ppfd = group.calculated_ppfd
        self.desired_ppfd = group.schedule.get_current_event().moles_desired
        self.accumulated_daily_light_integral = self.calc_daily_dli(timestamp)

    def calc_daily_dli(self, timestamp: datetime) -> float:
        """ this sums all the daily light consumption"""
        if not self.par:
            return self.accumulated_daily_light_integral
        # if a day is passed - set to zero
        if timestamp.date() != datetime.now().date():
            return 0.0
        # else calc how much was the ppf and translate it into hours and add it
        hours_elapsed = (datetime.now() - timestamp).total_seconds()
        dli = hours_elapsed / 3600 * self.par
        return self.accumulated_daily_light_integral + dli


class LampInDB(LampLogCreate):
    """a blower database structure"""
    id: ItemID
    time_created: datetime


router = InferringRouter(tags=["Lamp"], include_in_schema=False)


@cbv(router)
class Lamp:

    def __init__(self, session):
        self.session = session

    async def get_owned_item(self, item_id: ItemID) -> LampLogORM:
        item: Optional[LampLogORM] = await self.session.get(LampLogORM, item_id)
        if item is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        return item

    @router.post("/lamp")
    async def create_item(self, item: LampLogCreate) -> LampInDB:
        item_orm = LampLogORM(**item.dict())
        self.session.add(item_orm)
        await self.session.flush()
        return await self.get_owned_item(item_orm.id)

    @router.get("/lamp/{item_id}")
    async def read_item(self, item_id: ItemID) -> LampInDB:
        item_orm = await self.get_owned_item(item_id)
        return LampInDB.from_orm(item_orm)

    @router.delete("/lamp/{item_id}")
    async def delete_item(self, item_id: ItemID) -> APIMessage:
        item = await self.get_owned_item(item_id)
        self.session.delete(item)
        await self.session.flush()
        return APIMessage(detail=f"Deleted item {item_id}")
