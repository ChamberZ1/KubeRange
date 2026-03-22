from pydantic import BaseModel
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

    class Config:
        from_attributes = True