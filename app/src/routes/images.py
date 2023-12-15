"""
Module of images' routes
"""


from dataclasses import asdict
from typing import List

from pydantic import UUID4
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status, Query
from fastapi.responses import FileResponse
from redis.asyncio.client import Redis
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connect_db import get_session, get_redis_db1
from src.database.models import User, Role, Image
from src.repository import images as repository_images
from src.services.auth import auth_service
from src.services.roles import RoleAccess
from src.services.qr_code import generate_qr_code
from src.schemas.images import (
    ImageModel,
    ImageCreateForm,
    ImageDb,
    ImageDescriptionModel,
    CloudinaryTransformations,
)


from src.conf.config import settings


router = APIRouter(prefix="/images", tags=["images"])

allowed_operations_for_self = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operations_for_all = RoleAccess([Role.administrator])


@router.post(
    "",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def create_image(
    file: Annotated[UploadFile, File()],
    data: ImageCreateForm = Depends(),
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a POST-operation to "" images subroute and create an image.

    :param file: The uploaded file to create avatar from.
    :type file: UploadFile
    :param data: The data for the image to create.
    :type data: ImageCreateForm
    :param user: The user who creates the image.
    :type user: User
    :param session: Get the database session
    :type AsyncSession: The current session.
    :param cache: The Redis client.
    :type cache: Redis
    :return: Newly created image of the current user.
    :rtype: Image
    """
    try:
        if data.tags:
            if data.tags[0]:
                data.tags = list(set(data.tags[0].split(",")))
            else:
                data.tags = None
        data = ImageModel(**asdict(data))
    except Exception as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error_message),
        )
    image = await repository_images.create_image(file, data, user, session, cache)
    return image


@router.get(
    "/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_image(
    image_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a GET-operation to '/{image_id}' images subroute and gets the image with id.

    :param image_id: The image id.
    :type image_id: UUID | int
    :param session: Get the database session
    :type AsyncSession: The current session.
    :return: The image with id.
    :rtype: Image
    """
    image = await repository_images.read_image(image_id, session, cache)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not Found"
        )
    return image


@router.get(
    "/{image_id}/qr_code",
    response_class=FileResponse,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def get_qr_code(
    image_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a GET-operation to '/{image_id}/qr_code' images subroute and gets FileResponse.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param session: Get the database session
    :type AsyncSession: The current session.
    :return: Reply with a file in image/png format.
    :rtype: FileResponse
    """
    image = await repository_images.read_image(image_id, session, cache)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    image_url = image.url
    generate_qr_code(image_url)
    return FileResponse(
        "static/qrcode.png",
        media_type="image/png",
        filename="qrcode.png",
        status_code=200,
    )


@router.get(
    "",
    response_model=List[ImageDb],
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_images(
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ScalarResult:
    """
    Handles a GET-operation to "" images subroute and gets images of current user.

    :param user: The current user.
    :type user: User
    :return: List of images of the current user.
    :rtype: ScalarResult
    """
    images = await repository_images.read_images(user.id, session)
    return images


@router.get(
    "/{user_id}/images",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_user_images(
    user_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
) -> List:
    """
    Handles a GET-operation to images subroute '/{user_id}/images'.
        Gets of the user's images

    :param user_id: The Id of the current user.
    :type user_id: UUID | int
    :param session: Get the database session
    :type AsyncSession: The current session.
    :return: List of the user's images.
    :rtype: List
    """
    images = await repository_images.read_images(user_id, session)
    return images


@router.put(
    "/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def update_image(
    image_id: UUID4 | int,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
    transformations: List[CloudinaryTransformations] = Query(
        ...,
        description="List of Cloudinary image transformations",
        example=["crop", "resize"],
    ),
):
    """
    Handles a PUT operation for the images subroute '/{image_id}'.
        Updates the current user's image.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param user: The current user who updated image.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :param transformations: The Enum list of the image file transformation parameters.
    :type transformations: List
    :return: The updated image object.
    :rtype: Image
    """
    image = await repository_images.update_image(
        image_id,
        user.id,
        session,
        cache,
        transformations,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.put(
    "/{user_id}/images/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def update_user_image(
    image_id: UUID4 | int,
    user_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
    transformations: List[CloudinaryTransformations] = Query(
        ...,
        description="List of Cloudinary image transformations",
        example=["crop", "resize"],
    ),
):
    """
    Handles a PUT operation for the images subroute '/{user_id}/images/{image_id}'.
        Updates the user's image.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :param transformations: The Enum list of the image file transformation parameters.
    :type transformations: List
    :return: The updated image object.
    :rtype: Image
    """
    image = await repository_images.update_image(
        image_id,
        user_id,
        session,
        transformations,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.patch(
    "/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def patch_image(
    image_id: UUID4 | int,
    body: ImageDescriptionModel,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{image_id}'.
        Patches the current user's image.

    :param image_id: The Id of the image to patch.
    :type image_id: UUID4 | int
    :param body: The data for the image to patch.
    :type body: ImageDescriptionModel
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :param transformations: The Enum list of the image file transformation parameters.
    :type transformations: List
    :return: The updated image.
    :rtype: Image
    """
    image = await repository_images.patch_image(
        image_id,
        body,
        user.id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.patch(
    "/{user_id}/images/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def patch_user_image(
    image_id: UUID4 | int,
    body: ImageDescriptionModel,
    user_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{user_id}/images/{image_id}'.
        Patches the image of the user.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param body: The data for the image to update.
    :type body: ImageDescriptionModel
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The patched image.
    :rtype: Image
    """
    image = await repository_images.patch_image(
        image_id,
        body,
        user_id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def delete_image(
    image_id: UUID4 | int,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a DELETE operation for the images subroute '/{image_id}'.
        Deleted the current user's image.

    :param image_id: The Id of the image to delete.
    :type image_id: UUID4 | int
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: None
    :type: None
    """
    image = await repository_images.delete_image(image_id, user.id, session)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return None


@router.delete(
    "/{user_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def delete_user_image(
    image_id: UUID4 | int,
    user_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a DELETE operation for the images subroute '/{user_id}/images/{image_id}'.
        Delete the image of the user.

    :param image_id: The Id of the image to delete.
    :type image_id: UUID4 | int
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param session: The database session.
    :type session: AsyncSession
    :return: None
    :type: None
    """
    image = await repository_images.delete_image(image_id, user_id, session)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return None


@router.patch(
    "/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def add_tag_to_image(
    image_id: UUID4 | int,
    tag_title: str,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{image_id}/tags/{tag_title}'.
        Patches the tags of the current user's image.

    :param image_id: The Id of the image to patch.
    :type image_id: UUID4 | int
    :param tag_title: The tag title for the image.
    :type tag_title: str
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: Patched image object.
    :type: Image
    """
    image = await repository_images.add_tag_to_image(
        image_id,
        tag_title,
        user.id,
        user,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.patch(
    "/{user_id}/images/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def add_tag_to_user_image(
    image_id: UUID4 | int,
    tag_title: str,
    user_id: UUID4 | int,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{user_id}/images{image_id}/tags/{tag_title}'.
        Patches the current user's image tag.

    :param image_id: The Id of the image to patch the tag.
    :type image_id: UUID4 | int
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: An image object.
    :rtype: Image
    """
    image = await repository_images.add_tag_to_image(
        image_id,
        tag_title,
        user_id,
        user,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.delete(
    "/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def delete_tag_from_image(
    image_id: UUID4 | int,
    tag_title: str,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a DELETE operation for the images subroute '/{image_id}/tags/{tag_title}'.
        Delited the current user's image tag.

    :param image_id: The Id of the image to delete.
    :type image_id: UUID4 | int
    :param tag_title: The tag title for the image.
    :type tag_title: str
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: An image object.
    :rtype: Image
    """
    image = await repository_images.delete_tag_from_image(
        image_id,
        tag_title,
        user.id,
        user,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.delete(
    "/{user_id}/images/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def delete_tag_from_user_image(
    image_id: UUID4 | int,
    tag_title: str,
    user_id: UUID4 | int,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a DELETE operation for the images subroute '/{user_id}/images{image_id}/tags/{tag_title}'.
        Deleted the current user's image tag.

    :param image_id: The Id of the image to delete the tag.
    :type image_id: UUID4 | int
    :param tag_title: The tag title for the image.
    :type tag_title: str
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: An image object.
    :rtype: Image
    """
    image = await repository_images.delete_tag_from_image(
        image_id,
        tag_title,
        user_id,
        user,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image
