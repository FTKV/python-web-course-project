"""
Module of images' CRUD
"""

from enum import Enum
import pickle
from typing import List

from fastapi import HTTPException, UploadFile, status
from redis.asyncio.client import Redis
from sqlalchemy import select, UUID, and_
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.models import User, Image
import src.repository.tags as repository_tags
from src.schemas.images import (
    ImageModel,
    ImageUrlModel,
    ImageDescriptionModel,
    CloudinaryTransformations,
    MAX_NUMBER_OF_TAGS_PER_IMAGE,
)
from src.services.cloudinary import cloudinary_service


async def set_image_in_cache(image: Image, cache: Redis) -> None:
    """
    Sets an image in cache.

    :param image: The image to set in cache.
    :type image: Image
    :param cache: The Redis client.
    :type cache: Redis
    :return: None.
    :rtype: None
    """
    await cache.set(f"image: {image.id}", pickle.dumps(image))
    await cache.expire(f"image: {image.id}", settings.redis_expire)


async def create_image(
    file: UploadFile, body: ImageModel, user: User, session: AsyncSession, cache: Redis
) -> Image:
    """
    Creates a new image.

    :param body: The body for the image to create.
    :type body: ImageModel
    :param file: The uploaded file to create from.
    :type file: UploadFile
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The newly created image.
    :rtype: Image
    """
    result = await cloudinary_service.upload_image(
        file.file, user.username, file.filename
    )
    image_url = await cloudinary_service.get_image_url(result)
    image = Image(description=body.description, url=image_url, user_id=user.id)
    if body.tags:
        tags = []
        for tag_title in body.tags:
            tag = await repository_tags.read_tag(tag_title, session)
            if not tag:
                tag = await repository_tags.create_tag(tag_title, user, session)
            tags.append(tag)
        image.tags = tags
    session.add(image)
    await session.commit()
    await session.refresh(image)
    await set_image_in_cache(image, cache)
    return image


async def read_images(user_id, session: AsyncSession) -> list | None:
    """
    Gets an image with the specified id.

    :param image_id: The ID of the image to get.
    :type image_id: UUID
    :param session: The database session.
    :type session: AsyncSession
    :return: The image with the specified ID, or None if it does not exist.
    :rtype: Image | None
    """
    stmt = select(Image).filter(user_id == user_id)
    images = await session.execute(stmt)
    return images.scalars()


async def read_image(image_id: UUID | int, session: AsyncSession) -> Image | None:
    """
    Gets an image with the specified id.

    :param image_id: The ID of the image to get.
    :type image_id: UUID
    :param session: The database session.
    :type session: AsyncSession
    :return: The image with the specified ID, or None if it does not exist.
    :rtype: Image | None
    """
    stmt = select(Image).filter(Image.id == image_id)
    image = await session.execute(stmt)
    return image.scalar()


async def update_image(
    image_id: UUID,
    body: ImageUrlModel,
    user_id: UUID,
    session: AsyncSession,
    transformations: Enum,
) -> Image | None:
    """
    Updates existing image

    :param image_id: UUID | int: Find the image to update
    :param body: ImageModel: Get the fields from the request body
    :param user: User: Check if the user is allowed to update the image
    :param session: AsyncSession: Pass the current session to the function
    :param transformations: Enum: Image file transformation parameters.
    :return: An image  or None
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        if transformations:
            for i in CloudinaryTransformations:
                if i.value in transformations:
                    url = await cloudinary_service.image_transformations(
                        image.url,
                        i.value,
                    )
        else:
            url = body.url
        image.url = url
        await session.commit()
    return image


async def patch_image(
    image_id: UUID, body: ImageDescriptionModel, user_id: UUID, session: AsyncSession
) -> Image | None:
    """
    Updates existing image

    :param image_id: UUID | int: Find the image to update
    :param body: ImageModel: Get the fields from the request body
    :param user: User: Check if the user is allowed to update the image
    :param session: AsyncSession: Pass the current session to the function
    :return: An image  or None
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        image.description = body.description
        await session.commit()
    return image


async def delete_image(
    image_id: UUID | int, user_id: UUID, session: AsyncSession
) -> Image | None:
    """
    Deletes an image from the database.

    :param image_id: UUID | int: Specify the id of the image to delete
    :param user: User: Check if the user is authorized to delete the image
    :param session: AsyncSession: Pass the session to the function
    :return: The Image object that was deleted
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        public_id = await cloudinary_service.get_public_id_from_url(image.url)
        await cloudinary_service.delete_image(public_id)
        await session.delete(image)
        await session.commit()
    return image


async def add_tag_to_image(
    image_id: UUID | int,
    tag_title: str,
    user_id: UUID | int,
    user: User,
    session: AsyncSession,
    cache: Redis,
) -> Image | None:
    tag = await repository_tags.read_tag(tag_title, session)
    if not tag:
        tag = await repository_tags.create_tag(tag_title, user, session)
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        if len(image.tags) == MAX_NUMBER_OF_TAGS_PER_IMAGE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can't exceeded the maximum number ({MAX_NUMBER_OF_TAGS_PER_IMAGE}) of tags per image",
            )
        if tag not in image.tags:
            image.tags.append(tag)
            await session.commit()
            await set_image_in_cache(image, cache)
    return image


async def delete_tag_from_image(
    image_id: UUID | int,
    tag_title: str,
    user_id: UUID | int,
    user: User,
    session: AsyncSession,
    cache: Redis,
) -> Image | None:
    tag = await repository_tags.read_tag(tag_title, session)
    if not tag:
        tag = await repository_tags.create_tag(tag_title, user, session)
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        if image.tags and tag in image.tags:
            image.tags.remove(tag)
            await session.commit()
            await set_image_in_cache(image, cache)
    return image
