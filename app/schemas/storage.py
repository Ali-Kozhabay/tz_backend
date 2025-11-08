from pydantic import BaseModel, Field


class SignUrlQuery(BaseModel):
    key: str = Field(min_length=1)


class SignedUrlResponse(BaseModel):
    url: str
