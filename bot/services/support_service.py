import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from bot.database.models import SupportMessage

logger = logging.getLogger(__name__)

class SupportService:
    """Yordam so'rovlari bilan ishlash."""

    @staticmethod
    async def create_support_message(
        session: AsyncSession,
        user_id: int,
        message_type: str,
        text_content: Optional[str] = None,
        file_id: Optional[str] = None
    ) -> SupportMessage:
        """Yangi xabar yaratish."""
        msg = SupportMessage(
            user_id=user_id,
            message_type=message_type,
            text_content=text_content,
            file_id=file_id,
            status="NEW"
        )
        session.add(msg)
        await session.commit()
        return msg

    @staticmethod
    async def get_new_messages_count(session: AsyncSession) -> int:
        """Yangi xabarlar sonini olish."""
        result = await session.execute(select(func.count(SupportMessage.id)).where(SupportMessage.status == "NEW"))
        return result.scalar() or 0

    @staticmethod
    async def get_oldest_new_message(session: AsyncSession) -> Optional[SupportMessage]:
        """Eng eski o'qilmagan xabarni olish."""
        result = await session.execute(
            select(SupportMessage).where(SupportMessage.status == "NEW").order_by(SupportMessage.created_at.asc())
        )
        return result.scalars().first()

    @staticmethod
    async def mark_as_read(session: AsyncSession, msg_id: int) -> bool:
        """Xabarni o'qilgan qilib belgilash."""
        result = await session.execute(select(SupportMessage).where(SupportMessage.id == msg_id))
        msg = result.scalar_one_or_none()
        if msg:
            msg.status = "READ"
            await session.commit()
            return True
        return False
