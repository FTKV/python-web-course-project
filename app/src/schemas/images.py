"""
Module of images' schemas
"""


from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import Form, Query
from pydantic import (
    BaseModel,
    HttpUrl,
    UUID4,
    ConfigDict,
    Field,
    conlist,
    StringConstraints,
    constr,
)

# from pydantic.dataclasses import dataclass

from src.schemas.tags import TagResponse


class ImageModel(BaseModel):
    description: str | None
    tags: conlist(
        Annotated[
            str,
            StringConstraints(
                min_length=2,
                max_length=49,
                strip_whitespace=True,
                pattern=r"^[a-zA-Z0-9_.-]+$",
            ),
        ],
        max_length=5,
    ) | None


@dataclass
class ImageCreateForm:
    description: Annotated[str | None, Form(...)] = None
    tags: Annotated[List[str] | None, Form(...)] = None


class ImageDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    url: HttpUrl
    user_id: UUID4 | int
    description: str | None
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse]


class ImageUrlModel(BaseModel):
    url: HttpUrl
