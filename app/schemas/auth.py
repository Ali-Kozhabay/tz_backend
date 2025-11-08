from pydantic import BaseModel, EmailStr


class TokenPair(BaseModel):
    access: str
    refresh: str


class TokenRefreshRequest(BaseModel):
    refresh: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
