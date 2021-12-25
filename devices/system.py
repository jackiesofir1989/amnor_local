import logging
from typing import List, Optional

import yaml
from fastapi_utils.api_model import APIModel

from config.config import settings
from .flower import Flower
from .gateway import Gateway
from .group import Group


class Flowers(APIModel):
    flowers: List[Flower]


class System:

    def __init__(self, path: str):
        self.path = path
        self.flowers = None
        self.load_system()

    def load_system(self):
        logging.info('Loading System.....')
        try:
            with open(self.path + '.yaml') as _f:
                self.flowers: List[Flower] = Flowers(**yaml.load(_f, Loader=yaml.FullLoader)).flowers
        except yaml.YAMLError as exc:
            logging.error(exc)

    def get_all_gateways(self) -> List[Gateway]:
        gateways = []
        for fl in self.flowers:
            for gw in fl.gateways:
                gateways.append(gw)
        return gateways

    def get_gws_serial_numbers(self) -> List[str]:
        return [gw.serial_number for gw in self.get_all_gateways()]

    def get_all_groups(self) -> List[Group]:
        groups = []
        for gw in self.get_all_gateways():
            for gr in gw.groups:
                groups.append(gr)
        return groups

    def get_gw(self, serial_number: str) -> Optional[Gateway]:
        for gw in self.get_all_gateways():
            if gw.serial_number == serial_number:
                return gw
        return None


sys = System(path=settings.system_path)
