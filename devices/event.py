from datetime import datetime, time
from typing import List

import yaml
from pydantic import Field, validator
from pydantic.dataclasses import dataclass


@dataclass
class Event:
    name: str
    brightness: int
    moles_desired: int
    start_time: time
    colors: List[int] = Field(init=False, default_factory=list)

    def __post_init__(self):
        self.colors = self._get_colors()

    def _get_colors(self) -> List[int]:
        ROOT_FOLDER = 'config/spectrum_profiles.yaml'
        with open(ROOT_FOLDER) as _f:
            colors: List[int] = yaml.load(_f, Loader=yaml.FullLoader)[self.name]
            return colors

    @classmethod
    @validator('start_time', pre=True)
    def parse_time(cls, value):
        return datetime.strptime(value, '%H:%M:%S').time()

    def __str__(self):
        return f'Event {self.name}, Colors {self.colors}, Brightness {self.brightness} ,Moles Desired {self.moles_desired} ,' \
               f'Start time {self.start_time}'
