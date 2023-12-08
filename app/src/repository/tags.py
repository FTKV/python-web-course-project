"""
Module of tags' CRUD
"""


from sqlalchemy import select
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Tag, User
from src.schemas.tags import TagModel


async def read_tags(
    offset: int,
    limit: int,
    title: str,
    session: AsyncSession,
) -> ScalarResult:
    """
    Reads a list of tags with specified pagination parameters and search by title.

    :param offset: The number of tags to skip.
    :type offset: int
    :param limit: The maximum number of tags to return.
    :type limit: int
    :param title: The string to search by title.
    :type title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: A list of tags or None.
    :rtype: ScalarResult
    """
    stmt = select(Tag)
    if title:
        stmt = stmt.filter(Tag.title.like(f"%{title}%"))
    stmt = stmt.order_by(Tag.title).offset(offset).limit(limit)
    tags = await session.execute(stmt)
    return tags.scalars()


async def read_tag(title: str, session: AsyncSession) -> Tag | None:
    """
    Reads a single tag with the specified title.

    :param title: The title of the tag to retrieve
    :type title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: The tag with the specified title, or None if it does not exist.
    :rtype: Tag | None
    """
    stmt = select(Tag).filter(Tag.title == title.lower())
    tag = await session.execute(stmt)
    return tag.scalar()


async def create_tag(body: TagModel, user: User, session: AsyncSession) -> Tag | None:
    """
    Creates a new tag with the specified title.

    :param body: The request body with data for the tag to create.
    :type body: TagModel
    :param user: The user who creates the tag.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The newly created tag or None if creation failed.
    :rtype: Tag | None
    """
    tag = Tag(title=body.title.lower(), user_id=user.id)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


async def delete_tag(title: str, session: AsyncSession) -> Tag | None:
    """
    Deletes a single tag with the specified title.

    :param title: The title of the tag to delete
    :type title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: The deleted tag or None if it did not exist.
    :rtype: Tag | None
    """
    stmt = select(Tag).filter(Tag.title == title.lower())
    tag = await session.execute(stmt)
    tag = tag.scalar()
    if tag:
        await session.delete(tag)
        await session.commit()
    return tag
