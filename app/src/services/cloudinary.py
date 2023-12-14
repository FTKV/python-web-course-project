"""
Module of Cloudinary class and methods
"""


import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, File, status

from src.conf.config import settings

# from src.database.models import User


class CloudinaryService:
    api_name = settings.api_name.replace(" ", "_")
    public_id = f"{api_name}/"

    def __init__(self):
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    def gen_image_name(self, username, filename, album=None):
        """
        Generate image name.

        :param name: Image name.
        :param type: str
        :return: Full path to the image storage location in the cloud storage.
        :rtype: str
        """
        public_id = (
            CloudinaryService.public_id + f"/{username}/{album}/{filename}"
            if album
            else CloudinaryService.public_id + f"/{username}/{filename}"
        )
        return public_id

    async def upload_image(self, file, username, filename, album=None):
        """
        Uploads an user's image.

        :param file: The uploaded file of avatar.
        :type file: BinaryIO
        :param filename: The filename of the image to upload.
        :type filename: str
        :return: The file upload result
        :rtype: json
        """
        public_id = self.gen_image_name(username, filename, album)
        try:
            result = cloudinary.uploader.upload(
                file,
                public_id=public_id,
                overwrite=True,
            )
            print(result)
            return result
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None

    async def get_image_url(self, result):
        """
        Get image url from cloudinary json response.

        :param result: json response.
        :type result: json
        :return: Url of uploaded image.
        :rtype: str
        """
        try:
            image_url = result.get("secure_url")
            return image_url
        except Exception as e:
            print(f"Error getting image URL: {e}")
            return None

    async def delete_image(
        self,
        image_url,
    ):
        """
        Delete an image.

        :param image_url: The image to delete
        :type image_url: URL image
        :return: Result
        :rtype: str
        """
        try:
            result = cloudinary.uploader.destroy(image_url)
            print(f"Image deleted: {result}")
        except Exception as e:
            print(f"Error deleting image: {e}")

    async def upload_avatar(
        self,
        file,
        username,
        filename,
    ):
        """
        Uploads an user's avatar.

        :param file: The uploaded file of avatar.
        :type file: UploadFile
        :param username: The username of the user to upload avatar.
        :type username: User
        :type filename: The name of image file
        :return: The URL of uploaded avatar.
        :rtype: str
        """
        public_id = self.gen_image_name(username, filename, album="avatars")
        r = await self.upload_image(file, username, filename, album="avatars")
        avatar_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return avatar_url

    async def edit_image_face(self, file, public_id):
        result = cloudinary.CloudinaryImage(public_id).image(
            transformation=[
                {"gravity": "face", "height": 200, "width": 200, "crop": "thumb"},
                {"radius": "max"},
                {"fetch_format": "auto"},
            ]
        )
        # Result: srt = <img src="https://res.cloudinary.com/dszct2q9m/image/upload/c_thumb,g_face,h_200,w_200/r_max/f_auto/cogaj"/>


cloudinary_service = CloudinaryService()


# async def upload_avatar(
#     file: UploadFile,
#     username: str,
# ):
#     """
#     Uploads an user's avatar.

#     :param file: The uploaded file of avatar.
#     :type file: UploadFile
#     :param username: The username of the user to upload avatar.
#     :type username: User
#     :return: The URL of uploaded avatar.
#     :rtype: str
#     """
#     cloudinary.config(
#         cloud_name=settings.cloudinary_cloud_name,
#         api_key=settings.cloudinary_api_key,
#         api_secret=settings.cloudinary_api_secret,
#         secure=True,
#     )
#     api_name = settings.api_name.replace(" ", "_")
#     try:
#         r = cloudinary.uploader.upload(
#             file.file,
#             public_id=f"{api_name}/{username}",
#             overwrite=True,
#         )
#         src_url = cloudinary.CloudinaryImage(f"{api_name}/{username}").build_url(
#             width=250, height=250, crop="fill", version=r.get("version")
#         )
#     except Exception as error_message:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Upload image error: {str(error_message)}",
#         )
#     return src_url
