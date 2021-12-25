from enum import Enum
from typing import List, Optional, Any

from pydantic import BaseModel
from pydantic.fields import Field


class Command(BaseModel):
    priority: int
    data_bytes: bytes
    data: Optional[List[int]]
    owner: str
    description: str

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.data = list(self.data_bytes)

    class Config:
        arbitrary_types_allowed = True

    def __lt__(self, other):
        return self.priority < other.priority

    def __str__(self):
        return f'{self.priority}, {self.owner}, {self.description}'  # , {self.data_bytes.hex(" ").upper()}'


class GWTypes(str, Enum):
    send_new_net = 'Send Net'
    send_new_hops = 'Send Hops'
    send_new_call_address = 'Send Call Address'


class RawData(BaseModel):
    data: List[int] = Field(..., example=[1, 2, 3, 4, 5])


