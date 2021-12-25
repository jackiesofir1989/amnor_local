from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from fastapi_utils.api_model import APIMessage, APIModel
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy import Column, Integer, DateTime, Float, String
from sqlalchemy.sql import func
from starlette.status import HTTP_404_NOT_FOUND
from utils.db import Base, ItemID


class SensorORM(Base):
    __tablename__ = "sensors_data"

    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    gw_sn = Column(String)
    address = Column(Integer)
    ppfd = Column(Float)


class SensorCreate(APIModel):
    """a event structure"""
    gw_sn: str
    address: int
    ppfd: float


class SensorInDB(SensorCreate):
    """a event database structure"""
    id: ItemID
    time_created: datetime


router = InferringRouter(
    tags=["Sensor"], include_in_schema=False,

)


@cbv(router)
class Sensor:

    def __init__(self, session):
        self.session = session

    async def get_owned_item(self, item_id: ItemID) -> SensorORM:
        item: Optional[SensorORM] = await self.session.get(SensorORM, item_id)
        if item is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        return item

    @router.post("/sensor")
    async def create_item(self, item: SensorCreate) -> SensorInDB:
        item_orm = SensorORM(**item.dict())
        self.session.add(item_orm)
        await self.session.flush()
        return await self.get_owned_item(item_orm.id)

    @router.get("/sensor/{item_id}")
    async def read_item(self, item_id: ItemID) -> SensorInDB:
        item_orm = await self.get_owned_item(item_id)
        return SensorInDB.from_orm(item_orm)

    @router.delete("/sensor/{item_id}")
    async def delete_item(self, item_id: ItemID) -> APIMessage:
        item = await self.get_owned_item(item_id)
        self.session.delete(item)
        await self.session.flush()
        return APIMessage(detail=f"Deleted item {item_id}")
