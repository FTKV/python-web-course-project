"""
Module of users' schemas
"""


from datetime import datetime, date
import inspect
import json
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    SecretStr,
    HttpUrl,
    UUID4,
    ConfigDict,
    ValidationError,
)
from typing import Type, Annotated

from fastapi import Form
from fastapi.exceptions import RequestValidationError

from src.database.models import Role


def as_form(cls: Type[BaseModel]):
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():
        model_field: ModelField  # type: ignore
        if model_field.is_required:
            new_parameters.append(
                inspect.Parameter(
                    field_name,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(model_field.default),
                    annotation=model_field.annotation,
                )
            )
        else:
            new_parameters.append(
                inspect.Parameter(
                    field_name,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(None),
                    annotation=model_field.annotation,
                )
            )

    async def as_form_func(**data):
        try:
            return cls(**data)
        except ValidationError as e:
            raise RequestValidationError(e.errors())

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, "as_form", as_form_func)
    return cls


@as_form
class UserModel(BaseModel):
    username: str = Field(min_length=2, max_length=254)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=72)
    first_name: Annotated[str | None, Field(max_length=254)] = None
    last_name: Annotated[str | None, Field(max_length=254)] = None
    phone: Annotated[str | None, Field(max_length=38)] = None
    birthday: date | None = None

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


@as_form
class UserUpdateModel(BaseModel):
    first_name: Annotated[str | None, Field(max_length=254)] = None
    last_name: Annotated[str | None, Field(max_length=254)] = None
    phone: Annotated[str | None, Field(max_length=38)] = None
    birthday: date | None = None

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class UserRequestEmail(BaseModel):
    email: EmailStr


class UserPasswordSetModel(BaseModel):
    password: str = Field(min_length=8, max_length=72)


class UserSetRoleModel(BaseModel):
    role: Role


class UserDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    username: str = Field(min_length=2, max_length=254)
    email: EmailStr
    first_name: Annotated[str | None, Field(max_length=254)]
    last_name: Annotated[str | None, Field(max_length=254)]
    phone: Annotated[str | None, Field(max_length=38)]
    birthday: date | None
    created_at: datetime
    updated_at: datetime
    avatar: HttpUrl
    role: Role
    is_active: bool


class UserResponse(BaseModel):
    user: UserDb
    message: str = "User successfully created"
