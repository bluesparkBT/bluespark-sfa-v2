from pydantic import BaseModel
from typing import Optional


class AddressRead(BaseModel):
    id: int
    country: str
    city: str
    sub_city: str
    woreda: str
    landmark: Optional[str]

    class Config:
        orm_mode = True


class LocationRead(BaseModel):
    id: int
    name: Optional[str]
    latitude: float
    longitude: float
    address_rel: Optional[AddressRead]

    class Config:
        orm_mode = True
