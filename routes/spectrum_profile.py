from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
from fastapi_utils.api_model import APIMessage, APIModel
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from pydantic import Field
from sqlalchemy import Column, Integer, DateTime, String, ARRAY
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from starlette.status import HTTP_404_NOT_FOUND

from utils.db import Base, ItemID


class SpectrumProfileORM(Base):
    __tablename__ = "spectrum_profiles"

    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String, unique=True)
    colors = Column(ARRAY(Integer))


class SpectrumProfileCreate(APIModel):
    """a spectrum profile structure base"""
    name: str = Field(..., example='Blue')
    colors: List[int] = Field(..., example=[100, 2, 4, 6, 1, 12, 3, 4])


class SpectrumProfileInDB(SpectrumProfileCreate):
    """a spectrum profile database structure"""
    id: ItemID
    time_created: datetime


router = InferringRouter(
    tags=["Spectrum Profile"],
    include_in_schema=False
)


@cbv(router)
class SpectrumProfile:

    def __init__(self, session):
        self.session = session

    async def get_owned_item(self, item_id: ItemID) -> SpectrumProfileORM:
        item: Optional[SpectrumProfileORM] = await self.session.get(SpectrumProfileORM, item_id)
        if item is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        return item

    @router.post("/spectrum_profile")
    async def create_item(self, item: SpectrumProfileCreate) -> SpectrumProfileInDB:
        item_orm = SpectrumProfileORM(**item.dict())
        self.session.add(item_orm)
        await self.session.flush()
        return await self.get_owned_item(item_orm.id)

    @router.get("/spectrum_profile/{item_id}")
    async def read_item(self, item_id: ItemID) -> SpectrumProfileInDB:
        item_orm = await self.get_owned_item(item_id)
        return SpectrumProfileInDB.from_orm(item_orm)

    @router.put("/spectrum_profile/{item_id}")
    async def update_item(self, item_id: ItemID, item: SpectrumProfileCreate) -> SpectrumProfileInDB:
        item_orm = await self.get_owned_item(item_id)
        item_orm.name = item.name
        self.session.add(item_orm)
        await self.session.flush()
        return SpectrumProfileInDB.from_orm(item_orm)

    @router.delete("/spectrum_profile/{item_id}")
    async def delete_item(self, item_id: ItemID) -> APIMessage:
        item = await self.get_owned_item(item_id)
        self.session.delete(item)
        await self.session.flush()
        return APIMessage(detail=f"Deleted item {item_id}")
