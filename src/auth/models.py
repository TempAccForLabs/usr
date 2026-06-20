from datetime import datetime
from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
import uuid

class User(SQLModel, table = True):
    __tablename__="user_accounts"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid.uuid4,
            info={"description": "Unique identifier for the user account"}
        )
    )

    username: str
    first_name: str = Field(nullable=True)
    last_name: str = Field(nullable=True)
    # original implementation with e-mail only 
    # valid email address
    is_verified: bool = False
    email: str
    password_hash: str


    ######
    ######
    # 2FA Fields
    is_2fa_enabled: bool = Field(default=False)
    totp_secret: str = Field(nullable=True)  # Encrypted TOTP secret
    ######
    ######


    created_at: datetime = Field(sa_column = Column(
        pg.TIMESTAMP, 
        default = datetime.now
    ))
    # add update
    updated_at: datetime = Field(sa_column = Column(
        pg.TIMESTAMP, 
        default = datetime.now,
        onupdate=datetime.now
    ))


    def __repr__(self) -> str:
        return f"<User {self.username}>"    