"""
Module of rates' schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ConfigDict, validator


class RateModel(BaseModel):
    rate: int = Field(ge=1, le=5)


class RateResponse(RateModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4 | int
    image_id: UUID4 | int
    rate: int
    user_id: UUID4 | int
    created_at: datetime
    updated_at: datetime

class RateImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    avg_rate: float | None
    image_id: UUID4 | int
    
    @validator('avg_rate', pre=True, always=True)
    def round_avg_rate(cls, v):
        if v:     
            return round(v, 2)
        return None