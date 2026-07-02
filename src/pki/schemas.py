from pydantic import BaseModel, Field


class CertificateGenerateModel(BaseModel):
    p12_password: str = Field(min_length=6)
