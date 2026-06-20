from typing import Any, List

from fastapi import APIRouter, status, Depends, Request
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException

from src.db.main import get_session
from .models import User


from .service import UserService
from .utils import decode_token

# auth.service.py
user_service = UserService()


"""
Child instance of HTTPBearer to insure access of endpoints
only where jwt checks are validated

HTTPBearer dependency that has to be injected to endpoints that must allow
access via HTTPBearer tokens
The child instance of HTTPearer can be used as a dependency
via Depends()
"""

# changed to parent class called TokenBearer
# with 2 children classes, AccessTokenBearer and RefreshTokenBearer
# both currently implementing jwt authentication
class TokenBearer(HTTPBearer):

    def __init__(self, auto_error=True):
        # raise error if token is not provided
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)
        token = creds.credentials
        # auth.utils decode_token 
        token_data = decode_token(token)

        """
        jwt
        """
        if not self.token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail={
                    "error":"This token is invalid or expired",
                    "resolution":"Please get new token"
                }
            )

        ###
        # polymorphic call
        ###
        self.verify_token_data(token_data)

        # only requests with valid token data are processed further
        return token_data
    
    """
    check against provided jwt token 
    """
    def token_valid(self, token: str) -> bool:
        # auth.utils decode_token method
        token_data = decode_token(token)
        # valid if not None
        return token_data is not None 
    
    """
    implement in children classes
    """
    def verify_token_data(self, token_data):
        raise NotImplementedError("Implement in children classes")
    

class AccessTokenBearer(TokenBearer):
    def verify_token_data(
            self, 
            token_data: dict
    ) -> None:
        # raise an exception if refresh token instead of access token
        if token_data and token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide an access token",
            )


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(
            self, 
            token_data: dict
    ) -> None:
        # raise an exception if access token instead of refresh token
        if token_data and not token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide a refresh token",
            )


