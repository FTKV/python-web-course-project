"""
Module of role access class
"""


from typing import List

from fastapi import Depends, HTTPException, status, Request

from src.database.models import User, Role
from src.services.auth import auth_service


class RoleAccess:
    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, request: Request, user: User = Depends(auth_service.get_current_user)
    ):
        # print(request.method)
        # print(request.url)
        # if request.method in ["POST", "PUT", "PATCH"]:
        #     print(await request.json())
        # print("User", user.role)
        # print("Roles", self.allowed_roles)
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation forbidden"
            )