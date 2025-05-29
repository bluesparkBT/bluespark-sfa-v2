from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class ErrorLog(SQLModel, table=True):
    __tablename__ = "error_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default=datetime.now(), index=True)
    endpoint: str
    request_data: Optional[str] = None
    error_message: str
    stack_trace: Optional[str] = None