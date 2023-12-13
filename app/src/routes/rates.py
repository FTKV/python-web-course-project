"""
Module of commentss' routes
"""

from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connect_db import get_session
from src.database.models import User, Role
from src.repository import rates as repository_rates
from src.schemas.rates import RateModel, RateResponse, RateImageResponse
from src.services.auth import auth_service
from src.services.roles import RoleAccess

allowed_operation_get = RoleAccess([Role.administrator, Role.moderator, Role.user])
allowed_operation_create = RoleAccess(
    [Role.administrator, Role.moderator, Role.user])
allowed_operation_update = RoleAccess(
    [Role.administrator, Role.moderator, Role.user])
allowed_operation_remove = RoleAccess([Role.administrator, Role.moderator])
allowed_operation_non_user = RoleAccess([Role.administrator, Role.moderator])

router = APIRouter(prefix="/rates", tags=["rates"])

@router.get(
    "/{image_id}",
    response_model=List[RateResponse],
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])
async def read_all_rates_to_photo(
    image_id: UUID4 | int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=1000), 
    session: AsyncSession = Depends(get_session),
):

    return await repository_rates.read_all_rates_to_photo(image_id, offset, limit, session)

@router.get(
    "/avg/{image_id}",
    response_model=RateImageResponse,
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])
async def read_avg_rate_to_photo(
    image_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
):

    return await repository_rates.read_avg_rate_to_photo(image_id, session)


@router.get(
    "/avg/all/",
    response_model=List[RateImageResponse],
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])

async def read_all_avg_rate(
    session: AsyncSession = Depends(get_session),
):

    return await repository_rates.read_all_avg_rate(session)

@router.post(
    "/{image_id}",
    response_model=RateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)])
async def create_rate_to_photo(
    image_id: UUID4 | int,
    body: RateModel,
    current_user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session)):

    rate = await repository_rates.create_rate_to_photo(image_id, body, current_user, session)
    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found or forbiden to rate twice or forbidden to rate your photo"
        )
    return rate

@router.delete(
    "/{rate_id}",
    response_model=RateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create),
                  Depends(auth_service.get_current_user)])
async def delete_rate_to_photo(
    rate_id: UUID4 | int,
    session: AsyncSession = Depends(get_session)):

    return await repository_rates.delete_rate_to_photo(rate_id, session)


