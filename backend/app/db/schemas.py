from pydantic import BaseModel, field_serializer
from datetime import datetime
from typing import Optional

# Pydantic models for API requests and responses

class LabTypeResponse(BaseModel):
    id: int
    name: str
    image: str
    port: int
    description: Optional[str]

    class Config:  # allows Pydantic to read data from SQLAlchemy model objects directly
        from_attributes = True

class LabSessionResponse(BaseModel):
    id: int
    lab_type_id: int
    pod_name: Optional[str]
    url: Optional[str]
    status: str
    start_time: Optional[datetime]
    expiration_time: Optional[datetime]

    @field_serializer("start_time", "expiration_time")
    def serialize_dt(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        # stored as naive UTC — append Z so the browser treats it as UTC
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    class Config:
        from_attributes = True