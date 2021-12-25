from typing import List

from fastapi_utils.api_model import APIModel

from .gateway import Gateway


class Flower(APIModel):
    address: int  # 9600 buadrate
    gateways: List[Gateway]

    def __str__(self):
        return f'Flower {self.address}'
