"""
Module of images' schemas
"""


from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, HttpUrl, UUID4, ConfigDict


class ImageModel(BaseModel):
    description: str | None


@dataclass
class ImageCreateForm:
    description: Annotated[str | None, Form(...)] = None


class ImageDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    url: HttpUrl
    user_id: UUID4 | int
    description: str | None
    created_at: datetime
    updated_at: datetime
    rate: float | None


class ImageUrlModel(BaseModel):
    url: HttpUrl
