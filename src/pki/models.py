from datetime import datetime
from typing import Optional
import uuid

from sqlmodel import SQLModel, Field, Column, Index
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey


class ClientCertificate(SQLModel, table=True):
    __tablename__ = "client_certificates"

    # Integer auto-increment primary key
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            pg.INTEGER,
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
    )

    # Foreign key to user_accounts.uid (UUID — matches the actual User PK type)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            ForeignKey("user_accounts.uid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    # Unique certificate serial number (hex string, e.g. "1a2b3c4d...")
    serial_number: str = Field(
        sa_column=Column(
            pg.TEXT,
            unique=True,
            index=True,
            nullable=False,
        )
    )

    # Certificate validity window
    valid_from: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, nullable=False)
    )

    valid_until: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, nullable=False)
    )

    # Revocation flag — False means the certificate is active (whitelist entry)
    is_revoked: bool = Field(
        sa_column=Column(
            pg.BOOLEAN,
            nullable=False,
            default=False,
            server_default="false",
        )
    )

    # PEM-encoded public certificate text (can be several KB)
    certificate_pem: str = Field(
        sa_column=Column(pg.TEXT, nullable=False)
    )

    # Audit timestamps
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.utcnow, nullable=False)
    )

    def __repr__(self) -> str:
        status = "REVOKED" if self.is_revoked else "active"
        return f"<ClientCertificate serial={self.serial_number} status={status}>"
