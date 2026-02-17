from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async for session in get_session():
        try:
            yield session
        finally:
            await session.close()


async def get_current_admin(db: AsyncSession = Depends(get_db)) -> dict:
    """Get current admin user (simplified for demo)"""
    # In production, implement proper JWT authentication
    # For now, return a mock admin
    return {
        "id": 123456789,
        "username": "admin",
        "role": "admin"
    }
