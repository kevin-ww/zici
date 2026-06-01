import uuid
from typing import Optional

from sqlmodel import SQLModel


class UserCreate(SQLModel):
    email: str
    password: str
    display_name: Optional[str] = None


class UserRead(SQLModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str] = None


class LoginRequest(SQLModel):
    email: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
