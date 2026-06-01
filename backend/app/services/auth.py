from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserCreate


async def register_user(session: AsyncSession, data: UserCreate) -> User:
    existing = await session.exec(select(User).where(User.email == data.email))
    if existing.first():
        raise ValueError("Email already registered")
    user = User(
        email=data.email,
        display_name=data.display_name,
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def login_user(session: AsyncSession, email: str, password: str) -> str:
    result = await session.exec(select(User).where(User.email == email))
    user = result.first()
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password")
    return create_access_token(str(user.id))


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    import uuid
    return await session.get(User, uuid.UUID(user_id))
