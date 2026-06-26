from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.models import User, Organization


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: str) -> Optional[User]:
        r = await self.db.execute(select(User).where(User.id == id))
        return r.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        r = await self.db.execute(select(User).where(User.email == email))
        return r.scalar_one_or_none()

    async def get_by_google_id(self, gid: str) -> Optional[User]:
        r = await self.db.execute(select(User).where(User.google_id == gid))
        return r.scalar_one_or_none()

    async def get_by_verification_token(self, token: str) -> Optional[User]:
        r = await self.db.execute(select(User).where(User.verification_token == token))
        return r.scalar_one_or_none()

    async def get_by_reset_token(self, token: str) -> Optional[User]:
        r = await self.db.execute(select(User).where(User.reset_token == token))
        return r.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user


class OrgRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: str) -> Optional[Organization]:
        r = await self.db.execute(select(Organization).where(Organization.id == id))
        return r.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        r = await self.db.execute(select(Organization).where(Organization.slug == slug))
        return r.scalar_one_or_none()

    async def get_by_owner(self, owner_id: str) -> Optional[Organization]:
        r = await self.db.execute(select(Organization).where(Organization.owner_id == owner_id))
        return r.scalar_one_or_none()
