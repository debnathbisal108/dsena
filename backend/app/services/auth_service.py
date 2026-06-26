from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, generate_secure_token
from app.core.exceptions import ConflictError, BadRequestError, UnauthorizedError
from app.models import User
from app.repositories.user_repo import UserRepository
from app.schemas import RegisterRequest, LoginRequest
from app.services import email_service


async def register_user(db: AsyncSession, data: RegisterRequest):
    repo = UserRepository(db)
    if await repo.get_by_email(data.email):
        raise ConflictError("Email already registered")
    token = generate_secure_token()
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        verification_token=token,
        is_verified=False,
    )
    await repo.create(user)
    try:
        await email_service.send_verification_email(user.email, user.full_name, token)
    except Exception:
        pass  # Don't block registration if email fails
    return user, create_access_token(user.id), create_refresh_token(user.id)


async def login_user(db: AsyncSession, data: LoginRequest):
    repo = UserRepository(db)
    user = await repo.get_by_email(data.email)
    if not user or not user.hashed_password:
        raise UnauthorizedError("Invalid email or password")
    if not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")
    return user, create_access_token(user.id), create_refresh_token(user.id)


async def verify_email(db: AsyncSession, token: str):
    repo = UserRepository(db)
    user = await repo.get_by_verification_token(token)
    if not user:
        raise BadRequestError("Invalid or expired verification token")
    user.is_verified = True
    user.verification_token = None
    await db.flush()
    return user


async def forgot_password(db: AsyncSession, email: str):
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user:
        return
    token = generate_secure_token()
    user.reset_token = token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.flush()
    try:
        await email_service.send_password_reset_email(user.email, user.full_name, token)
    except Exception:
        pass


async def reset_password(db: AsyncSession, token: str, new_password: str):
    repo = UserRepository(db)
    user = await repo.get_by_reset_token(token)
    if not user:
        raise BadRequestError("Invalid or expired reset token")
    if user.reset_token_expires_at and user.reset_token_expires_at < datetime.now(timezone.utc):
        raise BadRequestError("Reset token has expired")
    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    await db.flush()


async def google_oauth_login(db: AsyncSession, google_id: str, email: str, full_name: str, avatar_url: str = ""):
    repo = UserRepository(db)
    user = await repo.get_by_google_id(google_id) or await repo.get_by_email(email)
    if user:
        user.google_id = google_id
        if avatar_url:
            user.avatar_url = avatar_url
        user.is_verified = True
        await db.flush()
    else:
        user = User(email=email, full_name=full_name, google_id=google_id, avatar_url=avatar_url, is_verified=True)
        await repo.create(user)
    return user, create_access_token(user.id), create_refresh_token(user.id)
