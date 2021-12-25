from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from fastapi_utils.api_model import APIMessage, APIModel
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.sql import func
from starlette.status import HTTP_404_NOT_FOUND

from utils.db import Base, ItemID


class BlowerORM(Base):
    __tablename__ = "blowers_data"

    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    gw_sn = Column(String)
    address = Column(Integer)
    is_on = Column(Integer)


class BlowerCreate(APIModel):
    """a blower structure"""
    gw_sn: str
    address: int
    is_on: int


class BlowerInDB(BlowerCreate):
    """a blower database structure"""
    id: ItemID
    time_created: datetime


router = InferringRouter(
    tags=["Blower"], include_in_schema=False
)


@cbv(router)
class Blower:

    def __init__(self, session):
        self.session = session

    async def get_owned_item(self, item_id: ItemID) -> BlowerORM:
        item: Optional[BlowerORM] = await self.session.get(BlowerORM, item_id)
        if item is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        return item

    @router.post("/blower")
    async def create_item(self, item: BlowerCreate) -> BlowerInDB:
        item_orm = BlowerORM(**item.dict())
        self.session.add(item_orm)
        await self.session.flush()
        return BlowerInDB.from_orm(item_orm)

    @router.get("/blower/{item_id}")
    async def read_item(self, item_id: ItemID) -> BlowerInDB:
        item_orm = await self.get_owned_item(item_id)
        return BlowerInDB.from_orm(item_orm)

    @router.delete("/blower/{item_id}")
    async def delete_item(self, item_id: ItemID) -> APIMessage:
        item = await self.get_owned_item(item_id)
        self.session.delete(item)
        await self.session.flush()
        return APIMessage(detail=f"Deleted item {item_id}")
