
"""
A function that will check whether the address is valid or not.
And if the address was added previously, it will return the address id.
And make the first letters capital of the city, sub_city, and landmark.
"""

import re
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session, and_, select

from db import get_session
from models.Location import Address


SessionDep = Annotated[Session, Depends(get_session)]


def check_address(session: SessionDep, address: Address):
    try:

        split = re.split(r"[,\s]+", address.city)
        split = [item.capitalize() for item in split]
        address.city = " ".join(split)

        split = re.split(r"[,\s]+", address.sub_city)
        split = [item.capitalize() for item in split]
        address.sub_city = " ".join(split)

        split = re.split(r"[,\s]+", address.woreda)
        split = [item.capitalize() for item in split]
        address.woreda = " ".join(split)

        split = re.split(r"[,\s]+", address.landmark)
        split = [item.capitalize() for item in split]
        address.landmark = " ".join(split)

        address_db = session.exec(
            select(Address).where(
                and_(
                    Address.city == address.city,
                    Address.sub_city == address.sub_city,
                    Address.woreda == address.woreda,
                    Address.landmark == address.landmark,
                )
            )
        ).first()
        if address_db:
            return address_db
        address.id = None
        session.add(address)
        session.commit()
        session.refresh(address)
        return address
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
