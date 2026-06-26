from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.core.database import get_db
from app.core.security import decode_token, get_current_user, create_access_token, create_refresh_token
from app.core.exceptions import UnauthorizedError
from app.core.config import settings
from app.middleware.rate_limit import limiter
from app.schemas import RegisterRequest, LoginRequest, RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest, AuthResponse, UserOut, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.post("/register", response_model=AuthResponse, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, access, refresh = await auth_service.register_user(db, data)
    return AuthResponse(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
@limiter.limit("20/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, access, refresh = await auth_service.login_user(db, data)
    return AuthResponse(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest):
    user_id = decode_token(data.refresh_token, "refresh")
    if not user_id:
        raise UnauthorizedError("Invalid refresh token")
    return TokenResponse(access_token=create_access_token(user_id), refresh_token=create_refresh_token(user_id))


@router.get("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_email(db, token)
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.forgot_password(db, data.email)
    return {"message": "If that email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(db, data.token, data.password)
    return {"message": "Password reset successfully"}


@router.get("/google")
async def google_login():
    params = (f"?client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.google_redirect_uri}"
              f"&response_type=code&scope=openid%20email%20profile&access_type=offline&prompt=consent")
    return {"url": GOOGLE_AUTH_URL + params}


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        tokens = (await client.post(GOOGLE_TOKEN_URL, data={
            "code": code, "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.google_redirect_uri, "grant_type": "authorization_code",
        })).json()
        info = (await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"})).json()
    user, access, refresh = await auth_service.google_oauth_login(db, info["sub"], info["email"], info.get("name", ""), info.get("picture", ""))
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback?access_token={access}&refresh_token={refresh}")


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut.model_validate(current_user)
