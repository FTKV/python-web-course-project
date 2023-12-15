"""
Module of images' schemas
"""


from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, List

from fastapi import Form
from pydantic import (
    BaseModel,
    HttpUrl,
    UUID4,
    ConfigDict,
    conlist,
)
from src.schemas.tags import TagTitleType, TagResponse


MAX_NUMBER_OF_TAGS_PER_IMAGE = 5


class ImageModel(BaseModel):
    description: str | None
    tags: conlist(TagTitleType, max_length=MAX_NUMBER_OF_TAGS_PER_IMAGE) | None


@dataclass
class ImageCreateForm:
    description: Annotated[str | None, Form(...)] = None
    tags: Annotated[List[str | None], Form(...)] = None


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


class CloudinaryTransformations(str, Enum):
    crop = "c_thumb,g_face,h_200,w_200,z_1/f_auto/r_max/"
    resize = "ar_1.0,c_fill,h_250"
    rotate = "a_10/"
    improve = "e_improve:outdoor:29/"
    brightness = "e_brightness:80/"
    blackwhite = "e_blackwhite:49/"
    saturation = "e_saturation:50/"
    border = "bo_5px_solid_lightblue/"
    rounded_corners = "r_100/"
