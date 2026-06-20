import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

#####
# import other schemas as necessary here
#####


######
######
"""
2FA/TOTP schemas here
"""

class Enable2FAModel(BaseModel):
    password: str  # Verify password before enabling 2FA

class Verify2FAModel(BaseModel):
    code: str = Field(min_length=6, max_length=6)

class Verify2FASetupModel(BaseModel):
    code: str = Field(min_length=6, max_length=6)

class LoginResponseModel(BaseModel):
    requires_2fa: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[dict] = None

    
######
######



class UserCreateModel(BaseModel):
    # pydantic Field is used to enforce constraints 
    first_name: str = Field(max_length = 25)
    last_name: str = Field(max_length = 25)
    username: str = Field(max_length = 8)
    email: str = Field(max_length = 40)
    password: str = Field(min_length=6)

# IMPORTANT!
# The auth.schemas UserModel and auth.models User attributes
# have to match. True for every schema and model "equivalent" 
# even if respective models from every folder are 
# potenitially moved to db folder
class UserModel(BaseModel):
    # the IMMUTABLE ANCHOR maintaining the session state
    uid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    # removed password hash from response
    # password_hash: str = Field(exclude=True)
    created_at: datetime
    updated_at: datetime    

class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str  = Field(min_length=6)    