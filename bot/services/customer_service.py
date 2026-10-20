"""Mijoz bilan bog'liq database operatsiyalari."""
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, Order

logger = logging.getLogger(__name__)


class CustomerService:
    """Mijoz uchun service."""

    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        telegram_id: int,
        full_name: Optional[str] = None,
    ) -> User:
        """Foydalanuvchini topish yoki yaratish."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                role="customer",
            )
            session.add(user)
            await session.flush()
            logger.info(f"Yangi foydalanuvchi yaratildi: {telegram_id}")

        return user

    @staticmethod
    async def update_phone(
        session: AsyncSession,
        telegram_id: int,
        phone: str,
    ) -> Optional[User]:
        """Telefon raqamni saqlash."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.phone = phone
            await session.flush()
            logger.info(f"Telefon saqlandi: {telegram_id} -> {phone}")

        return user

    @staticmethod
    async def update_name(
        session: AsyncSession,
        telegram_id: int,
        full_name: str,
    ) -> Optional[User]:
        """Ismni yangilash."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.full_name = full_name
            await session.flush()

        return user

    @staticmethod
    async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Foydalanuvchini topish."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Foydalanuvchini ID bo'yicha topish."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_stats(session: AsyncSession, user_id: int) -> dict:
        """Foydalanuvchi statistikasi."""
        total = await session.execute(
            select(func.count(Order.id)).where(Order.customer_id == user_id)
        )
        completed = await session.execute(
            select(func.count(Order.id)).where(
                Order.customer_id == user_id,
                Order.status == "COMPLETED",
            )
        )
        cancelled = await session.execute(
            select(func.count(Order.id)).where(
                Order.customer_id == user_id,
                Order.status == "CANCELLED",
            )
        )

        return {
            "total": total.scalar() or 0,
            "completed": completed.scalar() or 0,
            "cancelled": cancelled.scalar() or 0,
        }

    @staticmethod
    async def get_user_orders(
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list:
        """Foydalanuvchi buyurtmalarini olish."""
        stmt = (
            select(Order)
            .where(Order.customer_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_users_count(session: AsyncSession) -> int:
        """Barcha foydalanuvchilar soni."""
        result = await session.execute(select(func.count(User.id)))
        return result.scalar() or 0

    @staticmethod
    async def get_all_user_ids(session: AsyncSession) -> list:
        """Barcha foydalanuvchilar telegram_id larini olish."""
        result = await session.execute(select(User.telegram_id))
        return [row[0] for row in result.all()]
