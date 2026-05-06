from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class OBDRecord(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    command: str = Field(..., description="OBD command name, e.g. RPM")
    value: Any = Field(..., description="Sensor reading value")
    unit: str | None = Field(default=None, description="Unit of the value if available")


class OBDSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    records: list[OBDRecord]
