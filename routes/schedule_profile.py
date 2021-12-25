from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
from fastapi_utils.api_model import APIMessage, APIModel
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from pydantic import Field
from sqlalchemy import Column, Integer, DateTime, String, ARRAY, Time
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from starlette.status import HTTP_404_NOT_FOUND

from utils.db import Base, ItemID


class EventsProfileORM(Base):
    __tablename__ = "event_profiles"

    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String)
    # colors: List[int]
    brightness = Column(Integer)
    moles_desired = Column(Integer)
    start_time = Column(Time)


class ScheduleProfileORM(Base):
    __tablename__ = "schedule_profiles"

    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String)
    events = Column(ARRAY(Integer))


class ScheduleProfileCreate(APIModel):
    """a Schedule profile structure"""
    name: str = Field(..., example='Winter 2021')
    events: List[int] = Field(..., example=[1, 2, 3, 5])  # list of id of the events


class ScheduleProfileInDB(ScheduleProfileCreate):
    """a Schedule profile database structure"""
    id: ItemID
    time_created: datetime


router = InferringRouter(
    tags=["Schedule Profile"],
    include_in_schema=False
    )


@cbv(router)
class ScheduleProfile:

    def __init__(self, session):
        self.session = session

    async def get_owned_item(self, item_id: ItemID) -> ScheduleProfileORM:
        item: Optional[ScheduleProfileORM] = await self.session.get(ScheduleProfileORM, item_id)
        if item is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        return item

    @router.post("/schedule_profile")
    async def create_item(self, item: ScheduleProfileCreate) -> ScheduleProfileInDB:
        item_orm = ScheduleProfileORM(**item.dict())
        self.session.add(item_orm)
        await self.session.flush()
        return await self.get_owned_item(item_orm.id)

    @router.get("/schedule_profile/{item_id}")
    async def read_item(self, item_id: ItemID) -> ScheduleProfileInDB:
        item_orm = await self.get_owned_item(item_id)
        return ScheduleProfileInDB.from_orm(item_orm)

    @router.put("/schedule_profile/{item_id}")
    async def update_item(self, item_id: ItemID, item: ScheduleProfileCreate) -> ScheduleProfileInDB:
        item_orm = await self.get_owned_item(item_id)
        item_orm.name = item.name
        self.session.add(item_orm)
        await self.session.flush()
        return ScheduleProfileInDB.from_orm(item_orm)

    @router.delete("/schedule_profile/{item_id}")
    async def delete_item(self, item_id: ItemID) -> APIMessage:
        item = await self.get_owned_item(item_id)
        self.session.delete(item)
        await self.session.commit()
        return APIMessage(detail=f"Deleted item {item_id}")
