"""
Module of tags' routes
"""


from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connect_db import get_session
from src.database.models import User
from src.repository import tags as repository_tags
from src.schemas.tags import TagModel, TagResponse
from src.services.auth import auth_service


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=List[TagResponse])
async def read_tags(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=1000),
    title: str = Query(default=None),
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to tags route and reads a list of tags with specified pagination parameters and search by title.

    :param offset: The number of tags to skip (default = 0, min value = 0).
    :type offset: int
    :param limit: The maximum number of tags to return (default = 10, min value = 1, max value = 1000).
    :type limit: int
    :param title: The string to search by title.
    :type title: str
    :param user: The authenticated user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: A list of tags or None.
    :rtype: ScalarResult
    """
    return await repository_tags.read_tags(offset, limit, title, session)
