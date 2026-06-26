from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expire, "type": "access"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": subject, "exp": expire, "type": "refresh"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, token_type: str = "access") -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None


def generate_secure_token() -> str:
    return secrets.token_urlsafe(32)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.user_repo import UserRepository
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    if not credentials:
        raise exc
    user_id = decode_token(credentials.credentials, "access")
    if not user_id:
        raise exc
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise exc
    return user
