from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import HTTPException
from fastapi_utils.api_model import APIMessage, APIModel
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from pydantic import Field
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.sql import func
from starlette.status import HTTP_404_NOT_FOUND

from utils.db import Base, ItemID


class AlertLevel(Enum):
    """defines the levels of the alerts"""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'


class AlertEventORM(Base):
    __tablename__ = "alert_event"

    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    owner = Column(String)
    log_level = Column(String)
    description = Column(String)


class AlertEventCreate(APIModel):
    """a event structure"""
    owner: str = Field(..., example='Lamp - 1')
    log_level: str = Field(..., example='INFO')
    description: str = Field(..., example='Sent LL Vector')

    def __str__(self):
        return f'{self.owner}, {self.description}'


class AlertEventInDB(AlertEventCreate):
    """a event database structure"""
    id: ItemID
    time_created: datetime


router = InferringRouter(
    tags=["Events"],
    include_in_schema=False
)


@cbv(router)
class AlertEvent:

    def __init__(self, session):
        self.session = session

    async def get_owned_item(self, item_id: ItemID) -> AlertEventORM:
        item: Optional[AlertEventORM] = await self.session.get(AlertEventORM, item_id)
        if item is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        return item

    @router.post("/events")
    async def create_item(self, item: AlertEventCreate) -> AlertEventInDB:
        item_orm = AlertEventORM(**item.dict())
        self.session.add(item_orm)
        await self.session.flush()
        # a = AlertEventInDB.from_orm(item_orm)
        return await self.get_owned_item(item_orm.id)

    @router.get("/events/{item_id}")
    async def read_item(self, item_id: ItemID) -> AlertEventInDB:
        item_orm = await self.get_owned_item(item_id)
        return AlertEventInDB.from_orm(item_orm)

    @router.delete("/events/{item_id}")
    async def delete_item(self, item_id: ItemID) -> APIMessage:
        item = await self.get_owned_item(item_id)
        self.session.delete(item)
        await self.session.flush()
        return APIMessage(detail=f"Deleted item {item_id}")
